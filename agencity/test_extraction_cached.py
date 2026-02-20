#!/usr/bin/env python3
"""
Test LinkedIn connection extraction using cached cookies.

Uses per-account cookie cache files (created by scripts/save_test_auth.py)
to avoid login and 2FA. Each account gets its own isolated browser profile.

If cookies are stale and LinkedIn shows "Welcome Back",
uses the adaptive login flow to re-authenticate.

Usage:
    python test_extraction_cached.py [--cautious] [--email EMAIL]

Options:
    --cautious    Use cautious mode (2x slower, more idle pauses) for new accounts
    --email       LinkedIn account email (uses LINKEDIN_TEST_EMAIL env var if not provided)
    --clear       Clear the browser profile before running (fresh start)
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.linkedin.stealth_browser import StealthBrowser
from app.services.linkedin.human_behavior import GhostCursor, ExtractionMode
from app.services.linkedin.credential_auth import LinkedInCredentialAuth, LoginState
from app.services.linkedin.account_manager import AccountManager

# Legacy cache path for backwards compatibility
LEGACY_CACHE_PATH = Path(__file__).parent / ".linkedin_test_cache.json"


def get_cache_path(email: str) -> Path:
    """Get the cache file path for a specific account."""
    profile_id = AccountManager.get_profile_id(email)
    return Path(__file__).parent / f".linkedin_cache_{profile_id}.json"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test LinkedIn connection extraction with cached cookies"
    )
    parser.add_argument(
        "--cautious",
        action="store_true",
        help="Use cautious mode (2x slower, more idle pauses) for new accounts"
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="LinkedIn account email (uses LINKEDIN_TEST_EMAIL env var if not provided)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the browser profile before running (fresh start)"
    )
    return parser.parse_args()


def load_cookies(email: str) -> list:
    """Load cookies from cache and convert to Playwright format."""
    # Try account-specific cache first
    cache_path = get_cache_path(email)

    if not cache_path.exists():
        # Fall back to legacy cache
        if LEGACY_CACHE_PATH.exists():
            print(f"⚠️  Using legacy cache (consider re-running scripts/save_test_auth.py)")
            cache_path = LEGACY_CACHE_PATH
        else:
            print(f"❌ Cookie cache not found for {email}")
            print(f"   Expected: {cache_path}")
            print("   Run: python scripts/save_test_auth.py")
            sys.exit(1)

    with open(cache_path) as f:
        cookies_dict = json.load(f)

    cookie_list = []
    for name, data in cookies_dict.items():
        cookie = {
            "name": name,
            "value": data["value"],
            "domain": data.get("domain", ".linkedin.com"),
            "path": data.get("path", "/"),
            "secure": data.get("secure", True),
            "httpOnly": data.get("httpOnly", False),
        }
        if data.get("expirationDate"):
            cookie["expires"] = data["expirationDate"]
        cookie_list.append(cookie)

    return cookie_list


async def test_extraction(cautious_mode: bool = False, email: str = None, clear_profile: bool = False):
    # Get email from argument or environment
    if not email:
        email = os.environ.get('LINKEDIN_TEST_EMAIL', '').strip()

    if not email:
        print("❌ Email required. Use --email or set LINKEDIN_TEST_EMAIL env var")
        sys.exit(1)

    # Get account-specific profile ID
    profile_id = AccountManager.get_profile_id(email)
    account_mgr = AccountManager()

    print("=" * 70)
    print("TEST: LinkedIn Connection Extraction (Using Cached Cookies)")
    print("=" * 70)
    print(f"Account: {email}")
    print(f"Profile: {profile_id}")
    if cautious_mode:
        print("Mode: CAUTIOUS (2x slower, more idle pauses)")
    else:
        print("Mode: NORMAL")

    # Clear profile if requested
    if clear_profile:
        print(f"\n🗑️  Clearing browser profile for fresh start...")
        account_mgr.clear_profile(email)

    cookies = load_cookies(email)
    print(f"✅ Loaded {len(cookies)} cookies from cache")

    # Use account-specific profile (isolated from other accounts)
    async with StealthBrowser.launch_persistent(
        session_id=profile_id,
        headless=False
    ) as sb:
        # The profile already has cookies from the original auth,
        # but we also inject from cache in case profile was cleared
        await sb.context.add_cookies(cookies)
        page = await sb.new_page()

        # Navigate through the natural chain
        print("\n1. Navigating to feed...")
        await page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
        await asyncio.sleep(3)

        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "/login" in current_url or "/checkpoint" in current_url:
            print("⚠️ Cookies stale - attempting adaptive re-auth...")

            # Use the credential auth state machine to handle this
            auth = LinkedInCredentialAuth()
            email = os.getenv("LINKEDIN_TEST_EMAIL")
            password = os.getenv("LINKEDIN_TEST_PASSWORD")

            if not email or not password:
                print("❌ LINKEDIN_TEST_EMAIL/PASSWORD not set in .env")
                await page.screenshot(path="login_redirect_debug.png")
                return

            # Detect and handle login state
            max_iterations = 10
            for iteration in range(max_iterations):
                state = await auth._detect_login_state(page, email)
                print(f"   Login state: {state}")

                if state == LoginState.LOGGED_IN:
                    break
                elif state == LoginState.WELCOME_BACK:
                    clicked = await auth._handle_welcome_back(page, email)
                    if not clicked:
                        await auth._click_sign_in_another_account(page)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.LOGIN_FORM:
                    await auth._fill_login_form(page, email, password)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.PASSWORD_ONLY:
                    await auth._fill_password_only(page, password)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.TWO_FA:
                    print("❌ 2FA required - run scripts/save_test_auth.py manually")
                    await page.screenshot(path="2fa_required_debug.png")
                    return
                elif state == LoginState.ERROR:
                    print("❌ Login error detected")
                    await page.screenshot(path="login_error_debug.png")
                    return
                else:
                    await asyncio.sleep(2)

            # Update cookie cache with fresh cookies
            fresh_cookies = await sb.context.cookies()
            fresh_cache = auth._extract_linkedin_cookies(fresh_cookies)
            with open(CACHE_PATH, "w") as f:
                json.dump(fresh_cache, f, indent=2)
            print(f"   ✅ Updated cookie cache with {len(fresh_cache)} cookies")

        print(f"   ✅ Feed loaded: {page.url}")

        # Navigate to connections
        print("\n2. Navigating to connections...")
        await page.goto(
            "https://www.linkedin.com/mynetwork/invite-connect/connections/",
            wait_until="load",
            timeout=30000
        )
        await asyncio.sleep(5)

        if "/login" in page.url or "/checkpoint" in page.url:
            print("⚠️ Redirected to login - attempting adaptive re-auth...")

            # Use the credential auth state machine to handle this
            auth = LinkedInCredentialAuth()
            email = os.getenv("LINKEDIN_TEST_EMAIL")
            password = os.getenv("LINKEDIN_TEST_PASSWORD")

            if not email or not password:
                print("❌ LINKEDIN_TEST_EMAIL/PASSWORD not set in .env")
                await page.screenshot(path="login_redirect_debug.png")
                return

            # Detect and handle login state
            max_iterations = 10
            for iteration in range(max_iterations):
                state = await auth._detect_login_state(page, email)
                print(f"   Login state: {state}")

                if state == LoginState.LOGGED_IN:
                    break
                elif state == LoginState.WELCOME_BACK:
                    clicked = await auth._handle_welcome_back(page, email)
                    if not clicked:
                        await auth._click_sign_in_another_account(page)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.LOGIN_FORM:
                    await auth._fill_login_form(page, email, password)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.PASSWORD_ONLY:
                    await auth._fill_password_only(page, password)
                    await page.wait_for_load_state("load", timeout=15000)
                    await asyncio.sleep(2)
                elif state == LoginState.TWO_FA:
                    print("❌ 2FA required - run scripts/save_test_auth.py manually")
                    await page.screenshot(path="2fa_required_debug.png")
                    return
                elif state == LoginState.ERROR:
                    print("❌ Login error detected")
                    await page.screenshot(path="login_error_debug.png")
                    return
                else:
                    await asyncio.sleep(2)

            # Re-navigate to connections after auth
            print("\n   Re-navigating to connections...")
            await page.goto(
                "https://www.linkedin.com/mynetwork/invite-connect/connections/",
                wait_until="load",
                timeout=30000
            )
            await asyncio.sleep(5)

            if "/login" in page.url or "/checkpoint" in page.url:
                print("❌ Still redirected after re-auth - session truly invalid")
                await page.screenshot(path="reauth_failed_debug.png")
                return

            # Update cookie cache with fresh cookies
            fresh_cookies = await sb.context.cookies()
            fresh_cache = auth._extract_linkedin_cookies(fresh_cookies)
            with open(CACHE_PATH, "w") as f:
                json.dump(fresh_cache, f, indent=2)
            print(f"   ✅ Updated cookie cache with {len(fresh_cache)} cookies")

        print(f"   ✅ Connections loaded: {page.url}")

        # Run extraction
        print("\n3. Extracting connections...")
        result = await page.evaluate(r'''() => {
            const connections = [];
            const seenUrls = new Set();

            const listContainer = document.querySelector('[data-view-name="connections-list"]');
            const searchRoot = listContainer || document;

            const cards = searchRoot.querySelectorAll('[componentkey^="auto-component-"]');
            console.log('Cards found:', cards.length);

            cards.forEach(card => {
                const profileLinks = card.querySelectorAll('a[href*="/in/"]');
                if (profileLinks.length === 0) return;

                const profileLink = profileLinks[0];
                const url = profileLink.href?.split('?')[0];
                if (!url || seenUrls.has(url)) return;
                seenUrls.add(url);

                let name = null;
                for (const link of profileLinks) {
                    const innerA = link.querySelector('a');
                    if (innerA && innerA.textContent?.trim()) {
                        name = innerA.textContent.trim();
                        break;
                    }
                    const pWithA = link.querySelector('p a');
                    if (pWithA && pWithA.textContent?.trim()) {
                        name = pWithA.textContent.trim();
                        break;
                    }
                    const linkText = link.textContent?.trim();
                    if (linkText && linkText.length > 2 && linkText.length < 60 && !linkText.includes('@')) {
                        if (!linkText.includes(' | ') && !linkText.includes(' at ')) {
                            name = linkText;
                            break;
                        }
                    }
                }

                let headline = null;
                let connectedDate = null;
                const paragraphs = card.querySelectorAll('p');
                for (const p of paragraphs) {
                    const text = p.textContent?.trim();
                    if (!text || text.length < 5) continue;
                    if (text === name) continue;
                    if (text.startsWith('Connected on') || text.startsWith('Connected ')) {
                        connectedDate = text;
                        continue;
                    }
                    if (/^(Message|Connect|Follow|Pending|Send|InMail)$/i.test(text)) continue;
                    if (!headline && text.length >= 10 && text.length <= 200) {
                        headline = text;
                    }
                }

                if (!name) {
                    const figure = card.querySelector('figure[aria-label]');
                    if (figure) {
                        const ariaLabel = figure.getAttribute('aria-label');
                        if (ariaLabel && ariaLabel.includes("'s profile picture")) {
                            name = ariaLabel.replace("'s profile picture", "").trim();
                        }
                    }
                }

                if (!name || name.length < 2) return;

                const img = card.querySelector('img[src*="licdn"], img[src*="profile"]');

                connections.push({
                    name,
                    headline,
                    url,
                    imgUrl: img?.src || null,
                    connectedDate
                });
            });

            return {
                listFound: !!listContainer,
                cardsFound: cards.length,
                connections
            };
        }''')

        print("\n" + "=" * 70)
        print("EXTRACTION RESULTS")
        print("=" * 70)

        print(f"\nList container found: {result.get('listFound')}")
        print(f"Cards found: {result.get('cardsFound')}")
        print(f"Connections extracted: {len(result.get('connections', []))}")

        for conn in result.get("connections", []):
            print(f"\n  Name: {conn.get('name', 'Unknown')}")
            print(f"  Headline: {conn.get('headline', 'N/A')}")
            print(f"  URL: {conn.get('url', 'N/A')}")
            print(f"  Connected: {conn.get('connectedDate', 'N/A')}")

        # Take screenshot
        await page.screenshot(path="extraction_test_result.png", full_page=True)
        print(f"\n📸 Screenshot saved: extraction_test_result.png")

        if result.get("connections"):
            print("\n✅ Extraction successful!")
        else:
            print("\n⚠️ No connections found - check if account has connections")

        # Keep browser open briefly to verify
        await asyncio.sleep(3)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(test_extraction(
        cautious_mode=args.cautious,
        email=args.email,
        clear_profile=args.clear
    ))
