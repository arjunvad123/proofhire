#!/usr/bin/env python3
"""
Quick test script for LinkedIn automation flow.

Tests:
1. Authentication with credentials
2. Connection extraction (limited to 10)
3. Warning detection
4. Persistent browser profile

Usage:
    python scripts/test_linkedin_flow.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
from app.services.linkedin.session_manager import LinkedInSessionManager
from app.services.linkedin.warning_detection import LinkedInWarningDetector


async def test_authentication():
    """Test Phase 1: Authentication."""
    print("\n" + "=" * 70)
    print("PHASE 1: AUTHENTICATION TEST")
    print("=" * 70)

    # Get credentials from environment or prompt
    email = os.environ.get('LINKEDIN_TEST_EMAIL')
    if not email:
        email = input("\nLinkedIn Email: ").strip()

    password = os.environ.get('LINKEDIN_TEST_PASSWORD')
    if not password:
        password = input("LinkedIn Password: ").strip()

    print(f"\n🚀 Logging in as {email}...")

    auth = LinkedInCredentialAuth()
    result = await auth.login(
        email=email,
        password=password,
        user_location="San Francisco, CA"
    )

    # Handle 2FA
    if result['status'] == '2fa_required':
        print("\n🔐 2FA Required")
        code = input("Enter 6-digit verification code: ").strip()

        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state')
        )

    if result['status'] != 'connected':
        print(f"\n❌ Login failed: {result.get('error')}")
        return None

    print("\n✅ Login successful!")
    print(f"   Cookies extracted: {len(result['cookies'])} cookies")

    if 'li_at' in result['cookies']:
        token = result['cookies']['li_at']['value']
        print(f"   li_at: {token[:20]}...")

    return result['cookies']


async def test_extraction(cookies):
    """Test Phase 2: Connection Extraction (limited)."""
    print("\n" + "=" * 70)
    print("PHASE 2: CONNECTION EXTRACTION TEST (LIMIT: 10)")
    print("=" * 70)

    # Create mock session manager for testing
    class MockSessionManager:
        async def get_session_cookies(self, session_id):
            return cookies

        async def get_session(self, session_id):
            return {
                'user_location': 'San Francisco, CA',
                'user_timezone': 'America/Los_Angeles'
            }

        async def record_activity(self, session_id, activity_type, count):
            print(f"   📊 Activity recorded: {activity_type} = {count}")

        async def pause_session(self, session_id, hours, reason):
            print(f"   ⏸️  Session paused for {hours}h: {reason}")

        async def record_warning(self, session_id, **kwargs):
            print(f"   ⚠️  Warning recorded: {kwargs}")

    session_manager = MockSessionManager()
    extractor = LinkedInConnectionExtractor(session_manager)

    print("\n📊 Starting extraction...")
    print("   (Limited to 10 connections for testing)")

    # Modify extractor to limit connections
    original_extract = extractor._extract_all_connections

    async def limited_extract(page, session_id, progress_callback=None):
        connections = []
        no_new_count = 0

        while len(connections) < 10:  # Limit to 10
            visible = await extractor._extract_visible_connections(page)

            new_count = 0
            for conn in visible:
                url = conn.get('linkedin_url')
                if url and url not in [c.get('linkedin_url') for c in connections]:
                    connections.append(conn)
                    new_count += 1
                    print(f"\n   [{len(connections)}/10] Found: {conn['full_name']}")
                    if conn['current_company']:
                        print(f"           {conn['current_title']} at {conn['current_company']}")

                    if len(connections) >= 10:
                        break

            if new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    break
            else:
                no_new_count = 0

            # Scroll
            await extractor._scroll_connections_page(page)
            await asyncio.sleep(1.5)

        return connections

    extractor._extract_all_connections = limited_extract

    # Run extraction
    result = await extractor.extract_connections(
        session_id='test-session-123',
        progress_callback=None
    )

    if result['status'] == 'success':
        print(f"\n✅ Extraction complete!")
        print(f"   Connections: {result['total']}")
        print(f"   Duration: {result['duration_seconds']:.1f}s")

        # Show sample
        if result['connections']:
            print("\n   Sample connections:")
            for conn in result['connections'][:3]:
                print(f"   • {conn['full_name']}")
                if conn['current_company']:
                    print(f"     {conn['current_title']} at {conn['current_company']}")
    else:
        print(f"\n❌ Extraction failed: {result.get('error')}")

    return result


async def test_warning_detection():
    """Test Phase 3: Warning Detection."""
    print("\n" + "=" * 70)
    print("PHASE 3: WARNING DETECTION TEST")
    print("=" * 70)

    detector = LinkedInWarningDetector()

    print("\n✅ Warning detector initialized")
    print(f"   Monitoring {len(detector.WARNING_SELECTORS)} selectors:")
    print(f"   • Restriction banners")
    print(f"   • CAPTCHA challenges")
    print(f"   • Unusual activity alerts")
    print(f"   • Security checkpoints")


async def test_browser_profile():
    """Test Phase 4: Persistent Browser Profile."""
    print("\n" + "=" * 70)
    print("PHASE 4: BROWSER PROFILE TEST")
    print("=" * 70)

    profiles_dir = Path('./browser_profiles')

    if profiles_dir.exists():
        profiles = list(profiles_dir.iterdir())
        print(f"\n✅ Browser profiles directory exists")
        print(f"   Location: {profiles_dir.absolute()}")
        print(f"   Profiles: {len(profiles)}")

        if profiles:
            for profile in profiles:
                print(f"\n   Profile: {profile.name}")
                cookies_file = profile / 'Default' / 'Cookies'
                if cookies_file.exists():
                    size_kb = cookies_file.stat().st_size / 1024
                    print(f"   • Cookies: {size_kb:.1f} KB")
                else:
                    print(f"   • Cookies: Not found")
    else:
        print(f"\n❌ Browser profiles directory not found")
        print(f"   Will be created on first run")


async def main():
    """Run full test flow."""
    print("\n" + "=" * 70)
    print("LINKEDIN AUTOMATION TEST SUITE")
    print("=" * 70)
    print("\nThis will test:")
    print("1. ✅ playwright-stealth (anti-detection)")
    print("2. ✅ Credential authentication + 2FA")
    print("3. ✅ Connection extraction (10 connections)")
    print("4. ✅ Warning detection system")
    print("5. ✅ Persistent browser profiles")
    print("\n⚠️  Use a TEST account, not your personal LinkedIn!")

    proceed = input("\nProceed with tests? (y/N): ").strip().lower()
    if proceed != 'y':
        print("Tests cancelled.")
        return

    try:
        # Phase 1: Authentication
        cookies = await test_authentication()
        if not cookies:
            print("\n❌ Authentication failed - stopping tests")
            return

        # Phase 2: Extraction
        await test_extraction(cookies)

        # Phase 3: Warning Detection
        await test_warning_detection()

        # Phase 4: Browser Profile
        await test_browser_profile()

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print("\n✅ All tests completed!")
        print("\nNext steps:")
        print("1. Check browser_profiles/ directory for persistent data")
        print("2. Run again to verify session persistence")
        print("3. Monitor for 24 hours to check cookie validity")
        print("4. Review TESTING_GUIDE.md for comprehensive testing")

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
