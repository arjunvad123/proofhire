#!/usr/bin/env python3
"""
Manual login script - handles security checkpoints interactively.

Opens a browser where you can complete LinkedIn's security verification
manually (CAPTCHA, email verification, etc.), then saves the cookies.

Usage:
    python scripts/manual_login.py [--email EMAIL]

The script will:
1. Open a browser with an isolated profile for your account
2. Navigate to LinkedIn login
3. Wait for you to complete login manually
4. Save cookies when you're logged in
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.linkedin.stealth_browser import StealthBrowser
from app.services.linkedin.account_manager import AccountManager


def get_cache_path(email: str) -> Path:
    """Get the cache file path for a specific account."""
    profile_id = AccountManager.get_profile_id(email)
    return Path(f".linkedin_cache_{profile_id}.json")


async def manual_login(email: str = None):
    """Open browser for manual login and save cookies."""

    if not email:
        email = os.environ.get('LINKEDIN_TEST_EMAIL', '').strip()

    if not email:
        email = input("LinkedIn account email: ").strip()

    if not email:
        print("❌ Email required")
        sys.exit(1)

    profile_id = AccountManager.get_profile_id(email)
    cache_path = get_cache_path(email)

    print()
    print("=" * 70)
    print("MANUAL LOGIN - Complete Security Verification")
    print("=" * 70)
    print(f"  Account    : {email}")
    print(f"  Profile ID : {profile_id}")
    print(f"  Cache file : {cache_path}")
    print()
    print("📋 Instructions:")
    print("   1. A browser will open to LinkedIn")
    print("   2. Complete the login manually (enter credentials, solve CAPTCHA, etc.)")
    print("   3. Once you see your LinkedIn feed, press ENTER here")
    print("   4. Cookies will be saved automatically")
    print()
    input("Press ENTER to open browser...")

    async with StealthBrowser.launch_persistent(
        session_id=profile_id,
        headless=False
    ) as sb:
        page = await sb.new_page()

        # Navigate to LinkedIn login
        print("\n🌐 Opening LinkedIn login page...")
        await page.goto("https://www.linkedin.com/login", wait_until="load", timeout=30000)

        print()
        print("=" * 70)
        print("⏳ WAITING FOR MANUAL LOGIN")
        print("=" * 70)
        print()
        print("Complete the login in the browser window.")
        print("This includes:")
        print("  - Entering your email/password")
        print("  - Solving any CAPTCHA")
        print("  - Completing email/SMS verification")
        print("  - Clicking through any security prompts")
        print()
        print("Once you see your LinkedIn feed or home page, come back here.")
        print()
        input("Press ENTER when you're logged in...")

        # Check current URL
        current_url = page.url
        print(f"\n📍 Current URL: {current_url}")

        if "/login" in current_url or "/checkpoint" in current_url:
            print("⚠️  Still on login/checkpoint page. Continue login and try again.")
            input("Press ENTER when fully logged in...")
            current_url = page.url
            print(f"📍 Current URL: {current_url}")

        # Extract cookies
        cookies = await sb.context.cookies()
        print(f"\n📦 Got {len(cookies)} cookies from browser")

        # Filter to LinkedIn cookies only
        linkedin_cookies = [c for c in cookies if "linkedin.com" in c.get("domain", "")]
        print(f"   LinkedIn cookies: {len(linkedin_cookies)}")

        # Check for essential cookies
        cookie_names = [c["name"] for c in linkedin_cookies]
        has_li_at = "li_at" in cookie_names
        has_jsession = "JSESSIONID" in cookie_names

        print(f"   li_at present: {'✅' if has_li_at else '❌'}")
        print(f"   JSESSIONID present: {'✅' if has_jsession else '❌'}")

        if not has_li_at:
            print("\n❌ li_at cookie not found - login may not be complete")
            print("   Try completing login and run this script again")
            return

        # Convert to cache format
        cookies_dict = {}
        for cookie in linkedin_cookies:
            cookies_dict[cookie["name"]] = {
                "value": cookie["value"],
                "domain": cookie.get("domain", ".linkedin.com"),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", True),
                "httpOnly": cookie.get("httpOnly", False),
                "expirationDate": cookie.get("expires"),
            }

        # Save to cache
        cache_path.write_text(json.dumps(cookies_dict, indent=2))

        # Also save to legacy path
        legacy_path = Path(".linkedin_test_cache.json")
        legacy_path.write_text(json.dumps(cookies_dict, indent=2))

        print()
        print("=" * 70)
        print("✅ SUCCESS - Cookies saved!")
        print("=" * 70)
        print(f"   Cache file : {cache_path}")
        print(f"   Legacy file: {legacy_path}")
        print(f"   Cookies    : {', '.join(cookies_dict.keys())}")
        print()
        print("You can now run extraction tests:")
        print(f"   python test_extraction_cached.py --email {email} --cautious")
        print()

        # Keep browser open briefly
        print("Browser will close in 3 seconds...")
        await asyncio.sleep(3)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Manual LinkedIn login")
    parser.add_argument("--email", type=str, help="LinkedIn account email")
    args = parser.parse_args()

    asyncio.run(manual_login(email=args.email))
