"""Time utilities."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime (timezone-naive for database compatibility)."""
    return datetime.utcnow()


def to_timestamp(dt: datetime) -> float:
    """Convert datetime to Unix timestamp."""
    return dt.timestamp()


def from_timestamp(ts: float) -> datetime:
    """Convert Unix timestamp to UTC datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)
