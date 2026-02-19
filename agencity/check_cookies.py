#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.linkedin.session_manager import LinkedInSessionManager

async def check():
    sm = LinkedInSessionManager()
    cookies = await sm.get_session_cookies(sys.argv[1])
    
    if cookies:
        print(f"✅ Cookies found: {len(cookies)} cookies")
        print(f"   Has li_at: {'li_at' in cookies}")
        if 'li_at' in cookies:
            print(f"   li_at value: {cookies['li_at']['value'][:30]}...")
    else:
        print("❌ No cookies found!")

asyncio.run(check())
