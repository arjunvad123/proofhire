#!/usr/bin/env python3
"""
Find the actual selectors LinkedIn uses for connection cards.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def find_selectors(session_id: str):
    """Find working selectors for LinkedIn connections."""

    session_manager = LinkedInSessionManager()
    cookies = await session_manager.get_session_cookies(session_id)

    if not cookies:
        print("❌ Session not found!")
        return

    async with async_playwright() as p:
        profile_dir = Path('./browser_profiles') / session_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        print("Navigating to connections page...")
        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load',
            timeout=0
        )

        print("Waiting 10 seconds for page to fully render...")
        await asyncio.sleep(10)

        # Scroll a bit to trigger lazy loading
        print("Scrolling to trigger content loading...")
        await page.evaluate('window.scrollBy(0, 800)')
        await asyncio.sleep(3)

        print()
        print("=" * 70)
        print("Analyzing page structure...")
        print("=" * 70)
        print()

        # Use JavaScript to find all list items that might be connections
        result = await page.evaluate('''() => {
            const analysis = {
                allLiElements: [],
                possibleConnections: [],
                mainContent: null,
                searchResults: []
            };

            // Find all <li> elements
            const allLis = document.querySelectorAll('li');
            analysis.allLiElements = Array.from(allLis).slice(0, 20).map(li => {
                return {
                    classes: li.className,
                    hasLink: li.querySelector('a[href*="/in/"]') ? true : false,
                    textPreview: li.textContent.substring(0, 100).trim()
                };
            });

            // Look for elements with profile links
            const profileLinks = document.querySelectorAll('a[href*="/in/"]');
            const connectionContainers = new Set();

            profileLinks.forEach(link => {
                // Find the closest list item or container
                let container = link.closest('li');
                if (container && !connectionContainers.has(container)) {
                    connectionContainers.add(container);
                    analysis.possibleConnections.push({
                        liClasses: container.className,
                        profileUrl: link.href,
                        hasImage: container.querySelector('img') ? true : false,
                        textPreview: container.textContent.substring(0, 150).trim()
                    });
                }
            });

            // Find main content area
            const main = document.querySelector('main');
            if (main) {
                analysis.mainContent = {
                    classes: main.className,
                    childCount: main.children.length
                };
            }

            // Look for search result patterns
            const searchResults = document.querySelectorAll('[class*="search"]');
            analysis.searchResults = Array.from(searchResults).slice(0, 5).map(el => el.className);

            return analysis;
        }''')

        print("FOUND LI ELEMENTS (first 20):")
        print("-" * 70)
        for i, li in enumerate(result['allLiElements'][:10], 1):
            print(f"{i}. Classes: {li['classes'][:100]}")
            print(f"   Has profile link: {li['hasLink']}")
            print(f"   Text: {li['textPreview'][:80]}...")
            print()

        print()
        print("=" * 70)
        print("POSSIBLE CONNECTION CONTAINERS:")
        print("-" * 70)
        for i, conn in enumerate(result['possibleConnections'][:10], 1):
            print(f"{i}. Container classes: {conn['liClasses'][:150]}")
            print(f"   Profile URL: {conn['profileUrl']}")
            print(f"   Has image: {conn['hasImage']}")
            print(f"   Preview: {conn['textPreview'][:100]}...")
            print()

        if result['mainContent']:
            print()
            print("=" * 70)
            print("MAIN CONTENT AREA:")
            print(f"Classes: {result['mainContent']['classes']}")
            print(f"Children: {result['mainContent']['childCount']}")

        print()
        print("=" * 70)
        print("Browser will stay open for 30 seconds...")
        print("Please manually inspect the page to verify what you see!")
        print("=" * 70)
        await asyncio.sleep(30)

        await context.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_connection_selectors.py <session_id>")
        sys.exit(1)

    session_id = sys.argv[1]
    asyncio.run(find_selectors(session_id))
