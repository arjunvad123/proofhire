#!/usr/bin/env python3
"""
Extract the actual selector LinkedIn uses for connection cards.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def extract_selector(session_id: str):
    """Find the real selector."""

    session_manager = LinkedInSessionManager()
    cookies = await session_manager.get_session_cookies(session_id)

    async with async_playwright() as p:
        profile_dir = Path('./browser_profiles') / session_id
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load',
            timeout=0
        )
        await asyncio.sleep(10)

        # Extract connection data using JavaScript
        connections = await page.evaluate('''() => {
            // Look for the connection card - it has the profile link and info
            const results = [];
            
            // The card appears to be in a list structure
            // Let's find all elements that contain profile links
            const profileLinks = document.querySelectorAll('a[href*="/in/"]');
            
            profileLinks.forEach(link => {
                // Get the container that has all the connection info
                const container = link.closest('[data-view-name*="connection"]') || 
                                link.closest('li') ||
                                link.closest('[class*="entity-result"]');
                
                if (container && container.querySelector('img')) {
                    const name = container.querySelector('[aria-label]')?.textContent?.trim() || 
                                container.querySelector('span[dir="ltr"]')?.textContent?.trim();
                    
                    const headline = Array.from(container.querySelectorAll('span'))
                        .find(s => s.textContent.includes('@') || s.textContent.includes('|'))
                        ?.textContent?.trim();
                    
                    results.push({
                        name: name,
                        headline: headline,
                        profileUrl: link.href,
                        containerTag: container.tagName,
                        containerClasses: container.className,
                        outerHTML: container.outerHTML.substring(0, 500)
                    });
                }
            });
            
            return results;
        }''')

        print("=" * 70)
        print("EXTRACTED CONNECTIONS:")
        print("=" * 70)
        print()

        for i, conn in enumerate(connections, 1):
            print(f"{i}. Name: {conn['name']}")
            print(f"   Headline: {conn['headline']}")
            print(f"   URL: {conn['profileUrl']}")
            print(f"   Container: <{conn['containerTag']}> with classes:")
            print(f"   {conn['containerClasses'][:200]}")
            print()

        if connections:
            print("=" * 70)
            print("RECOMMENDED SELECTOR:")
            print("=" * 70)
            # Extract common class pattern
            first_classes = connections[0]['containerClasses'].split()
            print(f"Try: {connections[0]['containerTag']}.{first_classes[0] if first_classes else ''}")
            print(f"Or: {connections[0]['containerTag']}[class*=\"{first_classes[0][:10] if first_classes else ''}\"]")

        await context.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_real_selector.py <session_id>")
        sys.exit(1)

    session_id = sys.argv[1]
    asyncio.run(extract_selector(session_id))
