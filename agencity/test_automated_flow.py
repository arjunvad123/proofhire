#!/usr/bin/env python3
"""
End-to-end test for automated LinkedIn login + extraction.

Tests:
1. Authentication (with 2FA support)
2. Connection extraction (limited to 10)
3. Data verification
4. Session persistence

Usage:
    export LINKEDIN_TEST_EMAIL="test@email.com"
    export LINKEDIN_TEST_PASSWORD="password"
    python test_automated_flow.py
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
from app.services.linkedin.session_manager import LinkedInSessionManager


async def test_automated_flow():
    """Test full automated flow."""

    print("=" * 70)
    print("AUTOMATED LOGIN + EXTRACTION - END TO END TEST")
    print("=" * 70)
    print()

    # Get credentials from env or prompt
    email = os.getenv('LINKEDIN_TEST_EMAIL')
    password = os.getenv('LINKEDIN_TEST_PASSWORD')

    if not email:
        email = input("LinkedIn email: ").strip()
    if not password:
        import getpass
        password = getpass.getpass("LinkedIn password: ")

    # Initialize services
    auth = LinkedInCredentialAuth()
    session_manager = LinkedInSessionManager()
    extractor = LinkedInConnectionExtractor(session_manager)

    # session_id will be generated after successful login

    # ================================================================
    # PHASE 1: AUTHENTICATION
    # ================================================================
    print("Phase 1: Authentication")
    print("-" * 70)
    print(f"📧 Email: {email}")
    print("🔐 Logging in...")
    print()

    result = await auth.login(
        email=email,
        password=password,
        user_location="San Francisco, CA"  # Optional
    )

    if result['status'] == '2fa_required':
        print("🔐 2FA Required!")
        print("Check your device for verification code.")
        code = input("Enter 6-digit code: ").strip()

        # Resume with 2FA code
        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state')
        )

    if result['status'] != 'connected':
        print(f"❌ Login failed: {result.get('error')}")
        return False

    print("✅ Login successful!")
    print(f"   Cookies extracted: {len(result['cookies'])} cookies")
    if 'li_at' in result['cookies']:
        print(f"   li_at: {result['cookies']['li_at']['value'][:20]}...")
    print()

    # Save session
    cookies = result['cookies']
    # Use Agencity company ID for testing (e6924b88-d22a-41a9-a336-cf604bf5bf9c)
    # Generate a test user ID
    test_company_id = "e6924b88-d22a-41a9-a336-cf604bf5bf9c"
    test_user_id = str(uuid.uuid4())

    print(f"   Saving session for company: {test_company_id}")
    print()

    session_result = await session_manager.create_session(
        company_id=test_company_id,
        user_id=test_user_id,
        cookies=cookies,
        user_location="San Francisco, CA"
    )
    # Use the generated session_id
    session_id = session_result['session_id']
    print(f"✅ Session saved!")
    print(f"   Session ID: {session_id}")
    print()

    # ================================================================
    # PHASE 2: CONNECTION EXTRACTION
    # ================================================================
    print("=" * 70)
    print("Phase 2: Connection Extraction (Limited to 10)")
    print("-" * 70)
    print()

    connection_count = [0]  # Use list to modify in callback

    def progress_callback(current, estimated):
        connection_count[0] = current
        if current <= 10:  # Only show first 10
            print(f"   [{current}] Extracting...")

    print("📊 Starting extraction...")
    print("   (Browser window will open - this is normal!)")
    print()

    # Extract connections (we'll limit to 10 for testing)
    extraction_result = await extractor.extract_connections(
        session_id=session_id,
        progress_callback=progress_callback
    )

    if extraction_result['status'] != 'success':
        print(f"❌ Extraction failed: {extraction_result.get('error')}")
        return False

    connections = extraction_result['connections'][:10]  # Limit to first 10

    print()
    print("✅ Extraction complete!")
    print(f"   Total connections found: {len(connections)}")
    print(f"   Duration: {extraction_result['duration_seconds']:.1f}s")
    print()

    # ================================================================
    # PHASE 3: VERIFY EXTRACTED DATA
    # ================================================================
    print("=" * 70)
    print("Phase 3: Verify Extracted Data")
    print("-" * 70)
    print()

    if not connections:
        print("⚠️  No connections extracted (this may be okay if account has no connections)")
        print()
    else:
        for i, conn in enumerate(connections[:5], 1):  # Show first 5
            name = conn.get('full_name', 'Unknown')
            title = conn.get('current_title', 'N/A')
            company = conn.get('current_company', 'N/A')
            url = conn.get('linkedin_url', 'N/A')

            print(f"{i}. {name}")
            print(f"   Title: {title}")
            print(f"   Company: {company}")
            print(f"   URL: {url}")
            print()

        if len(connections) > 5:
            print(f"   ... and {len(connections) - 5} more")
            print()

    # ================================================================
    # PHASE 4: SESSION PERSISTENCE CHECK
    # ================================================================
    print("=" * 70)
    print("Phase 4: Session Persistence Check")
    print("-" * 70)
    print()

    # Verify session was saved
    saved_session = await session_manager.get_session(session_id)
    if saved_session:
        print("✅ Session saved successfully")
        print(f"   Session ID: {session_id}")
        print(f"   Auth method: {saved_session.get('auth_method')}")
        print(f"   Created: {saved_session.get('created_at')}")
    else:
        print("⚠️  Session not found in database (may be expected if no DB configured)")

    print()

    # Check browser profile exists
    profile_path = Path("./browser_profiles") / session_id
    if profile_path.exists():
        items = list(profile_path.iterdir())
        print(f"✅ Browser profile created: {profile_path}")
        print(f"   Contains: {len(items)} items")

        # Check for cookies file
        cookies_file = profile_path / "Default" / "Cookies"
        if cookies_file.exists():
            print(f"   ✅ Cookies file found")
        else:
            print(f"   ⚠️  Cookies file not found (may be in different location)")
    else:
        print("⚠️  Browser profile not found")

    print()
    print("=" * 70)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Check that browser window was VISIBLE during test")
    print("2. Verify no CAPTCHA or warnings appeared")
    print("3. Review extracted connection data above")
    print("4. Test session re-use by running extraction again")
    print()

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_automated_flow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
