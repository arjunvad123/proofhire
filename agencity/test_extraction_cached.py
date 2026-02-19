#!/usr/bin/env python3
"""
Test LinkedIn connection extraction using cached cookies.

Uses the cookie cache from .linkedin_test_cache.json (created by
scripts/save_test_auth.py) to avoid login and 2FA.

Usage:
    python test_extraction_cached.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.stealth_browser import StealthBrowser
from app.services.linkedin.human_behavior import GhostCursor

CACHE_PATH = Path(__file__).parent / ".linkedin_test_cache.json"


def load_cookies() -> list:
    """Load cookies from cache and convert to Playwright format."""
    if not CACHE_PATH.exists():
        print(f"❌ Cookie cache not found: {CACHE_PATH}")
        print("   Run: python scripts/save_test_auth.py")
        sys.exit(1)

    with open(CACHE_PATH) as f:
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


async def test_extraction():
    print("=" * 70)
    print("TEST: LinkedIn Connection Extraction (Using Cached Cookies)")
    print("=" * 70)

    cookies = load_cookies()
    print(f"✅ Loaded {len(cookies)} cookies from cache")

    # Use the SAME profile that save_test_auth.py used
    # This ensures LinkedIn recognizes it as the same "device"
    async with StealthBrowser.launch_persistent(
        session_id="auth_test_account",
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
            print("❌ Redirected to login/checkpoint - cookies may be invalid")
            print("   Run: python scripts/save_test_auth.py")
            # Take screenshot to see what's happening
            await page.screenshot(path="login_redirect_debug.png")
            print("   Screenshot saved: login_redirect_debug.png")
            return

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
            print("❌ Redirected to login/checkpoint - session invalid")
            return

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
    asyncio.run(test_extraction())
