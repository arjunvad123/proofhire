"""
Integration test for Phase 1 (Auth) + Phase 2 (Extraction).

This test demonstrates the complete flow:
1. Authenticate with credentials
2. Extract connections with human-like behavior
3. Store in database
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
from app.services.linkedin.human_behavior import HumanBehaviorEngine, GhostCursorIntegration
from app.services.linkedin.session_manager import LinkedInSessionManager


class TestHumanBehavior:
    """Test human behavior engine."""

    def test_session_management(self):
        """Test session start and break detection."""
        behavior = HumanBehaviorEngine()

        # Start session
        behavior.start_session()
        assert behavior.session_start is not None
        assert behavior.actions_in_session == 0

        # Should not break immediately
        assert behavior.should_take_break() is False

    def test_profile_dwell_time(self):
        """Test profile dwell time calculation."""
        behavior = HumanBehaviorEngine()

        # Simple profile
        simple_dwell = behavior.get_profile_dwell_time('simple')
        assert 20 <= simple_dwell <= 35

        # Medium profile
        medium_dwell = behavior.get_profile_dwell_time('medium')
        assert 35 <= medium_dwell <= 50

        # Complex profile
        complex_dwell = behavior.get_profile_dwell_time('complex')
        assert 50 <= complex_dwell <= 60

    def test_message_delay(self):
        """Test delay between messages."""
        behavior = HumanBehaviorEngine()

        for _ in range(10):
            delay = behavior.get_delay_between_messages()
            # Should be between 30s and 5min, skewed toward 90s
            assert 30 <= delay <= 300

    def test_working_hours(self):
        """Test working hours detection."""
        behavior = HumanBehaviorEngine()

        # This will vary based on actual time
        is_working = behavior.is_working_hours()
        assert isinstance(is_working, bool)

    def test_weekday_detection(self):
        """Test weekday detection."""
        behavior = HumanBehaviorEngine()

        is_weekday = behavior.is_weekday()
        assert isinstance(is_weekday, bool)

    def test_rate_limiting(self):
        """Test rate limit checking."""
        behavior = HumanBehaviorEngine()

        # Under limit
        can_send, reason = behavior.should_send_message(10, daily_limit=50)
        # Result depends on time of day
        assert isinstance(can_send, bool)

        # Over limit
        can_send, reason = behavior.should_send_message(50, daily_limit=50)
        assert can_send is False
        assert 'Daily limit' in reason

    def test_micro_break(self):
        """Test micro-break detection."""
        behavior = HumanBehaviorEngine()

        # Should not break at 10 messages
        assert behavior.should_take_micro_break(10) is False

        # Might break around 15-25
        # (Exact number is random, so just test it's deterministic)
        result_20 = behavior.should_take_micro_break(20)
        assert isinstance(result_20, bool)

    def test_break_duration(self):
        """Test break duration calculation."""
        behavior = HumanBehaviorEngine()

        # Regular break (2-6 hours)
        duration = behavior.get_break_duration()
        assert 7200 <= duration <= 21600  # 2-6 hours in seconds

        # Micro break (30-60 minutes)
        micro_duration = behavior.get_micro_break_duration()
        assert 1800 <= micro_duration <= 3600  # 30-60 minutes


class TestGhostCursor:
    """Test ghost cursor integration."""

    @pytest.mark.asyncio
    async def test_natural_mouse_movement(self):
        """Test natural mouse movement (mocked)."""
        # Create mock page
        mock_page = AsyncMock()

        # Setup proper async mock for locator chain
        mock_element = AsyncMock()
        mock_element.bounding_box = AsyncMock(return_value={
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 50
        })
        mock_page.locator.return_value = mock_element

        # Test move to element
        await GhostCursorIntegration.move_to_element_naturally(
            mock_page,
            'button.test',
            duration=0.1  # Short duration for test
        )

        # Should have called mouse.move multiple times
        assert mock_page.mouse.move.call_count > 10

    @pytest.mark.asyncio
    async def test_natural_click(self):
        """Test natural clicking behavior."""
        mock_page = AsyncMock()

        # Setup proper async mock for locator chain
        mock_element = AsyncMock()
        mock_element.bounding_box = AsyncMock(return_value={
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 50
        })
        mock_page.locator.return_value = mock_element

        await GhostCursorIntegration.click_naturally(mock_page, 'button.test')

        # Should have moved mouse and clicked
        assert mock_page.mouse.move.call_count > 0
        assert mock_page.click.call_count == 1


class TestConnectionExtractor:
    """Test connection extraction."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        supabase = Mock()

        # Mock get session
        select_result = Mock()
        select_result.data = [{
            'id': 'test-session',
            'cookies_encrypted': 'encrypted-cookies',
            'user_location': 'San Francisco, CA',
            'status': 'active'
        }]

        eq_result = Mock()
        eq_result.execute.return_value = select_result

        select_mock = Mock()
        select_mock.eq.return_value = eq_result

        table_mock = Mock()
        table_mock.select.return_value = select_mock

        supabase.table.return_value = table_mock

        return supabase

    @pytest.fixture
    def extractor(self, mock_supabase):
        """Create extractor with mocked dependencies."""
        session_manager = LinkedInSessionManager(mock_supabase)
        return LinkedInConnectionExtractor(session_manager)

    def test_parse_occupation(self, extractor):
        """Test occupation parsing."""
        # Standard format
        title, company = extractor._parse_occupation("Senior Engineer at Google")
        assert title == "Senior Engineer"
        assert company == "Google"

        # Pipe separator
        title, company = extractor._parse_occupation("Engineer | Meta")
        assert title == "Engineer"
        assert company == "Meta"

        # Title only
        title, company = extractor._parse_occupation("Software Engineer")
        assert title == "Software Engineer"
        assert company is None

        # None
        title, company = extractor._parse_occupation(None)
        assert title is None
        assert company is None


