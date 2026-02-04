"""ID generation utilities."""

import uuid


def generate_id() -> str:
    """Generate a new UUID4 string ID."""
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False
