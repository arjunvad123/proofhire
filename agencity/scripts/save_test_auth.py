#!/usr/bin/env python3
"""
LinkedIn Profile Warming Script

This script authenticates with LinkedIn and "warms" the browser profile so
subsequent automation runs without CAPTCHA or verification.

Usage:
    # Local testing (saves cookies to local JSON file)
    python scripts/save_test_auth.py --email="you@example.com"

    # Production (saves to Supabase via API)
    python scripts/save_test_auth.py --email="you@example.com" --session-id="abc123"

What this does:
  1. Opens a persistent browser profile keyed to the EMAIL (hashed)
  2. Logs in with your LinkedIn credentials
  3. Waits for you to complete any CAPTCHA/verification
  4. Saves cookies to local file OR Supabase (if --session-id provided)

After warming:
  - The browser profile is "trusted" by LinkedIn
  - Subsequent automation runs won't trigger verification
  - Profile stays valid for ~1 year (li_at cookie lifespan)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import click
import httpx

# Allow running from the agencity/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.account_manager import AccountManager


def get_cache_path(email: str) -> Path:
    """Get the cache file path for a specific account."""
    profile_id = AccountManager.get_profile_id(email)
    return Path(f".linkedin_cache_{profile_id}.json")


def print_header():
    """Print the script header."""
    print()
    print("=" * 60)
    print("  LinkedIn Profile Warming")
    print("=" * 60)
    print()


def print_step(step: int, total: int, message: str):
    """Print a step in the process."""
    print(f"[{step}/{total}] {message}")


@click.command()
@click.option("--email", prompt="LinkedIn email", help="LinkedIn account email")
@click.option("--password", default=None, help="LinkedIn password (will prompt if not provided)")
@click.option("--session-id", default=None, help="Link to existing session in Supabase")
@click.option("--api-url", default="http://localhost:8000", help="API base URL")
def main(email: str, password: str, session_id: str, api_url: str):
    """Warm a LinkedIn browser profile for automation."""
    asyncio.run(run_warming(email, password, session_id, api_url))


async def run_warming(email: str, password: str, session_id: str, api_url: str):
    """Main warming logic."""
    # Get password if not provided
    if not password:
        password = os.getenv("LINKEDIN_TEST_PASSWORD", "").strip()
    if not password:
        import getpass
        password = getpass.getpass("LinkedIn password: ")

    if not email or not password:
        print("Error: Email and password are required.")
        sys.exit(1)

    # Get account-specific profile ID and cache path
    profile_id = AccountManager.get_profile_id(email)
    cache_path = get_cache_path(email)

    print_header()
    print(f"  Account    : {email}")
    print(f"  Profile ID : {profile_id}")
    if session_id:
        print(f"  Session ID : {session_id}")
        print(f"  API URL    : {api_url}")
    else:
        print(f"  Cache file : {cache_path}")
    print()

    # Initialize auth
    auth = LinkedInCredentialAuth()
    total_steps = 3

    # Step 1: Open browser and login
    print_step(1, total_steps, "Opening browser for LinkedIn login...")
    print()
    print("    A Chrome window will open.")
    print("    Enter your password if prompted.")
    print("    Complete any CAPTCHA or verification shown.")
    print("    Wait up to 5 minutes to complete verification.")
    print()

    result = await auth.login(
        email=email,
        password=password,
    )

    # Handle 2FA if required
    if result["status"] == "2fa_required":
        print()
        print("    2FA required - check your email or authenticator app.")
        code = input("    Enter the 6-digit verification code: ").strip()

        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result["verification_state"],
        )

    # Handle checkpoint timeout
    if result["status"] == "checkpoint_required":
        print()
        print(f"    {result.get('message', 'Checkpoint timeout')}")
        print("    The browser closed before verification completed.")
        print("    Run this script again and complete the checkpoint faster.")
        sys.exit(1)

    # Handle failure
    if result["status"] != "connected":
        print()
        print(f"    Login failed: {result.get('error', 'unknown error')}")
        sys.exit(1)

    cookies = result["cookies"]

    # Step 2: Show login success
    print_step(2, total_steps, "Waiting for login...")
    print()
    print("    Status: Logged in successfully!")
    print(f"    Cookies: {', '.join(cookies.keys())}")
    print()

    # Step 3: Save to appropriate destination
    if session_id:
        print_step(3, total_steps, "Saving to Agencity...")
        await save_to_supabase(api_url, session_id, cookies, profile_id)
    else:
        print_step(3, total_steps, "Saving to local cache...")
        save_to_local(cache_path, cookies)

    print()
    print("=" * 60)
    print("  Done! Profile warmed successfully.")
    print("=" * 60)
    print()

    if session_id:
        print("You can now close this window and return to the web app.")
    else:
        print("You can now run tests without triggering login emails:")
        print(f"   python test_extraction_cached.py --email {email}")
        print("   pytest tests/")
    print()


async def save_to_supabase(api_url: str, session_id: str, cookies: dict, profile_id: str):
    """Save warming data to Supabase via API."""
    url = f"{api_url}/api/v1/linkedin/session/{session_id}/warm"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={
                "cookies": cookies,
                "profile_id": profile_id,
            })

            if response.status_code == 200:
                print()
                print("    Saved to Agencity successfully!")
            elif response.status_code == 404:
                print()
                print(f"    Error: Session '{session_id}' not found.")
                print("    Make sure the session ID is correct.")
                sys.exit(1)
            else:
                print()
                print(f"    Error: API returned {response.status_code}")
                print(f"    {response.text}")
                sys.exit(1)

    except httpx.ConnectError:
        print()
        print(f"    Error: Could not connect to API at {api_url}")
        print("    Make sure the API server is running.")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"    Error: {e}")
        sys.exit(1)


def save_to_local(cache_path: Path, cookies: dict):
    """Save cookies to local JSON file."""
    cache_path.write_text(json.dumps(cookies, indent=2))
    print()
    print(f"    Saved to {cache_path.resolve()}")

    # Also write to legacy path for backwards compatibility
    legacy_path = Path(".linkedin_test_cache.json")
    legacy_path.write_text(json.dumps(cookies, indent=2))
    print(f"    Saved to {legacy_path.resolve()} (legacy)")


if __name__ == "__main__":
    main()
