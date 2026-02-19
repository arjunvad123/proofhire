#!/usr/bin/env python3
"""Quick DOM inspection of LinkedIn connections page."""

import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.stealth_browser import StealthBrowser


async def quick_inspect():
    email = os.environ.get('LINKEDIN_TEST_EMAIL')
    password = os.environ.get('LINKEDIN_TEST_PASSWORD')

    print(f'Email: {email}')
    print(f'Password set: {bool(password)}')

    if not email or not password:
        print('Missing credentials')
        return

    print('\n1. Authenticating...')
    auth = LinkedInCredentialAuth()
    result = await auth.login(email=email, password=password)

    # Handle 2FA if required
    if result['status'] == '2fa_required':
        print('2FA required! Check your email/phone for the verification code.')
        code = input('Enter 2FA code: ').strip()
        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state'),
        )

    if result['status'] != 'connected':
        print(f'Login failed: {result}')
        return

    print('✅ Authenticated')
    cookies = result['cookies']

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
        session_id='dom-inspector-quick',
        headless=False
    ) as sb:
        await sb.context.add_cookies(cookie_list)
        page = await sb.new_page()

        print('\n2. Navigating to connections page...')
        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load',
            timeout=30000
        )
        await asyncio.sleep(5)

        if '/login' in page.url:
            print('❌ Redirected to login')
            return

        print(f'✅ Loaded: {page.url}')

        # Save HTML
        print('\n3. Saving page HTML...')
        html = await page.content()
        with open('connections_page_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('   Saved: connections_page_full.html')

        # Analyze DOM
        print('\n4. Analyzing DOM structure...')
        analysis = await page.evaluate(r'''() => {
            const results = {};

            // Find all profile links
            const profileLinks = document.querySelectorAll('a[href*="/in/"]');
            results.profileLinks = profileLinks.length;

            // Find first profile link and analyze its parent structure
            if (profileLinks.length > 0) {
                const link = profileLinks[0];
                results.firstLinkHref = link.href;
                results.firstLinkText = link.textContent.trim();

                // Walk up the DOM to understand card structure
                let el = link;
                let parentChain = [];
                for (let i = 0; i < 10 && el && el !== document.body; i++) {
                    parentChain.push({
                        tag: el.tagName,
                        className: el.className.substring(0, 100),
                        id: el.id || null
                    });
                    el = el.parentElement;
                }
                results.parentChain = parentChain;

                // Get the full card HTML for first connection
                let card = link;
                for (let i = 0; i < 10 && card; i++) {
                    card = card.parentElement;
                    if (card && card.tagName === 'LI') break;
                }
                if (card && card.tagName === 'LI') {
                    results.firstCardHTML = card.outerHTML.substring(0, 3000);
                }
            }

            // Get the main content area classes
            const main = document.querySelector('main');
            if (main) {
                results.mainClass = main.className;
                const firstSection = main.querySelector('section');
                results.firstSectionClass = firstSection?.className || 'none';
            }

            // Find connection count
            const countText = document.body.innerText.match(/(\d+)\s*connection/i);
            results.connectionCountText = countText ? countText[0] : 'not found';

            // Get all unique class patterns containing card/connection/entity
            const allElements = document.querySelectorAll('[class*="card"], [class*="connection"], [class*="entity"], [class*="list-item"]');
            const classPatterns = new Set();
            allElements.forEach(el => {
                el.className.split(' ').forEach(c => {
                    if (c.match(/(card|connection|entity|list-item)/i)) {
                        classPatterns.add(c);
                    }
                });
            });
            results.relevantClasses = Array.from(classPatterns).slice(0, 30);

            return results;
        }''')

        print('\nDOM Analysis Results:')
        print(f'  Profile links found: {analysis.get("profileLinks", 0)}')
        print(f'  Connection count text: {analysis.get("connectionCountText", "?")}')
        print(f'  First link href: {analysis.get("firstLinkHref", "none")[:80]}...')
        print(f'  First link text: {analysis.get("firstLinkText", "none")}')
        print(f'  Main class: {analysis.get("mainClass", "none")}')
        print(f'  First section class: {analysis.get("firstSectionClass", "none")}')

        print('\n  Parent chain from first profile link:')
        for i, p in enumerate(analysis.get('parentChain', [])):
            print(f'    {i}: <{p["tag"]}> class="{p["className"][:60]}..."')

        print('\n  Relevant classes found:')
        for cls in analysis.get('relevantClasses', [])[:15]:
            print(f'    - {cls}')

        # Print first card HTML
        if analysis.get('firstCardHTML'):
            print('\n  First connection card HTML (truncated):')
            print('  ' + '-' * 60)
            html_preview = analysis['firstCardHTML'][:1500]
            for line in html_preview.split('\n')[:30]:
                print(f'    {line[:100]}')
            print('  ' + '-' * 60)

        # Save analysis to JSON
        with open('dom_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print('\n  Analysis saved to: dom_analysis.json')

        # Take screenshot
        await page.screenshot(path='connections_dom_snapshot.png', full_page=True)
        print('\n5. Screenshot saved: connections_dom_snapshot.png')

        # Wait briefly to see the browser
        await asyncio.sleep(3)

        print('\nDone!')


if __name__ == '__main__':
    asyncio.run(quick_inspect())
