#!/usr/bin/env python3
"""
Test the updated connection extraction with new LinkedIn DOM selectors.

Uses existing session to avoid 2FA.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.session_manager import LinkedInSessionManager
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor

# Use most recent active session
SESSION_ID = 'f5a79aa5-58c5-4930-ae13-cffefb318d8a'


async def test_extraction():
    print('=' * 70)
    print('TEST: Connection Extraction with New Selectors')
    print('=' * 70)

    print(f'\nUsing session: {SESSION_ID}')

    mgr = LinkedInSessionManager()
    extractor = LinkedInConnectionExtractor(session_manager=mgr)

    # Verify session exists
    session = await mgr.get_session(SESSION_ID)
    if not session:
        print('❌ Session not found')
        return

    print(f'✅ Session found: status={session.get("status")}, health={session.get("health")}')

    # Run extraction
    print('\nStarting extraction...')

    def progress_callback(found, estimated):
        print(f'   Progress: {found} connections found')

    result = await extractor.extract_connections(
        session_id=SESSION_ID,
        progress_callback=progress_callback
    )

    print('\n' + '=' * 70)
    print('EXTRACTION RESULTS')
    print('=' * 70)

    print(f'\nStatus: {result["status"]}')

    if result['status'] == 'success':
        print(f'Total connections: {result["total"]}')
        print(f'Duration: {result["duration_seconds"]:.1f} seconds')

        if result['connections']:
            print('\nExtracted connections:')
            for i, conn in enumerate(result['connections'][:10]):
                print(f'\n  {i+1}. {conn.get("full_name", "Unknown")}')
                print(f'      Title: {conn.get("current_title", "N/A")}')
                print(f'      Company: {conn.get("current_company", "N/A")}')
                print(f'      Headline: {conn.get("headline", "N/A")[:60]}...' if conn.get("headline") and len(conn.get("headline", "")) > 60 else f'      Headline: {conn.get("headline", "N/A")}')
                print(f'      URL: {conn.get("linkedin_url", "N/A")}')

            if result['total'] > 10:
                print(f'\n  ... and {result["total"] - 10} more')

            # Save to file
            with open('extracted_connections.json', 'w') as f:
                json.dump(result['connections'], f, indent=2)
            print(f'\n💾 All connections saved to: extracted_connections.json')
        else:
            print('\n⚠️ No connections extracted (list may be empty)')
    else:
        print(f'Error: {result.get("error", "Unknown error")}')

    print('\n' + '=' * 70)


if __name__ == '__main__':
    asyncio.run(test_extraction())
