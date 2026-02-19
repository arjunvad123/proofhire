#!/usr/bin/env python3
"""
Diagnostic script to understand session invalidation issue.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.stealth_browser import StealthBrowser


async def diagnose():
    """Run diagnostic tests on the authentication and session."""
    print("=" * 70)
    print("LINKEDIN SESSION DIAGNOSTIC")
    print("=" * 70)

    # Step 1: Authenticate
    email = os.environ.get('LINKEDIN_TEST_EMAIL')
    password = os.environ.get('LINKEDIN_TEST_PASSWORD')

    if not email or not password:
        print("❌ Set LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD")
        return

    print("\n1. Authenticating...")
    auth = LinkedInCredentialAuth()
    result = await auth.login(email=email, password=password)

    if result['status'] != 'connected':
        print(f"❌ Login failed: {result.get('error', result)}")
        return

    cookies = result['cookies']
    print(f"✅ Authenticated successfully")
    print(f"   Cookies obtained: {len(cookies)} cookies")

    # Print cookie details
    print("\n2. Cookie Analysis:")
    for name, data in cookies.items():
        print(f"   {name}:")
        print(f"     domain: {data.get('domain')}")
        print(f"     path: {data.get('path')}")
        print(f"     secure: {data.get('secure')}")
        print(f"     httpOnly: {data.get('httpOnly')}")
        print(f"     expires: {data.get('expirationDate', 'session')}")

    # Step 2: Test cookie injection
    print("\n3. Testing cookie injection in fresh browser...")

    # Convert to list format
    cookie_list = []
    for name, data in cookies.items():
        cookie = {
            'name': name,
            'value': data['value'],
            'domain': data.get('domain', '.linkedin.com'),
            'path': data.get('path', '/'),
            'secure': data.get('secure', True),
            'httpOnly': data.get('httpOnly', False),
        }
        if data.get('expirationDate'):
            cookie['expires'] = data['expirationDate']
        cookie_list.append(cookie)

    async with StealthBrowser.launch(headless=False) as sb:
        # First, inject cookies
        await sb.context.add_cookies(cookie_list)
        print("   ✅ Cookies injected")

        # Verify cookies were set
        injected = await sb.context.cookies()
        print(f"   ✅ {len(injected)} cookies in context")

        page = await sb.new_page()

        # Test navigation sequence
        urls_to_test = [
            ('https://www.linkedin.com/feed/', 'Feed'),
            ('https://www.linkedin.com/mynetwork/', 'My Network'),
            ('https://www.linkedin.com/mynetwork/invite-connect/connections/', 'Connections'),
        ]

        print("\n4. Testing navigation sequence:")
        for url, name in urls_to_test:
            print(f"\n   Navigating to {name}...")
            await page.goto(url, wait_until='load', timeout=30000)
            await asyncio.sleep(2)

            final_url = page.url
            print(f"   Final URL: {final_url}")

            # Check if redirected to login
            if '/login' in final_url or '/checkpoint' in final_url:
                print(f"   ❌ REDIRECTED TO LOGIN/CHECKPOINT")

                # Get current cookies
                current_cookies = await sb.context.cookies()
                print(f"   Cookies remaining: {len(current_cookies)}")

                # Check for li_at specifically
                li_at = [c for c in current_cookies if c['name'] == 'li_at']
                if li_at:
                    print(f"   ✅ li_at cookie still present")
                else:
                    print(f"   ❌ li_at cookie MISSING")

                # Take screenshot
                screenshot = f"diagnostic_{name.lower().replace(' ', '_')}.png"
                await page.screenshot(path=screenshot, full_page=True)
                print(f"   Screenshot: {screenshot}")

                break
            else:
                print(f"   ✅ Success - loaded {name}")

                # Check for session indicator elements
                try:
                    nav = await page.locator('nav.global-nav').count()
                    print(f"   Navigation bar present: {nav > 0}")
                except:
                    pass

        print("\n" + "=" * 70)
        print("Diagnostic complete. Check screenshots for details.")
        print("=" * 70)


if __name__ == '__main__':
    asyncio.run(diagnose())
