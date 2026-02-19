"""
Root pytest configuration.

Provides a session-scoped `linkedin_cookies` fixture that loads LinkedIn
session cookies from a local cache file so tests never need to log in.

To generate the cache (one-time, requires accepting a single sign-in email):
    python scripts/save_test_auth.py

The cache file (.linkedin_test_cache.json) is valid for ~1 year.
Re-run the script above when it expires.
"""

import json
import sys
from pathlib import Path

import pytest

# Keep the project root importable from tests
sys.path.insert(0, str(Path(__file__).parent))

CACHE_PATH = Path(__file__).parent / ".linkedin_test_cache.json"


@pytest.fixture(scope="session")
def linkedin_cookies() -> dict:
    """
    Real LinkedIn cookies loaded from the local cache file.

    No browser is launched, no login is performed, no sign-in email is sent.
    Inject these into a Playwright context via ``context.add_cookies()``.

    Skips the test (with a helpful message) if the cache doesn't exist yet.
    """
    if not CACHE_PATH.exists():
        pytest.skip(
            f"\n\nNo cached LinkedIn cookies found at {CACHE_PATH}.\n"
            "Run the one-time setup script first:\n"
            "    python scripts/save_test_auth.py\n"
        )

    try:
        cookies = json.loads(CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        pytest.skip(f"Failed to read cookie cache ({exc}). Re-run save_test_auth.py")

    li_at = cookies.get("li_at", {})
    if not li_at.get("value"):
        pytest.skip(
            "Cached li_at cookie is missing or empty. "
            "Re-run: python scripts/save_test_auth.py"
        )

    return cookies


@pytest.fixture(scope="session")
def linkedin_cookie_list(linkedin_cookies: dict) -> list:
    """
    Same cookies as `linkedin_cookies` but formatted as the list that
    Playwright's ``context.add_cookies()`` expects.
    """
    cookie_list = []
    for name, data in linkedin_cookies.items():
        cookie: dict = {
            "name": name,
            "value": data["value"],
            "domain": data.get("domain", ".linkedin.com"),
            "path": data.get("path", "/"),
            "secure": data.get("secure", True),
            "httpOnly": data.get("httpOnly", False),
        }
        if data.get("expirationDate"):
            cookie["expires"] = data["expirationDate"]
        cookie_list.append(cookie)
    return cookie_list
