#!/usr/bin/env python3
"""
End-to-end test for LinkedIn connection extraction.

Tests the full flow:
1. Authenticate (or reuse session) inside the SAME persistent browser profile
2. Create extraction job in database
3. Run extraction with pagination
4. Store connections in database
5. Verify data was stored correctly

Key insight: Authentication and extraction MUST use the same persistent
browser profile. LinkedIn ties session cookies to browser fingerprint/profile,
so cookies obtained in one profile won't work in another.

Usage:
    python test_extraction_e2e.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

# Test configuration
TEST_COMPANY_ID = "100b5ac1-1912-4970-a378-04d0169fd597"  # Confido test company


async def main():
    # Enable detailed logging so we can see navigation steps
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    print("=" * 60)
    print("LinkedIn Extraction E2E Test")
    print("=" * 60)

    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
        return

    supabase = create_client(supabase_url, supabase_key)
    print(f"✓ Connected to Supabase")

    # Step 1: Authenticate and get session
    print("\n--- Step 1: Authenticate ---")
    session, cookies = await authenticate_and_get_session(supabase)
    if not session or not cookies:
        print("ERROR: Authentication failed")
        return

    session_id = session['id']
    print(f"✓ Session ID: {session_id}")
    print(f"  Status: {session['status']}")
    print(f"  Cookies: {len(cookies)}")

    # Step 2: Create extraction job
    print("\n--- Step 2: Create Extraction Job ---")
    job = create_extraction_job(supabase, session_id)
    if not job:
        print("ERROR: Failed to create extraction job")
        return

    job_id = job['id']
    print(f"✓ Job ID: {job_id}")
    print(f"  Status: {job['status']}")

    # Step 3: Run extraction
    print("\n--- Step 3: Run Extraction ---")
    print("Starting extraction (this will take a while - slow and methodical)...")
    print("Watch for progress updates below:\n")

    from app.services.linkedin.extraction_task import run_connection_extraction

    # Disable proxy for local testing — cookies were obtained from local IP
    await run_connection_extraction(job_id, session_id, supabase, use_proxy=False)

    # Step 4: Check results
    print("\n--- Step 4: Verify Results ---")

    # Get updated job status
    job_result = supabase.table('connection_extraction_jobs')\
        .select('*')\
        .eq('id', job_id)\
        .execute()

    if job_result.data:
        job = job_result.data[0]
        print(f"Job Status: {job['status']}")
        print(f"Connections Found: {job.get('connections_found', 0)}")
        if job.get('error_message'):
            print(f"Error: {job['error_message']}")
        if job.get('completed_at'):
            print(f"Completed At: {job['completed_at']}")

    # Get stored connections
    connections_result = supabase.table('linkedin_connections')\
        .select('id, full_name, current_title, current_company, linkedin_url')\
        .eq('company_id', TEST_COMPANY_ID)\
        .order('created_at', desc=True)\
        .limit(10)\
        .execute()

    if connections_result.data:
        print(f"\n✓ {len(connections_result.data)} connections stored (showing first 10):")
        for conn in connections_result.data:
            name = conn.get('full_name', 'Unknown')
            title = conn.get('current_title', '')
            company = conn.get('current_company', '')
            print(f"  - {name}")
            if title or company:
                print(f"    {title} @ {company}")
    else:
        print("No connections stored in database")

    # Get total count
    count_result = supabase.table('linkedin_connections')\
        .select('id', count='exact')\
        .eq('company_id', TEST_COMPANY_ID)\
        .execute()

    total = count_result.count or 0
    print(f"\nTotal connections in database for company: {total}")

    print("\n" + "=" * 60)
    print("E2E Test Complete")
    print("=" * 60)


async def authenticate_and_get_session(supabase):
    """
    Authenticate using credential_auth (which uses its own persistent browser
    profile keyed to the email), then store cookies in the session.

    The extraction step will also use a persistent profile keyed to the
    session_id. To ensure cookies work, we authenticate fresh and store them
    in the database — the extractor will inject them into its profile.

    Returns:
        (session_dict, cookies_dict) or (None, None) on failure
    """
    from app.services.linkedin.credential_auth import LinkedInCredentialAuth
    from app.services.linkedin.session_manager import LinkedInSessionManager
    from app.services.linkedin.account_manager import AccountManager

    email = os.getenv("LINKEDIN_TEST_EMAIL")
    password = os.getenv("LINKEDIN_TEST_PASSWORD")

    if not email or not password:
        print("ERROR: LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD required in .env")
        return None, None

    # Get the browser profile ID for this email — extraction must use the same one
    profile_id = AccountManager.get_profile_id(email)
    print(f"Browser profile ID: {profile_id}")

    # Authenticate — this uses a persistent profile keyed to the email hash
    print(f"Authenticating as {email}...")
    auth = LinkedInCredentialAuth()
    result = await auth.login(
        email=email,
        password=password,
        user_id=email
    )

    if result["status"] == "2fa_required":
        print("\n2FA required - check your email or authenticator")
        code = input("Enter 6-digit code: ").strip()
        result = await auth.login(
            email=email,
            password=password,
            user_id=email,
            verification_code=code,
            resume_state=result["verification_state"]
        )

    if result["status"] != "connected":
        print(f"ERROR: Auth failed: {result.get('error')}")
        return None, None

    cookies = result["cookies"]
    print(f"✓ Authenticated — {len(cookies)} cookies extracted")

    # Get or create session in database
    session_manager = LinkedInSessionManager(supabase)

    existing = supabase.table('linkedin_sessions')\
        .select('*')\
        .eq('company_id', TEST_COMPANY_ID)\
        .eq('status', 'active')\
        .execute()

    if existing.data:
        session = existing.data[0]
        print(f"Found existing session: {session['id']}")
        await session_manager.refresh_session(session['id'], cookies)

        # Ensure profile_id is stored so extraction uses the right browser profile
        if session.get('profile_id') != profile_id:
            supabase.table('linkedin_sessions').update({
                'profile_id': profile_id
            }).eq('id', session['id']).execute()
            session['profile_id'] = profile_id
            print(f"Updated session profile_id: {profile_id}")

        print("Refreshed session with latest cookies")
        return session, cookies

    # Create new session
    print("Creating new session...")
    import uuid
    test_user_id = str(uuid.uuid4())

    create_result = await session_manager.create_session(
        company_id=TEST_COMPANY_ID,
        user_id=test_user_id,
        cookies=cookies,
        user_timezone="America/Los_Angeles",
        user_location="San Francisco, CA"
    )

    session_result = supabase.table('linkedin_sessions')\
        .select('*')\
        .eq('id', create_result['session_id'])\
        .execute()

    session = session_result.data[0] if session_result.data else None
    return session, cookies


def create_extraction_job(supabase, session_id: str) -> dict:
    """Create a new extraction job."""
    result = supabase.table('connection_extraction_jobs').insert({
        'session_id': session_id,
        'status': 'pending',
        'connections_found': 0
    }).execute()

    return result.data[0] if result.data else None


if __name__ == "__main__":
    asyncio.run(main())