# ===== Manual Integration Test =====

async def manual_integration_test():
    """
    Manual integration test of Phase 1 + Phase 2.

    Tests the complete flow:
    1. Login with credentials
    2. Extract connections
    3. Verify human-like behavior

    WARNING: Requires real LinkedIn credentials!
    """
    print("\n" + "=" * 70)
    print("MANUAL INTEGRATION TEST - Phase 1 + Phase 2")
    print("=" * 70)

    # Get credentials
    email = input("\nLinkedIn Email (or press Enter to skip): ").strip()
    if not email:
        print("Skipping integration test.")
        return

    password = input("LinkedIn Password: ").strip()

    print("\n" + "-" * 70)
    print("PHASE 1: CREDENTIAL AUTHENTICATION")
    print("-" * 70)

    # Initialize auth
    auth = LinkedInCredentialAuth()

    # Login
    print("\n🚀 Logging in...")
    result = await auth.login(
        email=email,
        password=password,
        user_location="San Francisco, CA"
    )

    # Handle 2FA
    if result['status'] == '2fa_required':
        print("\n🔐 2FA Required")
        code = input("Enter 6-digit code: ").strip()

        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state')
        )

    if result['status'] != 'connected':
        print(f"\n❌ Login failed: {result.get('error')}")
        return

    print("\n✅ Login successful!")
    print(f"   Cookies extracted: {len(result['cookies'])} cookies")

    # Show li_at token (truncated)
    if 'li_at' in result['cookies']:
        token = result['cookies']['li_at']['value']
        print(f"   li_at: {token[:20]}...")

    print("\n" + "-" * 70)
    print("PHASE 2: CONNECTION EXTRACTION (DEMO)")
    print("-" * 70)

    print("\n📊 Human Behavior Demo:")
    behavior = HumanBehaviorEngine()

    # Demo profile dwell time
    print("\n1. Profile Dwell Times:")
    for complexity in ['simple', 'medium', 'complex']:
        dwell = behavior.get_profile_dwell_time(complexity)
        print(f"   • {complexity.capitalize()}: {dwell:.1f}s")

    # Demo message delays
    print("\n2. Message Send Delays (sampling 5):")
    for i in range(5):
        delay = behavior.get_delay_between_messages()
        print(f"   • Message {i+1}: {delay:.0f}s delay")

    # Demo working hours
    print("\n3. Current Status:")
    print(f"   • Working hours: {behavior.is_working_hours()}")
    print(f"   • Weekday: {behavior.is_weekday()}")

    # Demo rate limiting
    can_send, reason = behavior.should_send_message(10, daily_limit=50)
    print(f"   • Can send message: {can_send}")
    if not can_send:
        print(f"     Reason: {reason}")

    print("\n" + "-" * 70)
    print("EXTRACTION BEHAVIOR SIMULATION")
    print("-" * 70)

    print("\n📜 Simulating 10 connection extractions with human timing:")
    behavior.start_session()

    for i in range(10):
        # Simulate scroll delay
        delay = random.uniform(1.0, 3.0)
        print(f"\n   [{i+1}/10] Scroll {i+1}...")
        print(f"           • Delay: {delay:.2f}s")

        # Occasionally show back-scroll
        if random.random() < 0.1:
            print(f"           • 📖 Back-scroll (re-reading)")

        await asyncio.sleep(delay)

        # Check for break
        if behavior.should_take_break():
            print(f"\n   ⏸️  Session limit reached - would take break now")
            print(f"       Break duration: {behavior.get_break_duration() / 60:.0f} minutes")
            break

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    import sys

    # Run unit tests
    print("Running unit tests...")
    result = pytest.main([__file__, '-v', '-s', '--tb=short'])

    if result == 0:
        print("\n✅ All unit tests passed!\n")

        # Optionally run integration test
        run_integration = input("Run manual integration test with real LinkedIn? (y/N): ").strip().lower()
        if run_integration == 'y':
            asyncio.run(manual_integration_test())
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
