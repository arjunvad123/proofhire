"""
Redis-based sliding window rate limiter for Agencity.
"""

import logging
import time

from fastapi import HTTPException, Request, status

from app.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            except Exception:
                logger.warning("Redis unavailable, rate limiting disabled")
                return None
        return self._redis

    async def check(self, key: str, limit: int, window_seconds: int):
        """
        Check if a request is within the rate limit.

        Uses Redis sorted set sliding window.
        Raises HTTPException(429) if limit exceeded.
        """
        r = self._get_redis()
        if r is None:
            return  # Fail open if Redis is unavailable

        now = time.time()
        window_start = now - window_seconds
        redis_key = f"ratelimit:{key}"

        pipe = r.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zadd(redis_key, {str(now): now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window_seconds + 1)
        results = pipe.execute()

        current_count = results[2]

        if current_count > limit:
            retry_after = int(window_seconds - (now - window_start))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. {limit} requests per {window_seconds}s.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )


rate_limiter = RateLimiter()
