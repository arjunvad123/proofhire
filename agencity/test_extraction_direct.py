#!/usr/bin/env python3
"""
Test connection extraction directly with cookies (no Supabase session).
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
from app.services.linkedin.session_manager import LinkedInSessionManager


async def test_extraction():
    """Test extraction flow with fresh authentication."""
    print("=" * 70)
    print("CONNECTION EXTRACTION TEST")
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
        print(f"❌ Login failed: {result.get('error')}")
        return

    cookies = result['cookies']
    print(f"✅ Authenticated - {len(cookies)} cookies obtained")

    # Step 2: Test extraction with cookies directly
    print("\n2. Starting connection extraction...")

    extractor = LinkedInConnectionExtractor(session_manager=LinkedInSessionManager())

    # We'll pass cookies directly instead of session_id
    # First let's modify the extractor to accept cookies

    async def progress(found, estimated):
        print(f"   Progress: {found}/{estimated} connections")

    try:
        # Call the extraction with a mock session
        # We need to create a temporary mock session
        result = await extractor._extract_with_cookies(cookies, progress)

        print(f"\n3. Extraction Results:")
        print(f"   Status: {result['status']}")

        if result['status'] == 'success':
            print(f"   ✅ Extracted {result['total']} connections")
            print(f"   Duration: {result.get('duration_seconds', 0):.1f}s")

            # Print first 5 connections
            if result['connections']:
                print(f"\n   Sample connections:")
                for conn in result['connections'][:5]:
                    print(f"   - {conn['full_name']}")
                    print(f"     {conn['headline']}")
                    print(f"     {conn['linkedin_url']}")
                    print()

                if result['total'] > 5:
                    print(f"   ... and {result['total'] - 5} more")
        else:
            print(f"   ❌ Extraction failed: {result.get('error')}")

    except AttributeError:
        print("\n   Note: Using standard extraction method...")
        # Fall back to creating a temp session
        print("   Creating temporary session...")

        # For now, just test navigation
        from app.services.linkedin.stealth_browser import StealthBrowser

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

        async with StealthBrowser.launch_persistent(
            session_id='test-extraction',
            headless=False
        ) as sb:
            await sb.context.add_cookies(cookie_list)
            page = await sb.new_page()

            print("\n   Navigating to connections page...")
            await page.goto(
                'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                wait_until='load',
                timeout=30000
            )
            await asyncio.sleep(3)

            if '/login' in page.url:
                print("   ❌ Redirected to login")
            else:
                print("   ✅ Connections page loaded successfully!")

                # Try to count connections
                try:
                    # Wait for connection cards
                    await page.wait_for_selector('[data-view-name="list-view"]', timeout=10000)

                    # Get connection cards
                    cards = await page.locator('li.mn-connection-card').all()
                    print(f"   Found {len(cards)} connection cards on first page")

                    if cards:
                        print("\n   Sample connections:")
                        for i, card in enumerate(cards[:3]):
                            try:
                                name_elem = card.locator('.mn-connection-card__name')
                                name = await name_elem.text_content()
                                print(f"   {i+1}. {name.strip()}")
                            except:
                                pass

                except Exception as e:
                    print(f"   ⚠️  Could not parse connections: {e}")

                # Screenshot
                await page.screenshot(path='extraction_test.png', full_page=True)
                print("\n   Screenshot saved: extraction_test.png")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    asyncio.run(test_extraction())
