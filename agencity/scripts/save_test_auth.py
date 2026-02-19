#!/usr/bin/env python3
"""
ONE-TIME setup script: authenticate with LinkedIn and cache cookies for tests.

Run this once from the agencity/ directory:
    python scripts/save_test_auth.py

What this does:
  1. Opens a persistent browser profile keyed to "test_account"
  2. Logs in with your test LinkedIn credentials
  3. Saves the cookies to .linkedin_test_cache.json

After this runs:
  - LinkedIn will have sent exactly ONE sign-in email (the first-time device trust)
  - All subsequent test runs load from the cache → no login → no emails
  - The cache is valid for ~1 year (li_at cookie lifespan). Re-run when it expires.

Environment variables (optional — falls back to prompts):
    LINKEDIN_TEST_EMAIL     LinkedIn test account email
    LINKEDIN_TEST_PASSWORD  LinkedIn test account password
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Allow running from the agencity/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth

CACHE_PATH = Path(".linkedin_test_cache.json")
TEST_USER_ID = "test_account"  # stable ID → stable persistent browser profile


async def main() -> None:
    email = os.getenv("LINKEDIN_TEST_EMAIL", "").strip()
    password = os.getenv("LINKEDIN_TEST_PASSWORD", "").strip()

    if not email:
        email = input("LinkedIn test account email: ").strip()
    if not password:
        password = input("LinkedIn test account password: ").strip()

    if not email or not password:
        print("❌ Email and password are required.")
        sys.exit(1)

    print()
    print("=" * 70)
    print("LinkedIn Test Auth Cache — ONE-TIME SETUP")
    print("=" * 70)
    print(f"  Account : {email}")
    print(f"  Profile : auth_{TEST_USER_ID}  (persistent browser profile)")
    print()
    print("⚠️  LinkedIn will send ONE sign-in email for this first login.")
    print("   After this, the profile is trusted and no more emails will arrive.")
    print()

    auth = LinkedInCredentialAuth()

    print("🔐 Logging in...")
    result = await auth.login(
        email=email,
        password=password,
        user_id=TEST_USER_ID,
    )

    # Handle 2FA
    if result["status"] == "2fa_required":
        print()
        print("🔐 2FA required — check your email or authenticator app.")
        code = input("Enter the 6-digit verification code: ").strip()

        result = await auth.login(
            email=email,
            password=password,
            user_id=TEST_USER_ID,
            verification_code=code,
            resume_state=result["verification_state"],
        )

    if result["status"] != "connected":
        print(f"\n❌ Login failed: {result.get('error', 'unknown error')}")
        sys.exit(1)

    cookies = result["cookies"]

    # Persist cookies to the cache file
    CACHE_PATH.write_text(json.dumps(cookies, indent=2))

    print()
    print("✅ Success! Cookies cached.")
    print(f"   Cache file : {CACHE_PATH.resolve()}")
    print(f"   Cookies    : {', '.join(cookies.keys())}")
    print()
    print("You can now run tests without triggering any login emails:")
    print("   python test_auth_only.py")
    print("   pytest tests/")
    print()


if __name__ == "__main__":
    asyncio.run(main())
