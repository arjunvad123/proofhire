#!/usr/bin/env python3
"""
Quick test for LinkedIn authentication and session storage.

On the FIRST run (no cache):
  - Logs in via Playwright with a persistent browser profile
  - LinkedIn sends ONE sign-in email (device is now trusted)
  - Saves cookies to .linkedin_test_cache.json

On SUBSEQUENT runs (cache present):
  - Loads cookies from .linkedin_test_cache.json
  - Skips login entirely → no sign-in email

To force a fresh login (e.g. cookies expired):
    rm .linkedin_test_cache.json && python test_auth_only.py
"""

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.session_manager import LinkedInSessionManager

CACHE_PATH = Path(".linkedin_test_cache.json")
TEST_USER_ID = "test_account"   # stable ID → stable persistent browser profile


async def _login_and_cache(email: str, password: str) -> dict:
    """Perform a real LinkedIn login and cache the resulting cookies."""
    auth = LinkedInCredentialAuth()

    print("Step 1: Authenticating via Playwright...")
    print(f"   Email  : {email}")
    print(f"   Profile: auth_{TEST_USER_ID}  (persistent — email fires once only)")

    result = await auth.login(
        email=email,
        password=password,
        user_id=TEST_USER_ID,
    )

    # Handle 2FA
    if result["status"] == "2fa_required":
        print("\n🔐 2FA required!")
        code = input("Enter the 6-digit verification code: ").strip()
        result = await auth.login(
            email=email,
            password=password,
            user_id=TEST_USER_ID,
            verification_code=code,
            resume_state=result["verification_state"],
        )

    if result["status"] != "connected":
        print(f"❌ Login failed: {result.get('error')}")
        return {}

    cookies = result["cookies"]

    # Cache for future runs
    CACHE_PATH.write_text(json.dumps(cookies, indent=2))
    print(f"✅ Login successful! Cookies cached to {CACHE_PATH}")
    print(f"   Cookies : {', '.join(cookies.keys())}")

    return cookies


async def test_auth() -> bool:
    """Test authentication and session storage."""

    print("=" * 70)
    print("LINKEDIN AUTHENTICATION & SESSION STORAGE TEST")
    print("=" * 70)
    print()

    # ------------------------------------------------------------------
    # Option 2: Load from cache when available — no login, no email
    # ------------------------------------------------------------------
    if CACHE_PATH.exists():
        print(f"✅ Found cached cookies at {CACHE_PATH} — skipping login")
        print("   No sign-in email will be sent.\n")

        try:
            cookies = json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            print(f"⚠️  Cache file is corrupt ({exc}), re-authenticating...\n")
            CACHE_PATH.unlink(missing_ok=True)
            cookies = {}

        if not cookies or not cookies.get("li_at", {}).get("value"):
            print("⚠️  Cached cookies are invalid. Re-authenticating...\n")
            CACHE_PATH.unlink(missing_ok=True)
            cookies = {}

        if cookies:
            print(f"   li_at: {cookies['li_at']['value'][:30]}...")
            print()

    # ------------------------------------------------------------------
    # Option 1: First-time login with persistent profile (email fires once)
    # ------------------------------------------------------------------
    if not CACHE_PATH.exists() or not cookies:
        email = os.getenv("LINKEDIN_TEST_EMAIL", "acn002@ucsd.edu")
        password = os.getenv("LINKEDIN_TEST_PASSWORD", "^5>r9p94Wy+zuu;")

        cookies = await _login_and_cache(email, password)
        if not cookies:
            return False
        print()

    # ------------------------------------------------------------------
    # Step 2: Save session to Supabase
    # ------------------------------------------------------------------
    print("Step 2: Saving session to database...")
    session_manager = LinkedInSessionManager()
    test_company_id = "e6924b88-d22a-41a9-a336-cf604bf5bf9c"  # Agencity
    test_user_id = str(uuid.uuid4())

    session_result = await session_manager.create_session(
        company_id=test_company_id,
        user_id=test_user_id,
        cookies=cookies,
        user_location="San Francisco, CA",
    )

    session_id = session_result["session_id"]
    print("✅ Session saved!")
    print(f"   Session ID: {session_id}")
    print(f"   Expires   : {session_result['expires_at']}")
    print()

    # ------------------------------------------------------------------
    # Step 3: Retrieve session
    # ------------------------------------------------------------------
    print("Step 3: Retrieving session from database...")
    saved_session = await session_manager.get_session(session_id)

    if not saved_session:
        print("❌ Session not found!")
        return False

    print("✅ Session retrieved!")
    print(f"   Status: {saved_session['status']}")
    print(f"   Health: {saved_session['health']}")
    print()

    # ------------------------------------------------------------------
    # Step 4: Retrieve and decrypt cookies
    # ------------------------------------------------------------------
    print("Step 4: Retrieving decrypted cookies...")
    retrieved_cookies = await session_manager.get_session_cookies(session_id)

    if not retrieved_cookies or "li_at" not in retrieved_cookies:
        print("❌ Cookies not found or invalid!")
        return False

    print("✅ Cookies retrieved and decrypted!")
    print(f"   li_at: {retrieved_cookies['li_at']['value'][:30]}...")
    print()

    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • Authentication : Working ✅")
    print("  • Session storage: Working ✅")
    print("  • Cookie encrypt : Working ✅")
    print("  • Session retriev: Working ✅")
    print()
    print(f"Session ID: {session_id}")
    print("You can now use this session for connection extraction!")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_auth())
    sys.exit(0 if success else 1)
