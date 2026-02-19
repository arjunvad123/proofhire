#!/usr/bin/env python3
"""
Inspect the actual DOM structure of LinkedIn connections page.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.stealth_browser import StealthBrowser


async def inspect_dom():
    """Inspect the connections page DOM structure."""
    print("=" * 70)
    print("LINKEDIN CONNECTIONS DOM INSPECTOR")
    print("=" * 70)

    # Authenticate
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
    print(f"✅ Authenticated")

    # Convert cookies
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
        session_id='dom-inspector',
        headless=False
    ) as sb:
        await sb.context.add_cookies(cookie_list)
        page = await sb.new_page()

        print("\n2. Navigating to connections page...")
        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load',
            timeout=30000
        )
        await asyncio.sleep(3)

        if '/login' in page.url:
            print("❌ Redirected to login")
            return

        print(f"✅ Loaded: {page.url}")

        # Save full HTML
        print("\n3. Saving page HTML...")
        html = await page.content()
        with open('connections_page_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("   Saved: connections_page_full.html")

        # Inspect structure
        print("\n4. Inspecting DOM structure...")

        # Check for main container
        containers = await page.locator('main').all()
        print(f"   <main> elements: {len(containers)}")

        # Look for list containers
        lists = await page.locator('ul').all()
        print(f"   <ul> elements: {len(lists)}")

        # Look for connection cards (try different selectors)
        selectors_to_try = [
            'li.mn-connection-card',
            'li[class*="connection"]',
            'div[class*="connection-card"]',
            'li[data-view-name]',
            'ul[class*="mn-connections"] li',
            'div.scaffold-finite-scroll__content li',
        ]

        print("\n5. Testing selectors:")
        for selector in selectors_to_try:
            try:
                elements = await page.locator(selector).all()
                print(f"   {selector}: {len(elements)} elements")

                if elements and len(elements) > 0:
                    # Get the outer HTML of first element
                    first = elements[0]
                    outer_html = await first.evaluate('el => el.outerHTML')
                    print(f"   First element HTML (truncated):")
                    print(f"   {outer_html[:300]}...")
            except Exception as e:
                print(f"   {selector}: ERROR - {e}")

        # Get all classes used in the page
        print("\n6. Finding connection-related classes...")
        classes = await page.evaluate('''() => {
            const elements = document.querySelectorAll('[class*="connection"], [class*="mn-"]');
            const classes = new Set();
            elements.forEach(el => {
                el.className.split(' ').forEach(c => {
                    if (c.includes('connection') || c.includes('mn-')) {
                        classes.add(c);
                    }
                });
            });
            return Array.from(classes);
        }''')
        print(f"   Found {len(classes)} connection-related classes:")
        for cls in sorted(classes)[:20]:
            print(f"   - {cls}")

        # Try to find the actual structure
        print("\n7. Analyzing page structure...")
        structure = await page.evaluate('''() => {
            const main = document.querySelector('main');
            if (!main) return 'No main element';

            const sections = main.querySelectorAll('section');
            const divs = main.querySelectorAll('div[class]');
            const lists = main.querySelectorAll('ul');

            return {
                sections: sections.length,
                divs: divs.length,
                lists: lists.length,
                mainClasses: main.className,
                firstSectionClasses: sections[0]?.className || 'none',
                firstListClasses: lists[0]?.className || 'none'
            };
        }''')
        print(f"   Structure: {structure}")

        # Take screenshot
        print("\n8. Taking screenshot...")
        await page.screenshot(path='connections_dom_inspection.png', full_page=True)
        print("   Saved: connections_dom_inspection.png")

        print("\n9. Waiting for manual inspection (browser will stay open)...")
        print("   Press Ctrl+C when done")

        try:
            await asyncio.sleep(300)  # Wait 5 minutes
        except KeyboardInterrupt:
            print("\n   Inspection complete")

        print("\n" + "=" * 70)


if __name__ == '__main__':
    asyncio.run(inspect_dom())
