#!/usr/bin/env python3
"""
End-to-end test for LinkedIn connection extraction.

Tests the full flow:
1. Load cached cookies (or authenticate if needed)
2. Create extraction job in database
3. Run extraction with pagination
4. Store connections in database
5. Verify data was stored correctly

If cookies are stale, will re-authenticate using the credentials
from environment variables.

Usage:
    python test_extraction_e2e.py
"""

import asyncio
import json
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
COOKIE_CACHE_FILE = ".linkedin_test_cache.json"
TEST_USER_ID = "test_account"


async def main():
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

    # Step 1: Get valid cookies (refresh if needed)
    print("\n--- Step 1: Validate/Refresh Cookies ---")
    cookies = await refresh_cookies_if_needed()
    if not cookies:
        print("ERROR: Could not get valid cookies")
        return

    print(f"✓ Have {len(cookies)} valid cookies")

    # Step 2: Create or get test session
    print("\n--- Step 2: Get/Create Session ---")
    session = await get_or_create_session(supabase, cookies)
    if not session:
        print("ERROR: Failed to create session")
        return

    session_id = session['id']
    print(f"✓ Session ID: {session_id}")
    print(f"  Status: {session['status']}")
    print(f"  Health: {session['health']}")

    # Step 3: Create extraction job
    print("\n--- Step 3: Create Extraction Job ---")
    job = create_extraction_job(supabase, session_id)
    if not job:
        print("ERROR: Failed to create extraction job")
        return

    job_id = job['id']
    print(f"✓ Job ID: {job_id}")
    print(f"  Status: {job['status']}")

    # Step 4: Run extraction
    print("\n--- Step 4: Run Extraction ---")
    print("Starting extraction (this will take a while - slow and methodical)...")
    print("Watch for progress updates below:\n")

    from app.services.linkedin.extraction_task import run_connection_extraction

    await run_connection_extraction(job_id, session_id, supabase)

    # Step 5: Check results
    print("\n--- Step 5: Verify Results ---")

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
            url = conn.get('linkedin_url', '')
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


def load_cached_cookies() -> dict:
    """Load cookies from cache file."""
    cache_path = Path(COOKIE_CACHE_FILE)
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)
            # Handle both formats: direct cookies or wrapped in 'cookies' key
            if 'cookies' in data:
                return data['cookies']
            elif 'li_at' in data:
                # Direct cookie format from save_test_auth.py
                return data
            return None
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None


def save_cookies_to_cache(cookies: dict) -> None:
    """Save fresh cookies to cache file."""
    cache_path = Path(COOKIE_CACHE_FILE)
    with open(cache_path, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"✓ Updated cookie cache: {cache_path}")


async def refresh_cookies_if_needed() -> dict:
    """
    Check if cookies are valid by testing navigation.
    If stale, re-authenticate and return fresh cookies.
    """
    from app.services.linkedin.stealth_browser import StealthBrowser
    from app.services.linkedin.credential_auth import LinkedInCredentialAuth

    cookies = load_cached_cookies()
    if not cookies:
        print("No cached cookies - need fresh authentication")
        return await do_fresh_auth()

    # Convert to cookie list for Playwright
    cookie_list = []
    for name, data in cookies.items():
        cookie = {
            "name": name,
            "value": data["value"],
            "domain": data.get("domain", ".linkedin.com"),
            "path": data.get("path", "/"),
            "secure": data.get("secure", True),
            "httpOnly": data.get("httpOnly", False),
        }
        if data.get("expirationDate"):
            cookie["expires"] = data["expirationDate"]
        cookie_list.append(cookie)

    # Test the cookies by navigating to feed
    print("Testing cookie validity...")
    cookies_valid = False

    async with StealthBrowser.launch_persistent(
        session_id=f"auth_{TEST_USER_ID}",
        headless=False
    ) as sb:
        await sb.context.add_cookies(cookie_list)
        page = await sb.new_page()

        await page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
        await asyncio.sleep(2)

        current_url = page.url
        if "/login" not in current_url and "/checkpoint" not in current_url:
            print("✓ Cookies are valid")
            cookies_valid = True

    # Browser is now closed - safe to re-auth if needed
    if cookies_valid:
        return cookies

    print("⚠️ Cookies are stale - re-authenticating...")
    return await do_fresh_auth()


async def do_fresh_auth() -> dict:
    """Perform fresh authentication."""
    from app.services.linkedin.credential_auth import LinkedInCredentialAuth

    email = os.getenv("LINKEDIN_TEST_EMAIL")
    password = os.getenv("LINKEDIN_TEST_PASSWORD")

    if not email or not password:
        print("ERROR: LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD required in .env")
        return None

    print(f"Authenticating as {email}...")
    auth = LinkedInCredentialAuth()
    result = await auth.login(
        email=email,
        password=password,
        user_id=TEST_USER_ID
    )

    if result["status"] == "2fa_required":
        print("\n🔐 2FA required - check your email or authenticator")
        code = input("Enter 6-digit code: ").strip()
        result = await auth.login(
            email=email,
            password=password,
            user_id=TEST_USER_ID,
            verification_code=code,
            resume_state=result["verification_state"]
        )

    if result["status"] == "connected":
        cookies = result["cookies"]
        save_cookies_to_cache(cookies)
        return cookies

    print(f"ERROR: Auth failed: {result.get('error')}")
    return None


async def get_or_create_session(supabase, cookies: dict) -> dict:
    """Get existing session or create new one."""
    from app.services.linkedin.session_manager import LinkedInSessionManager

    session_manager = LinkedInSessionManager(supabase)

    # Check for existing session
    existing = supabase.table('linkedin_sessions')\
        .select('*')\
        .eq('company_id', TEST_COMPANY_ID)\
        .eq('status', 'active')\
        .execute()

    if existing.data:
        session = existing.data[0]
        print(f"Found existing session: {session['id']}")

        # Update cookies
        await session_manager.refresh_session(session['id'], cookies)
        print("Refreshed session with latest cookies")

        return session

    # Create new session
    print("Creating new session...")

    # Generate a test user_id
    import uuid
    test_user_id = str(uuid.uuid4())

    result = await session_manager.create_session(
        company_id=TEST_COMPANY_ID,
        user_id=test_user_id,
        cookies=cookies,
        user_timezone="America/Los_Angeles",
        user_location="San Francisco, CA"
    )

    # Get the created session
    session_result = supabase.table('linkedin_sessions')\
        .select('*')\
        .eq('id', result['session_id'])\
        .execute()

    return session_result.data[0] if session_result.data else None


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
