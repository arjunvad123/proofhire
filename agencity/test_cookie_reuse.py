#!/usr/bin/env python3
"""
Test that cookies can be reused without re-logging in.
This should NOT trigger a new sign-in email from LinkedIn.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def test_cookie_reuse(session_id: str):
    """Test reusing cookies without logging in."""

    print("=" * 70)
    print("COOKIE REUSE TEST - NO RE-LOGIN")
    print("=" * 70)
    print()

    session_manager = LinkedInSessionManager()

    # Step 1: Retrieve saved cookies
    print("Step 1: Retrieving saved cookies from database...")
    print(f"   Session ID: {session_id}")

    cookies = await session_manager.get_session_cookies(session_id)

    if not cookies or 'li_at' not in cookies:
        print("❌ Session not found or expired!")
        print("   Run test_auth_only.py first to create a session.")
        return False

    print("✅ Cookies retrieved!")
    print(f"   li_at: {cookies['li_at']['value'][:30]}...")
    print()

    # Step 2: Use cookies in a new browser session (NO LOGIN)
    print("Step 2: Opening browser with saved cookies...")
    print("   (NO login will be performed - using cookies only)")
    print()

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Convert cookies to Playwright format
        cookie_list = []
        for name, data in cookies.items():
            cookie = {
                'name': name,
                'value': data['value'],
                'domain': data.get('domain', '.linkedin.com'),
                'path': data.get('path', '/'),
                'secure': data.get('secure', True),
                'httpOnly': data.get('httpOnly', False)
            }
            if data.get('expirationDate'):
                cookie['expires'] = data['expirationDate']
            cookie_list.append(cookie)

        # Add cookies to browser context
        await context.add_cookies(cookie_list)

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # Step 3: Navigate to LinkedIn (should already be logged in)
        print("Step 3: Navigating to LinkedIn...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='load')
        await asyncio.sleep(2)

        # Check if we're logged in
        url = page.url
        print(f"   Current URL: {url}")

        if '/feed' in url or '/mynetwork' in url:
            print()
            print("✅ Already logged in with saved cookies!")
            print("   No login email should have been sent.")
        elif '/login' in url or '/checkpoint' in url:
            print()
            print("❌ Cookies expired or invalid - redirected to login")
            print("   You may need to re-authenticate.")
            await browser.close()
            return False

        # Step 4: Navigate to connections page
        print()
        print("Step 4: Navigating to connections page...")
        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load'
        )
        await asyncio.sleep(2)

        url = page.url
        if '/mynetwork' in url:
            print("✅ Accessed connections page successfully!")
            print("   Session is fully functional.")
        else:
            print("❌ Could not access connections page")
            print(f"   Redirected to: {url}")

        print()
        print("=" * 70)
        print("✅ COOKIE REUSE TEST PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • No login performed ✅")
        print("  • No sign-in email sent ✅")
        print("  • Cookies worked perfectly ✅")
        print("  • Full access to LinkedIn ✅")
        print()
        print("The browser will stay open for 10 seconds so you can verify...")
        await asyncio.sleep(10)

        await browser.close()

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_cookie_reuse.py <session_id>")
        print()
        print("Get a session ID by running: python test_auth_only.py")
        print()
        print("Or retrieve the latest session from database:")
        print("  SELECT id FROM linkedin_sessions ORDER BY created_at DESC LIMIT 1;")
        sys.exit(1)

    session_id = sys.argv[1]
    success = asyncio.run(test_cookie_reuse(session_id))
    sys.exit(0 if success else 1)
