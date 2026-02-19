#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def debug_check():
    sm = LinkedInSessionManager()
    cookies = await sm.get_session_cookies(sys.argv[1])
    
    async with async_playwright() as p:
        pd = Path('./browser_profiles') / sys.argv[1]
        ctx = await p.chromium.launch_persistent_context(user_data_dir=str(pd), headless=False, viewport={'width':1920,'height':1080})
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)
        
        await page.goto('https://www.linkedin.com/mynetwork/invite-connect/connections/', wait_until='load', timeout=30000)
        await asyncio.sleep(3)
        
        url = page.url
        title = await page.title()
        
        print(f"URL: {url}")
        print(f"Title: {title}")
        print()
        
        has_login = '/login' in url
        has_checkpoint = '/checkpoint' in url
        has_mynetwork = '/mynetwork' in url
        
        print(f"Has /login: {has_login}")
        print(f"Has /checkpoint: {has_checkpoint}")
        print(f"Has /mynetwork: {has_mynetwork}")
        print()
        
        nav_count = await page.locator('nav').count()
        header_count = await page.locator('header[role="banner"]').count()
        
        print(f"nav count: {nav_count}")
        print(f"header count: {header_count}")
        print()
        
        if has_mynetwork:
            print("✅ Should be considered logged in!")
        else:
            print("❌ Would fail login check")
        
        await ctx.close()

asyncio.run(debug_check())
