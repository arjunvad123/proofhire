#!/usr/bin/env python3
"""
ONE-TIME setup script: authenticate with LinkedIn and cache cookies for tests.

Run this once from the agencity/ directory:
    python scripts/save_test_auth.py

What this does:
  1. Opens a persistent browser profile keyed to the EMAIL (hashed)
  2. Logs in with your LinkedIn credentials
  3. Saves the cookies to .linkedin_cache_{email_hash}.json

IMPORTANT: Each LinkedIn account gets its own isolated browser profile.
This prevents cookie pollution between accounts.

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
from app.services.linkedin.account_manager import AccountManager


def get_cache_path(email: str) -> Path:
    """Get the cache file path for a specific account."""
    profile_id = AccountManager.get_profile_id(email)
    return Path(f".linkedin_cache_{profile_id}.json")


# Legacy cache path for backwards compatibility
LEGACY_CACHE_PATH = Path(".linkedin_test_cache.json")


async def main() -> None:
    email = os.getenv("LINKEDIN_TEST_EMAIL", "").strip()
    password = os.getenv("LINKEDIN_TEST_PASSWORD", "").strip()

    if not email:
        email = input("LinkedIn account email: ").strip()
    if not password:
        password = input("LinkedIn account password: ").strip()

    if not email or not password:
        print("❌ Email and password are required.")
        sys.exit(1)

    # Get account-specific profile ID and cache path
    profile_id = AccountManager.get_profile_id(email)
    cache_path = get_cache_path(email)

    print()
    print("=" * 70)
    print("LinkedIn Auth Cache — ONE-TIME SETUP")
    print("=" * 70)
    print(f"  Account    : {email}")
    print(f"  Profile ID : {profile_id}  (isolated browser profile)")
    print(f"  Cache file : {cache_path}")
    print()
    print("⚠️  LinkedIn will send ONE sign-in email for this first login.")
    print("   After this, the profile is trusted and no more emails will arrive.")
    print()

    auth = LinkedInCredentialAuth()

    print("🔐 Logging in...")
    print()
    print("📌 A browser window will open. If LinkedIn shows a security checkpoint:")
    print("   1. Complete the CAPTCHA or email/SMS verification in the browser")
    print("   2. The script will automatically detect when you're logged in")
    print("   3. Wait up to 5 minutes to complete verification")
    print()

    # Note: email is used to derive the profile ID automatically
    result = await auth.login(
        email=email,
        password=password,
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

    if result["status"] == "checkpoint_required":
        print(f"\n⚠️  {result.get('message', 'Checkpoint timeout')}")
        print("   The browser closed before you completed verification.")
        print("   Run this script again and complete the checkpoint faster.")
        sys.exit(1)
    elif result["status"] != "connected":
        print(f"\n❌ Login failed: {result.get('error', 'unknown error')}")
        sys.exit(1)

    cookies = result["cookies"]

    # Persist cookies to the account-specific cache file
    cache_path.write_text(json.dumps(cookies, indent=2))

    # Also write to legacy path for backwards compatibility
    LEGACY_CACHE_PATH.write_text(json.dumps(cookies, indent=2))

    print()
    print("✅ Success! Cookies cached.")
    print(f"   Cache file : {cache_path.resolve()}")
    print(f"   Legacy file: {LEGACY_CACHE_PATH.resolve()}")
    print(f"   Cookies    : {', '.join(cookies.keys())}")
    print()
    print("You can now run tests without triggering any login emails:")
    print(f"   python test_extraction_cached.py --email {email}")
    print("   pytest tests/")
    print()


if __name__ == "__main__":
    asyncio.run(main())
