#!/usr/bin/env python3
"""Save a test LinkedIn session to Supabase for testing."""

import asyncio
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.session_manager import LinkedInSessionManager


async def save_session():
    """Authenticate and save session to Supabase."""
    email = os.environ.get('LINKEDIN_TEST_EMAIL')
    password = os.environ.get('LINKEDIN_TEST_PASSWORD')
    user_id = os.environ.get('TEST_USER_ID', str(uuid.uuid4()))

    if not email or not password:
        print("❌ Set LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD")
        return

    print("Authenticating...")
    auth = LinkedInCredentialAuth()
    result = await auth.login(email=email, password=password)

    if result['status'] != 'connected':
        print(f"❌ Login failed: {result.get('error')}")
        return

    cookies = result['cookies']
    print(f"✅ Authenticated - {len(cookies)} cookies")

    # Save to Supabase
    print("\nSaving session to Supabase...")
    mgr = LinkedInSessionManager()
    result = await mgr.create_session(
        company_id=user_id,  # Using user_id as company_id for testing
        user_id=user_id,
        cookies=cookies
    )
    session_id = result['session_id']

    print(f"✅ Session saved!")
    print(f"\nSession ID: {session_id}")
    print(f"\nAdd this to your .env file:")
    print(f"LINKEDIN_SESSION_ID={session_id}")

    return session_id


if __name__ == '__main__':
    asyncio.run(save_session())
