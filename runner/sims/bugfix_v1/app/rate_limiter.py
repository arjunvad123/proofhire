"""Rate limiter implementation for API endpoints.

This module provides a sliding window rate limiter that tracks request
counts per client within a configurable time window.

KNOWN BUG: There is an off-by-one error in the rate limit check.
The limiter allows one extra request beyond the configured limit.
"""

from typing import Dict, List


class RateLimiter:
    """Sliding window rate limiter.

    Tracks request timestamps per client and rejects requests
    that exceed the configured limit within the time window.

    Attributes:
        max_requests: Maximum number of requests allowed per window
        window_seconds: Size of the sliding window in seconds
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """Initialize the rate limiter.

        Args:
            max_requests: Maximum allowed requests per window
            window_seconds: Window duration in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def allow_request(self, client_id: str, timestamp: float) -> bool:
        """Check if a request from the client should be allowed.

        Implements a sliding window algorithm:
        1. Remove expired timestamps from the client's history
        2. Check if adding a new request would exceed the limit
        3. If allowed, record the timestamp

        Args:
            client_id: Unique identifier for the client
            timestamp: Unix timestamp of the request

        Returns:
            True if the request is allowed, False if rate limited
        """
        # Calculate the window cutoff
        cutoff = timestamp - self.window_seconds

        # Get or create request history for this client
        if client_id not in self._requests:
            self._requests[client_id] = []

        # Remove expired timestamps (outside the window)
        self._requests[client_id] = [
            t for t in self._requests[client_id]
            if t > cutoff
        ]

        # BUG: Off-by-one error!
        # Should be: len(...) >= self.max_requests
        # Currently allows max_requests + 1 requests
        if len(self._requests[client_id]) > self.max_requests:
            return False

        # Record this request
        self._requests[client_id].append(timestamp)
        return True

    def get_remaining(self, client_id: str, timestamp: float) -> int:
        """Get the number of remaining requests for a client.

        Args:
            client_id: Unique identifier for the client
            timestamp: Current timestamp

        Returns:
            Number of requests remaining in the current window
        """
        cutoff = timestamp - self.window_seconds

        if client_id not in self._requests:
            return self.max_requests

        active_requests = [
            t for t in self._requests[client_id]
            if t > cutoff
        ]

        return max(0, self.max_requests - len(active_requests))

    def reset(self, client_id: str) -> None:
        """Reset rate limit for a specific client.

        Args:
            client_id: Client to reset
        """
        if client_id in self._requests:
            del self._requests[client_id]

    def reset_all(self) -> None:
        """Reset rate limits for all clients."""
        self._requests.clear()
