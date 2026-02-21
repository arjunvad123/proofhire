#!/usr/bin/env python3
"""Inspect LinkedIn connections DOM using existing session."""

import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from app.services.linkedin.stealth_browser import StealthBrowser

# Use most recent session
SESSION_ID = 'f5a79aa5-58c5-4930-ae13-cffefb318d8a'


async def inspect_dom():
    print('=' * 70)
    print('LINKEDIN CONNECTIONS DOM INSPECTOR (Using Existing Session)')
    print('=' * 70)

    print(f'\n1. Loading session: {SESSION_ID}')
    mgr = LinkedInSessionManager()
    cookies = await mgr.get_session_cookies(SESSION_ID)

    if not cookies:
        print('❌ Session not found or expired')
        return

    print(f'✅ Loaded {len(cookies)} cookies')

    # Convert cookies to list format
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
        session_id='dom-inspector-session',
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

        current_url = page.url
        print(f'   Current URL: {current_url}')

        if '/login' in current_url or '/checkpoint' in current_url:
            print('❌ Redirected to login - session may be invalid')
            await page.screenshot(path='login_redirect.png')
            return

        print(f'✅ Loaded connections page')

        # Save HTML
        print('\n3. Saving page HTML...')
        html = await page.content()
        with open('connections_page_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'   Saved: connections_page_full.html ({len(html)} bytes)')

        # Detailed DOM analysis
        print('\n4. Analyzing DOM structure...')
        analysis = await page.evaluate(r'''() => {
            const results = {};

            // Find all profile links
            const profileLinks = document.querySelectorAll('a[href*="/in/"]');
            results.profileLinks = profileLinks.length;
            results.profileLinksDetails = [];

            // Analyze each profile link
            profileLinks.forEach((link, idx) => {
                if (idx >= 5) return; // Only first 5

                const info = {
                    href: link.href,
                    text: link.textContent.trim().substring(0, 50),
                    className: link.className,
                    parentTag: link.parentElement?.tagName,
                    parentClass: link.parentElement?.className?.substring(0, 50)
                };
                results.profileLinksDetails.push(info);
            });

            // Find first profile link and walk up to find the card
            if (profileLinks.length > 0) {
                const link = profileLinks[0];

                // Walk up the DOM to understand card structure
                let el = link;
                let parentChain = [];
                for (let i = 0; i < 12 && el && el !== document.body; i++) {
                    parentChain.push({
                        tag: el.tagName,
                        className: el.className?.substring(0, 80) || '',
                        id: el.id || null,
                        dataAttrs: Object.keys(el.dataset || {}).slice(0, 5)
                    });
                    el = el.parentElement;
                }
                results.parentChain = parentChain;

                // Get the full card HTML
                let card = link;
                for (let i = 0; i < 10 && card; i++) {
                    card = card.parentElement;
                    if (card && card.tagName === 'LI') break;
                }
                if (card && card.tagName === 'LI') {
                    results.firstCardOuterHTML = card.outerHTML;
                    results.firstCardClasses = card.className;

                    // Extract all text nodes
                    const walker = document.createTreeWalker(card, NodeFilter.SHOW_TEXT, null, false);
                    const texts = [];
                    let node;
                    while (node = walker.nextNode()) {
                        const text = node.textContent.trim();
                        if (text && text.length > 2 && text.length < 200) {
                            texts.push(text);
                        }
                    }
                    results.firstCardTextContent = texts;
                }
            }

            // Connection count
            const countMatch = document.body.innerText.match(/(\d+)\s*connection/i);
            results.connectionCount = countMatch ? countMatch[0] : 'not found';

            // Get main structural elements
            const main = document.querySelector('main');
            if (main) {
                results.mainClass = main.className;

                // Find list containers
                const lists = main.querySelectorAll('ul');
                results.ulCount = lists.length;
                results.ulClasses = Array.from(lists).slice(0, 5).map(ul => ul.className.substring(0, 60));

                // Find all LI elements with profile links
                const lis = main.querySelectorAll('li');
                results.liCount = lis.length;

                // Find LIs that contain profile links
                const lisWithLinks = Array.from(lis).filter(li => li.querySelector('a[href*="/in/"]'));
                results.lisWithProfileLinks = lisWithLinks.length;
                if (lisWithLinks.length > 0) {
                    results.firstLiWithLinkClass = lisWithLinks[0].className;
                }
            }

            // Find all elements with data attributes (LinkedIn uses these)
            const dataElements = document.querySelectorAll('[data-view-name], [data-control-name], [data-entity-hovercard-id]');
            results.dataAttributeElements = dataElements.length;
            results.dataAttrs = Array.from(dataElements).slice(0, 10).map(el => ({
                tag: el.tagName,
                viewName: el.dataset.viewName,
                controlName: el.dataset.controlName,
                entityId: el.dataset.entityHovercardId?.substring(0, 30)
            }));

            return results;
        }''')

        print('\n' + '=' * 70)
        print('DOM ANALYSIS RESULTS')
        print('=' * 70)

        print(f'\n📊 Overview:')
        print(f'   Profile links found: {analysis.get("profileLinks", 0)}')
        print(f'   Connection count: {analysis.get("connectionCount", "?")}')
        print(f'   <ul> elements in main: {analysis.get("ulCount", 0)}')
        print(f'   <li> elements in main: {analysis.get("liCount", 0)}')
        print(f'   <li> with profile links: {analysis.get("lisWithProfileLinks", 0)}')
        print(f'   Elements with data-* attrs: {analysis.get("dataAttributeElements", 0)}')

        print(f'\n🔗 First 5 profile links:')
        for i, link in enumerate(analysis.get('profileLinksDetails', [])):
            print(f'   {i+1}. {link["text"][:30]}...')
            print(f'      href: {link["href"][:60]}...')
            print(f'      class: {link["className"][:50]}')

        print(f'\n📐 Parent chain from first profile link:')
        for i, p in enumerate(analysis.get('parentChain', [])):
            data_attrs = ', '.join(p.get('dataAttrs', [])) if p.get('dataAttrs') else ''
            print(f'   {i}: <{p["tag"]}> class="{p["className"][:50]}..." {f"data=[{data_attrs}]" if data_attrs else ""}')

        print(f'\n📋 First connection card classes:')
        print(f'   {analysis.get("firstCardClasses", "none")}')

        print(f'\n📝 First card text content:')
        for text in analysis.get('firstCardTextContent', [])[:10]:
            print(f'   - "{text[:60]}{"..." if len(text) > 60 else ""}"')

        print(f'\n🏷️ Data attribute elements:')
        for attr in analysis.get('dataAttrs', [])[:5]:
            print(f'   <{attr["tag"]}> view={attr.get("viewName")} control={attr.get("controlName")} entity={attr.get("entityId", "")[:20]}...')

        # Save the first card HTML separately for detailed inspection
        if analysis.get('firstCardOuterHTML'):
            with open('first_connection_card.html', 'w') as f:
                f.write(analysis['firstCardOuterHTML'])
            print(f'\n💾 First card HTML saved to: first_connection_card.html')

        # Save full analysis
        with open('dom_analysis.json', 'w') as f:
            # Remove the large HTML from JSON output
            analysis_copy = {k: v for k, v in analysis.items() if k != 'firstCardOuterHTML'}
            json.dump(analysis_copy, f, indent=2)
        print(f'💾 Analysis saved to: dom_analysis.json')

        # Take screenshot
        await page.screenshot(path='connections_dom_snapshot.png', full_page=True)
        print(f'📸 Screenshot saved: connections_dom_snapshot.png')

        print('\n' + '=' * 70)
        print('Done! Browser will close in 5 seconds...')
        await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(inspect_dom())
