#!/usr/bin/env python3
"""
Test extraction logic offline using saved HTML.

This validates the JavaScript extraction code works correctly
without needing a live session.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from playwright.async_api import async_playwright


async def test_extraction_offline():
    print('=' * 70)
    print('TEST: Extraction Logic (Offline - Using Saved HTML)')
    print('=' * 70)

    # Read saved HTML
    html_path = Path('connections_page_full.html')
    if not html_path.exists():
        print('❌ connections_page_full.html not found')
        print('   Run inspect_with_session.py first to capture the page')
        return

    with open(html_path, 'r') as f:
        html_content = f.read()

    print(f'✅ Loaded HTML: {len(html_content)} bytes')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Load saved HTML
        await page.set_content(html_content)
        print('✅ HTML loaded into browser')

        # Run the extraction JavaScript (same as connection_extractor.py)
        result = await page.evaluate(r'''() => {
            const connections = [];
            const seenUrls = new Set();

            // Find the connections list container
            const listContainer = document.querySelector('[data-view-name="connections-list"]');
            console.log('List container found:', !!listContainer);

            const searchRoot = listContainer || document;

            // Find all connection cards by componentkey (stable attribute)
            const cards = searchRoot.querySelectorAll('[componentkey^="auto-component-"]');
            console.log('Cards found:', cards.length);

            cards.forEach(card => {
                // Find profile link within this card
                const profileLinks = card.querySelectorAll('a[href*="/in/"]');
                if (profileLinks.length === 0) return;

                // Get the profile URL from the first link
                const profileLink = profileLinks[0];
                const url = profileLink.href?.split('?')[0];
                if (!url || seenUrls.has(url)) return;
                seenUrls.add(url);

                // Extract name - look for the innermost text in a profile link
                let name = null;
                for (const link of profileLinks) {
                    // Check for nested <a> with just the name
                    const innerA = link.querySelector('a');
                    if (innerA && innerA.textContent?.trim()) {
                        name = innerA.textContent.trim();
                        break;
                    }
                    // Check for <p> containing <a> with name
                    const pWithA = link.querySelector('p a');
                    if (pWithA && pWithA.textContent?.trim()) {
                        name = pWithA.textContent.trim();
                        break;
                    }
                    // Fallback: use link text if it looks like a name
                    const linkText = link.textContent?.trim();
                    if (linkText && linkText.length > 2 && linkText.length < 60 && !linkText.includes('@')) {
                        if (!linkText.includes(' | ') && !linkText.includes(' at ')) {
                            name = linkText;
                            break;
                        }
                    }
                }

                // Extract headline
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

                // If no name found, try aria-label
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

                // Extract profile image
                const img = card.querySelector('img[src*="licdn"], img[src*="profile"]');
                const imgUrl = img?.src || null;

                connections.push({
                    name,
                    headline,
                    url,
                    imgUrl,
                    connectedDate
                });
            });

            // Fallback if no cards found
            if (connections.length === 0) {
                console.log('No cards found, trying fallback...');
                const profileLinks = searchRoot.querySelectorAll('[data-view-name="connections-profile"]');
                console.log('Profile links with data-view-name:', profileLinks.length);

                const processedUrls = new Set();

                profileLinks.forEach(link => {
                    const url = link.href?.split('?')[0];
                    if (!url || processedUrls.has(url)) return;
                    processedUrls.add(url);

                    let card = link.parentElement;
                    for (let i = 0; i < 8 && card; i++) {
                        if (card.hasAttribute('componentkey')) break;
                        card = card.parentElement;
                    }

                    if (!card) return;

                    let name = null;
                    const nameLink = card.querySelector('a[href*="/in/"] p a, p a[href*="/in/"]');
                    if (nameLink) {
                        name = nameLink.textContent?.trim();
                    } else {
                        const figure = card.querySelector('figure[aria-label]');
                        if (figure) {
                            const ariaLabel = figure.getAttribute('aria-label');
                            if (ariaLabel?.includes("'s profile picture")) {
                                name = ariaLabel.replace("'s profile picture", "").trim();
                            }
                        }
                    }

                    if (!name) return;

                    let headline = null;
                    const paragraphs = card.querySelectorAll('p');
                    for (const p of paragraphs) {
                        const text = p.textContent?.trim();
                        if (!text || text === name || text.length < 10) continue;
                        if (text.startsWith('Connected')) continue;
                        if (/^(Message|Connect|Follow)$/i.test(text)) continue;
                        headline = text;
                        break;
                    }

                    const img = card.querySelector('img[src*="licdn"]');

                    connections.push({
                        name,
                        headline,
                        url,
                        imgUrl: img?.src || null,
                        connectedDate: null
                    });
                });
            }

            return {
                listContainerFound: !!listContainer,
                cardsFound: cards.length,
                connections: connections
            };
        }''')

        await browser.close()

    print('\n' + '=' * 70)
    print('EXTRACTION RESULTS')
    print('=' * 70)

    print(f'\nList container found: {result.get("listContainerFound")}')
    print(f'Cards found: {result.get("cardsFound")}')
    print(f'Connections extracted: {len(result.get("connections", []))}')

    for conn in result.get('connections', []):
        print(f'\n  Name: {conn.get("name", "Unknown")}')
        print(f'  Headline: {conn.get("headline", "N/A")}')
        print(f'  URL: {conn.get("url", "N/A")}')
        print(f'  Connected: {conn.get("connectedDate", "N/A")}')

    if result.get('connections'):
        print('\n✅ Extraction working correctly!')
    else:
        print('\n⚠️ No connections extracted')

    print('\n' + '=' * 70)


if __name__ == '__main__':
    asyncio.run(test_extraction_offline())
