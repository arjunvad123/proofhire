"""
LinkedIn Account Manager - Multi-account session isolation.

Manages browser profiles and sessions for multiple LinkedIn accounts:
- Each account gets its own isolated browser profile (keyed by email hash)
- Profiles persist cookies, localStorage, cache between runs
- Supports server deployment with proper profile management
- Handles profile lifecycle (create, clear, delete)

Architecture:
    Email → Hash → Profile Directory → Browser Context → Cookies

    account_manager/
    ├── profiles/
    │   ├── a1b2c3d4/          # Hash of account1@example.com
    │   │   └── Default/       # Chromium profile data
    │   ├── e5f6g7h8/          # Hash of account2@example.com
    │   │   └── Default/
    │   └── ...
    └── accounts.json          # Account metadata (optional)
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Manages isolated browser profiles for multiple LinkedIn accounts.

    Each account gets a unique profile directory based on a hash of the email.
    This ensures complete isolation between accounts while maintaining
    persistent sessions for each.
    """

    DEFAULT_PROFILES_DIR = Path("./browser_profiles")
    METADATA_FILE = "account_metadata.json"

    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize account manager.

        Args:
            profiles_dir: Root directory for browser profiles.
                         Defaults to ./browser_profiles
        """
        self.profiles_dir = Path(profiles_dir) if profiles_dir else self.DEFAULT_PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.profiles_dir / self.METADATA_FILE
        self._metadata = self._load_metadata()

    # ─────────────────────────────────────────────────────────────────────────
    # Profile ID Generation
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_profile_id(email: str) -> str:
        """
        Generate a unique profile ID from an email address.

        Uses SHA256 hash truncated to 16 chars for a stable, unique identifier
        that doesn't expose the email in the filesystem.

        Args:
            email: LinkedIn account email

        Returns:
            16-character hex string profile ID
        """
        normalized = email.lower().strip()
        hash_bytes = hashlib.sha256(normalized.encode()).hexdigest()
        return hash_bytes[:16]

    @staticmethod
    def get_profile_id_from_session(session_id: str) -> str:
        """
        Extract or generate profile ID from a session ID.

        If session_id looks like an email, hash it.
        Otherwise, hash the session_id itself for consistency.

        Args:
            session_id: Session identifier (could be email, UUID, etc.)

        Returns:
            16-character profile ID
        """
        # If it looks like an email, use email hashing
        if "@" in session_id:
            return AccountManager.get_profile_id(session_id)

        # Otherwise, hash the session_id for consistency
        hash_bytes = hashlib.sha256(session_id.encode()).hexdigest()
        return hash_bytes[:16]

    # ─────────────────────────────────────────────────────────────────────────
    # Profile Management
    # ─────────────────────────────────────────────────────────────────────────

    def get_profile_path(self, email_or_id: str) -> Path:
        """
        Get the filesystem path for an account's browser profile.

        Args:
            email_or_id: Email address or profile ID

        Returns:
            Path to the profile directory
        """
        if "@" in email_or_id:
            profile_id = self.get_profile_id(email_or_id)
        else:
            profile_id = email_or_id

        return self.profiles_dir / profile_id

    def profile_exists(self, email_or_id: str) -> bool:
        """Check if a profile exists for the given account."""
        profile_path = self.get_profile_path(email_or_id)
        return profile_path.exists() and any(profile_path.iterdir())

    def create_profile(self, email: str) -> Path:
        """
        Create a new browser profile directory for an account.

        Args:
            email: LinkedIn account email

        Returns:
            Path to the created profile directory
        """
        profile_id = self.get_profile_id(email)
        profile_path = self.profiles_dir / profile_id
        profile_path.mkdir(parents=True, exist_ok=True)

        # Update metadata
        self._metadata[profile_id] = {
            "email_hash": hashlib.sha256(email.lower().strip().encode()).hexdigest(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
        }
        self._save_metadata()

        logger.info(f"Created browser profile: {profile_id} for account")
        return profile_path

    def clear_profile(self, email_or_id: str) -> bool:
        """
        Clear all data from a profile (cookies, cache, etc.) without deleting it.

        Useful when switching accounts or resetting a corrupted profile.

        Args:
            email_or_id: Email address or profile ID

        Returns:
            True if profile was cleared, False if it didn't exist
        """
        profile_path = self.get_profile_path(email_or_id)

        if not profile_path.exists():
            return False

        # Remove all contents but keep the directory
        for item in profile_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        logger.info(f"Cleared browser profile: {profile_path.name}")
        return True

    def delete_profile(self, email_or_id: str) -> bool:
        """
        Completely delete a browser profile.

        Args:
            email_or_id: Email address or profile ID

        Returns:
            True if deleted, False if it didn't exist
        """
        profile_path = self.get_profile_path(email_or_id)

        if not profile_path.exists():
            return False

        shutil.rmtree(profile_path)

        # Update metadata
        if "@" in email_or_id:
            profile_id = self.get_profile_id(email_or_id)
        else:
            profile_id = email_or_id

        self._metadata.pop(profile_id, None)
        self._save_metadata()

        logger.info(f"Deleted browser profile: {profile_id}")
        return True

    def update_last_used(self, email_or_id: str) -> None:
        """Update the last_used timestamp for a profile."""
        if "@" in email_or_id:
            profile_id = self.get_profile_id(email_or_id)
        else:
            profile_id = email_or_id

        if profile_id in self._metadata:
            self._metadata[profile_id]["last_used"] = datetime.now(timezone.utc).isoformat()
            self._save_metadata()

    # ─────────────────────────────────────────────────────────────────────────
    # Account Listing
    # ─────────────────────────────────────────────────────────────────────────

    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all browser profiles with metadata.

        Returns:
            List of profile info dicts
        """
        profiles = []

        for profile_dir in self.profiles_dir.iterdir():
            if profile_dir.is_dir() and profile_dir.name != self.METADATA_FILE.replace(".json", ""):
                profile_id = profile_dir.name

                # Get size
                size_bytes = sum(f.stat().st_size for f in profile_dir.rglob("*") if f.is_file())
                size_mb = size_bytes / (1024 * 1024)

                # Get metadata
                meta = self._metadata.get(profile_id, {})

                profiles.append({
                    "profile_id": profile_id,
                    "path": str(profile_dir),
                    "size_mb": round(size_mb, 2),
                    "created_at": meta.get("created_at"),
                    "last_used": meta.get("last_used"),
                    "has_cookies": (profile_dir / "Default" / "Cookies").exists() or
                                   any(profile_dir.glob("**/Cookies")),
                })

        return profiles

    def cleanup_old_profiles(self, days_unused: int = 30) -> int:
        """
        Delete profiles that haven't been used in N days.

        Args:
            days_unused: Delete profiles unused for this many days

        Returns:
            Number of profiles deleted
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_unused)
        deleted = 0

        for profile_id, meta in list(self._metadata.items()):
            last_used = meta.get("last_used")
            if last_used:
                last_used_dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
                if last_used_dt < cutoff:
                    if self.delete_profile(profile_id):
                        deleted += 1

        logger.info(f"Cleaned up {deleted} old profiles (unused for {days_unused}+ days)")
        return deleted

    # ─────────────────────────────────────────────────────────────────────────
    # Cookie Management (for migration/backup)
    # ─────────────────────────────────────────────────────────────────────────

    def export_cookies(self, email_or_id: str, output_path: Path) -> bool:
        """
        Export cookies from a profile to a JSON file.

        Note: This exports from the cookie cache file, not from a running browser.
        For complete cookie export, use the browser context's cookies() method.

        Args:
            email_or_id: Email or profile ID
            output_path: Path to write cookies JSON

        Returns:
            True if exported, False if profile doesn't exist
        """
        profile_path = self.get_profile_path(email_or_id)

        if not profile_path.exists():
            return False

        # Look for cookie files
        cookie_files = list(profile_path.glob("**/Cookies"))

        if not cookie_files:
            logger.warning(f"No cookie files found in profile {profile_path.name}")
            return False

        # Note: Chromium cookies are in SQLite format, would need sqlite3 to read
        # For now, just copy the raw file
        shutil.copy(cookie_files[0], output_path)
        logger.info(f"Exported cookies to {output_path}")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Metadata Persistence
    # ─────────────────────────────────────────────────────────────────────────

    def _load_metadata(self) -> Dict[str, Any]:
        """Load account metadata from disk."""
        if self._metadata_path.exists():
            try:
                return json.loads(self._metadata_path.read_text())
            except Exception as e:
                logger.warning(f"Failed to load account metadata: {e}")
        return {}

    def _save_metadata(self) -> None:
        """Save account metadata to disk."""
        try:
            self._metadata_path.write_text(json.dumps(self._metadata, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save account metadata: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────

_default_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    """Get the default AccountManager instance (singleton)."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AccountManager()
    return _default_manager


def get_profile_path_for_email(email: str) -> Path:
    """Convenience function to get profile path for an email."""
    return get_account_manager().get_profile_path(email)


def clear_account_profile(email: str) -> bool:
    """Convenience function to clear an account's profile."""
    return get_account_manager().clear_profile(email)
