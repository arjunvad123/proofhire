"""
LinkedIn automation services.

This module provides:
- Session management (cookie-based authentication)
- Credential authentication (direct login)
- Connection extraction with natural navigation chain
- Stealth browser with context-level evasions
- Profile enrichment via scraper pool
- DM automation with safe rate limits
- Human behavior simulation (idle patterns, warmup mode)
"""

from .session_manager import LinkedInSessionManager
from .encryption import CookieEncryption
from .credential_auth import LinkedInCredentialAuth
from .proxy_manager import ProxyManager
from .stealth_browser import StealthBrowser
from .connection_extractor import LinkedInConnectionExtractor
from .account_manager import AccountManager, get_account_manager
from .human_behavior import (
    ExtractionConfig,
    ExtractionMode,
    IdlePatternGenerator,
    GhostCursor,
    GhostCursorIntegration,
    HumanBehaviorEngine,
)

__all__ = [
    'LinkedInSessionManager',
    'CookieEncryption',
    'LinkedInCredentialAuth',
    'ProxyManager',
    'StealthBrowser',
    'LinkedInConnectionExtractor',
    # Account management
    'AccountManager',
    'get_account_manager',
    # Human behavior exports
    'ExtractionConfig',
    'ExtractionMode',
    'IdlePatternGenerator',
    'GhostCursor',
    'GhostCursorIntegration',
    'HumanBehaviorEngine',
]
