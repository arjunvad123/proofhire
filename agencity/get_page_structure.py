#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def get_structure():
    sm = LinkedInSessionManager()
    cookies = await sm.get_session_cookies(sys.argv[1])
    async with async_playwright() as p:
        pd = Path('./browser_profiles') / sys.argv[1]
        ctx = await p.chromium.launch_persistent_context(user_data_dir=str(pd), headless=False, viewport={'width':1920,'height':1080})
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto('https://www.linkedin.com/mynetwork/invite-connect/connections/', wait_until='load', timeout=0)
        await asyncio.sleep(10)
        
        # Get the HTML of the main content area
        html = await page.evaluate('''() => {
            const main = document.querySelector('main');
            return main ? main.innerHTML : 'NO MAIN FOUND';
        }''')
        
        # Save to file
        with open('linkedin_main_content.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("Saved HTML to: linkedin_main_content.html")
        print(f"Size: {len(html)} characters")
        
        # Also try to find any div/section with the connection name
        selector_test = await page.evaluate('''() => {
            const text = "Aidan Nguyen-Tran";
            const all = document.querySelectorAll('*');
            const matches = [];
            all.forEach(el => {
                if (el.textContent.includes(text) && el.children.length < 20) {
                    matches.push({
                        tag: el.tagName,
                        classes: el.className,
                        text: el.textContent.substring(0, 200)
                    });
                }
            });
            return matches.slice(0, 10);
        }''')
        
        print("\nElements containing connection name:")
        for i, m in enumerate(selector_test[:5], 1):
            print(f"{i}. <{m['tag']}> classes: {m['classes'][:100]}")
        
        await ctx.close()

asyncio.run(get_structure())
