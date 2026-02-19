#!/usr/bin/env python3
import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.linkedin.session_manager import LinkedInSessionManager
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor

async def test():
    sm = LinkedInSessionManager()
    ext = LinkedInConnectionExtractor(sm)
    
    print("Testing connection extraction with updated selectors...")
    print()
    
    result = await ext.extract_connections(
        session_id=sys.argv[1],
        progress_callback=lambda c, e: print(f"  Progress: {c} connections found")
    )
    
    print()
    print("=" * 70)
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Total connections: {result['total']}")
        print(f"Duration: {result['duration_seconds']:.1f}s")
        print()
        print("Connections extracted:")
        for i, conn in enumerate(result['connections'][:5], 1):
            print(f"{i}. {conn['full_name']}")
            print(f"   {conn['headline']}")
            print(f"   {conn['linkedin_url']}")
            print()
    else:
        print(f"Error: {result.get('error')}")

asyncio.run(test())
