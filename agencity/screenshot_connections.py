#!/usr/bin/env python3
"""
Take a screenshot of the connections page to see what's actually displayed.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def screenshot_page(session_id: str):
    """Screenshot the connections page."""

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

        print("Waiting for page to load...")
        await asyncio.sleep(10)

        # Take screenshot
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f'linkedin_connections_{timestamp}.png'

        await page.screenshot(path=screenshot_path, full_page=True)

        print(f"✅ Screenshot saved: {screenshot_path}")
        print()

        # Get page title and URL
        title = await page.title()
        url = page.url

        print(f"Page title: {title}")
        print(f"Current URL: {url}")
        print()

        # Check for common messages
        messages_to_check = [
            "You don't have any connections yet",
            "Start connecting",
            "verification",
            "unusual activity",
            "Let's secure your account",
            "restricted"
        ]

        page_text = await page.evaluate('() => document.body.innerText')

        print("Checking for specific messages:")
        for msg in messages_to_check:
            if msg.lower() in page_text.lower():
                print(f"  ⚠️  Found: '{msg}'")

        print()
        print("=" * 70)
        print(f"Please check the screenshot: {screenshot_path}")
        print("=" * 70)

        await context.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python screenshot_connections.py <session_id>")
        sys.exit(1)

    session_id = sys.argv[1]
    asyncio.run(screenshot_page(session_id))
