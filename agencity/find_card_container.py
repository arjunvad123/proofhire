#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def find_card():
    session_manager = LinkedInSessionManager()
    cookies = await session_manager.get_session_cookies(sys.argv[1])
    async with async_playwright() as p:
        profile_dir = Path('./browser_profiles') / sys.argv[1]
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir), headless=False,
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto('https://www.linkedin.com/mynetwork/invite-connect/connections/', wait_until='load', timeout=0)
        await asyncio.sleep(10)
        
        data = await page.evaluate('''() => {
            // Find the main list container
            const lists = document.querySelectorAll('ul');
            let bestMatch = null;
            
            lists.forEach(ul => {
                const items = ul.querySelectorAll('li');
                items.forEach(li => {
                    const hasProfileLink = li.querySelector('a[href*="/in/"]');
                    const hasImage = li.querySelector('img');
                    const hasText = li.textContent.trim().length > 20;
                    
                    if (hasProfileLink && hasImage && hasText) {
                        const name = li.textContent.split('\\n')[0].trim();
                        bestMatch = {
                            containerTag: 'li',
                            containerClasses: li.className,
                            ulClasses: ul.className,
                            name: name,
                            innerHTML: li.innerHTML.substring(0, 1000)
                        };
                    }
                });
            });
            
            return bestMatch;
        }''')
        
        if data:
            print("FOUND CONNECTION CARD!")
            print(f"Container: <li> with classes: {data['containerClasses'][:200]}")
            print(f"Parent <ul> classes: {data['ulClasses'][:200]}")
            print(f"Name found: {data['name'][:50]}")
            print()
            print("SELECTOR TO USE:")
            classes = data['containerClasses'].split()
            if classes:
                print(f"  li.{classes[0]}")
        else:
            print("No connection card found!")
        
        await context.close()

asyncio.run(find_card())
