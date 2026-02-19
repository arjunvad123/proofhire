"""
LinkedIn automation services.

This module provides:
- Session management (cookie-based authentication)
- Credential authentication (direct login)
- Connection extraction
- Profile enrichment via scraper pool
- DM automation with safe rate limits
"""

from .session_manager import LinkedInSessionManager
from .encryption import CookieEncryption
from .credential_auth import LinkedInCredentialAuth
from .proxy_manager import ProxyManager

__all__ = [
    'LinkedInSessionManager',
    'CookieEncryption',
    'LinkedInCredentialAuth',
    'ProxyManager'
]
