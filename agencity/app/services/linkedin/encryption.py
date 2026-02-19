"""
Cookie encryption service.

Uses Fernet (AES-128-CBC) for symmetric encryption of LinkedIn session cookies.
"""

import os
import json
from typing import Dict, Any
from cryptography.fernet import Fernet
from app.config import settings


class CookieEncryption:
    """Handles encryption and decryption of LinkedIn cookies."""

    def __init__(self):
        """Initialize with encryption key from settings."""
        # Use secret_key to derive Fernet key, or generate if needed
        key = self._derive_key(settings.secret_key)
        self._fernet = Fernet(key)

    def _derive_key(self, secret: str) -> bytes:
        """Derive a valid Fernet key from secret."""
        import hashlib
        import base64

        # Hash the secret to get consistent 32 bytes
        hash_bytes = hashlib.sha256(secret.encode()).digest()
        # Fernet requires base64-encoded 32-byte key
        return base64.urlsafe_b64encode(hash_bytes)

    def encrypt_cookies(self, cookies: Dict[str, Any]) -> str:
        """
        Encrypt cookies dict to string.

        Args:
            cookies: Dict of cookie name -> cookie data

        Returns:
            Encrypted string (base64 encoded)
        """
        json_bytes = json.dumps(cookies).encode('utf-8')
        encrypted = self._fernet.encrypt(json_bytes)
        return encrypted.decode('utf-8')

    def decrypt_cookies(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt encrypted cookie string.

        Args:
            encrypted: Encrypted cookie string

        Returns:
            Original cookies dict
        """
        decrypted = self._fernet.decrypt(encrypted.encode('utf-8'))
        return json.loads(decrypted.decode('utf-8'))

    def encrypt_string(self, value: str) -> str:
        """Encrypt a single string value."""
        encrypted = self._fernet.encrypt(value.encode('utf-8'))
        return encrypted.decode('utf-8')

    def decrypt_string(self, encrypted: str) -> str:
        """Decrypt a single string value."""
        decrypted = self._fernet.decrypt(encrypted.encode('utf-8'))
        return decrypted.decode('utf-8')
