"""Tests for the RateLimiter class.

These tests verify the rate limiting behavior including:
- Basic request allowing
- Rate limit enforcement
- Window expiration
- Multiple clients
"""

import pytest
from app.rate_limiter import RateLimiter


class TestRateLimiterBasics:
    """Basic functionality tests."""

    def test_allows_first_request(self):
        """First request from a client should always be allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.allow_request("client1", 0.0) is True

    def test_allows_requests_up_to_limit(self):
        """Should allow exactly max_requests within a window."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # First 3 requests should all be allowed
        assert limiter.allow_request("client1", 0.0) is True
        assert limiter.allow_request("client1", 1.0) is True
        assert limiter.allow_request("client1", 2.0) is True

    def test_blocks_requests_over_limit(self):
        """Should block the (max_requests + 1)th request.

        This test fails with the current buggy implementation
        because of the off-by-one error (> vs >=).
        """
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Make exactly max_requests calls
        for i in range(3):
            assert limiter.allow_request("client1", float(i)) is True

        # The 4th request should be blocked
        assert limiter.allow_request("client1", 3.0) is False

    def test_different_clients_have_separate_limits(self):
        """Each client should have their own rate limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # client1 uses their quota
        assert limiter.allow_request("client1", 0.0) is True
        assert limiter.allow_request("client1", 1.0) is True

        # client2 should still have their full quota
        assert limiter.allow_request("client2", 2.0) is True
        assert limiter.allow_request("client2", 3.0) is True


class TestWindowExpiration:
    """Tests for sliding window expiration."""

    def test_allows_requests_after_window_expires(self):
        """Requests should be allowed after the window slides."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)

        # Use up the quota
        assert limiter.allow_request("client1", 0.0) is True
        assert limiter.allow_request("client1", 1.0) is True

        # After window expires, should allow again
        # 11.0 is outside the 10-second window from 0.0 and 1.0
        assert limiter.allow_request("client1", 11.0) is True

    def test_partial_window_expiration(self):
        """Old requests expire as the window slides."""
        limiter = RateLimiter(max_requests=2, window_seconds=10)

        # Make requests at t=0 and t=5
        assert limiter.allow_request("client1", 0.0) is True
        assert limiter.allow_request("client1", 5.0) is True

        # At t=11, the t=0 request has expired but t=5 hasn't
        # So we should have 1 slot available
        assert limiter.allow_request("client1", 11.0) is True

        # But not 2 (t=5 still in window)
        # This should be blocked - only 1 spot was available
        assert limiter.allow_request("client1", 11.5) is False


class TestRemainingRequests:
    """Tests for the get_remaining method."""

    def test_remaining_for_new_client(self):
        """New client should have full quota available."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.get_remaining("new_client", 0.0) == 5

    def test_remaining_decreases_with_requests(self):
        """Remaining count should decrease as requests are made."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        limiter.allow_request("client1", 0.0)
        assert limiter.get_remaining("client1", 1.0) == 4

        limiter.allow_request("client1", 2.0)
        assert limiter.get_remaining("client1", 3.0) == 3

    def test_remaining_resets_after_window(self):
        """Remaining should reset as requests expire from window."""
        limiter = RateLimiter(max_requests=3, window_seconds=10)

        # Use all requests
        limiter.allow_request("client1", 0.0)
        limiter.allow_request("client1", 1.0)
        limiter.allow_request("client1", 2.0)

        assert limiter.get_remaining("client1", 5.0) == 0

        # After window slides
        assert limiter.get_remaining("client1", 15.0) == 3


class TestReset:
    """Tests for reset functionality."""

    def test_reset_clears_client_history(self):
        """Reset should clear a client's request history."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        limiter.allow_request("client1", 0.0)
        limiter.allow_request("client1", 1.0)

        limiter.reset("client1")

        # Should be able to make requests again
        assert limiter.allow_request("client1", 2.0) is True
        assert limiter.allow_request("client1", 3.0) is True

    def test_reset_all_clears_all_clients(self):
        """Reset all should clear history for all clients."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        limiter.allow_request("client1", 0.0)
        limiter.allow_request("client2", 0.0)

        limiter.reset_all()

        assert limiter.allow_request("client1", 1.0) is True
        assert limiter.allow_request("client2", 1.0) is True


class TestEdgeCases:
    """Edge case tests."""

    def test_zero_max_requests(self):
        """Rate limiter with 0 max requests should block everything."""
        limiter = RateLimiter(max_requests=0, window_seconds=60)
        assert limiter.allow_request("client1", 0.0) is False

    def test_very_short_window(self):
        """Very short window should allow rapid reuse."""
        limiter = RateLimiter(max_requests=1, window_seconds=1)

        assert limiter.allow_request("client1", 0.0) is True
        assert limiter.allow_request("client1", 0.5) is False
        assert limiter.allow_request("client1", 1.1) is True

    def test_timestamps_exactly_at_window_boundary(self):
        """Requests exactly at window boundary should be handled correctly."""
        limiter = RateLimiter(max_requests=1, window_seconds=10)

        assert limiter.allow_request("client1", 0.0) is True
        # Exactly at the boundary - old request at t=0 should be expired
        # Window is (timestamp - window_seconds, timestamp] = (-10, 10]
        # t=0 is outside this range, so it's expired
        assert limiter.allow_request("client1", 10.0) is True
