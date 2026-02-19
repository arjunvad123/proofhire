#!/usr/bin/env python3
"""
Debug why the LinkedIn connections page is timing out.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def debug_connections_page(session_id: str):
    """Debug connections page access."""

    print("=" * 70)
    print("DEBUG: LinkedIn Connections Page Access")
    print("=" * 70)
    print()

    session_manager = LinkedInSessionManager()

    # Get cookies
    print("Step 1: Retrieving cookies...")
    cookies = await session_manager.get_session_cookies(session_id)

    if not cookies or 'li_at' not in cookies:
        print("❌ Session not found!")
        return

    print("✅ Cookies retrieved")
    print()

    async with async_playwright() as p:
        # Use persistent context (like the extractor does)
        profile_dir = Path('./browser_profiles') / session_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        print(f"Step 2: Launching persistent browser profile...")
        print(f"   Profile: {profile_dir}")
        print()

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Los_Angeles',
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Check if cookies already exist in profile
        current_cookies = await context.cookies()
        has_li_at = any(c['name'] == 'li_at' for c in current_cookies)

        print(f"Step 3: Checking existing cookies in profile...")
        print(f"   Cookies in profile: {len(current_cookies)}")
        print(f"   Has li_at: {has_li_at}")
        print()

        # Add cookies if not present
        if not has_li_at:
            print("Step 4: Adding cookies to browser context...")
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

            await context.add_cookies(cookie_list)
            print("✅ Cookies added")
            print()
        else:
            print("✅ Cookies already in profile")
            print()

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # Try different approaches
        print("=" * 70)
        print("ATTEMPT 1: Navigate directly to connections page")
        print("=" * 70)
        print()

        try:
            print("Navigating to: https://www.linkedin.com/mynetwork/invite-connect/connections/")
            print("Wait strategy: load (no timeout)")

            await page.goto(
                'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                wait_until='load',
                timeout=0  # No timeout - wait indefinitely
            )

            await asyncio.sleep(3)

            print(f"✅ Page loaded!")
            print(f"   URL: {page.url}")
            print()

            # Check if we're on the right page
            if '/mynetwork' in page.url and '/connections' in page.url:
                print("✅ Successfully on connections page!")
            elif '/login' in page.url:
                print("⚠️ Redirected to login page")
            elif '/checkpoint' in page.url:
                print("⚠️ LinkedIn checkpoint/verification")
            else:
                print(f"⚠️ Unexpected URL: {page.url}")

        except Exception as e:
            print(f"❌ Failed: {e}")

        print()
        print("=" * 70)
        print("ATTEMPT 2: Navigate to feed first, then connections")
        print("=" * 70)
        print()

        try:
            print("Step A: Navigate to feed...")
            await page.goto('https://www.linkedin.com/feed/', wait_until='load', timeout=30000)
            await asyncio.sleep(2)
            print(f"   Feed URL: {page.url}")

            print()
            print("Step B: Navigate to connections from feed...")
            await page.goto(
                'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                wait_until='load',
                timeout=30000
            )
            await asyncio.sleep(2)

            print(f"✅ Page loaded!")
            print(f"   URL: {page.url}")
            print()

            if '/mynetwork' in page.url and '/connections' in page.url:
                print("✅ Successfully on connections page!")

                # Try to extract a connection card
                print()
                print("Checking for connection cards...")
                card_count = await page.locator('li.mn-connection-card').count()
                print(f"   Connection cards found: {card_count}")

                if card_count > 0:
                    print()
                    print("✅ Connection cards detected! Extraction should work.")
                else:
                    print()
                    print("⚠️ No connection cards found. Page might still be loading.")

                    # Wait a bit longer
                    print("   Waiting 5 more seconds...")
                    await asyncio.sleep(5)
                    card_count = await page.locator('li.mn-connection-card').count()
                    print(f"   Connection cards now: {card_count}")

            else:
                print(f"⚠️ Not on connections page: {page.url}")

        except Exception as e:
            print(f"❌ Failed: {e}")

        print()
        print("Browser will stay open for 15 seconds for inspection...")
        await asyncio.sleep(15)

        await context.close()

    print()
    print("=" * 70)
    print("Debug complete!")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_connections_page.py <session_id>")
        print()
        print("Get session ID from: python test_auth_only.py")
        sys.exit(1)

    session_id = sys.argv[1]
    asyncio.run(debug_connections_page(session_id))
