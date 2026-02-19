#!/usr/bin/env python3
"""
Quick test for LinkedIn authentication and session storage only.
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.session_manager import LinkedInSessionManager


async def test_auth():
    """Test authentication and session storage."""

    print("=" * 70)
    print("LINKEDIN AUTHENTICATION & SESSION STORAGE TEST")
    print("=" * 70)
    print()

    # Get credentials
    email = os.getenv('LINKEDIN_TEST_EMAIL', 'acn002@ucsd.edu')
    password = os.getenv('LINKEDIN_TEST_PASSWORD', '^5>r9p94Wy+zuu;')

    # Initialize services
    auth = LinkedInCredentialAuth()
    session_manager = LinkedInSessionManager()

    # Step 1: Login
    print("Step 1: Authenticating...")
    print(f"   Email: {email}")
    result = await auth.login(email=email, password=password)

    if result['status'] != 'connected':
        print(f"❌ Login failed: {result.get('error')}")
        return False

    print("✅ Login successful!")
    print(f"   Cookies: {len(result['cookies'])} cookies")
    print(f"   li_at: {result['cookies']['li_at']['value'][:30]}...")
    print()

    # Step 2: Save session
    print("Step 2: Saving session to database...")
    test_company_id = "e6924b88-d22a-41a9-a336-cf604bf5bf9c"  # Agencity
    test_user_id = str(uuid.uuid4())

    session_result = await session_manager.create_session(
        company_id=test_company_id,
        user_id=test_user_id,
        cookies=result['cookies'],
        user_location="San Francisco, CA"
    )

    session_id = session_result['session_id']
    print("✅ Session saved!")
    print(f"   Session ID: {session_id}")
    print(f"   Expires: {session_result['expires_at']}")
    print()

    # Step 3: Retrieve session
    print("Step 3: Retrieving session from database...")
    saved_session = await session_manager.get_session(session_id)

    if not saved_session:
        print("❌ Session not found!")
        return False

    print("✅ Session retrieved!")
    print(f"   Status: {saved_session['status']}")
    print(f"   Health: {saved_session['health']}")
    print()

    # Step 4: Retrieve cookies
    print("Step 4: Retrieving decrypted cookies...")
    cookies = await session_manager.get_session_cookies(session_id)

    if not cookies or 'li_at' not in cookies:
        print("❌ Cookies not found or invalid!")
        return False

    print("✅ Cookies retrieved and decrypted!")
    print(f"   li_at: {cookies['li_at']['value'][:30]}...")
    print()

    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  • Authentication: Working ✅")
    print(f"  • Session storage: Working ✅")
    print(f"  • Cookie encryption: Working ✅")
    print(f"  • Session retrieval: Working ✅")
    print()
    print(f"Session ID: {session_id}")
    print("You can now use this session for connection extraction!")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_auth())
    sys.exit(0 if success else 1)
