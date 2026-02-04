"""Hashing utilities for passwords and data integrity."""

import hashlib
import json
from typing import Any

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def hash_data(data: bytes) -> str:
    """Generate SHA256 hash of binary data."""
    return hashlib.sha256(data).hexdigest()


def hash_json(obj: Any) -> str:
    """Generate SHA256 hash of a JSON-serializable object."""
    json_str = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hash_data(json_str.encode("utf-8"))


def hash_chain(prev_hash: str, event_data: str) -> str:
    """Generate next hash in a chain (for audit log)."""
    combined = f"{prev_hash}:{event_data}"
    return hash_data(combined.encode("utf-8"))
