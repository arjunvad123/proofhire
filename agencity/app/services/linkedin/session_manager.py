"""
LinkedIn session manager.

Handles:
- Storing encrypted LinkedIn session cookies
- Session validation and health monitoring
- Cookie refresh and expiration
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from supabase import Client

from .encryption import CookieEncryption


class LinkedInSessionManager:
    """Manages LinkedIn session cookies and lifecycle."""

    # Session expires after 30 days
    SESSION_EXPIRY_DAYS = 30

    # Required cookies for valid session
    REQUIRED_COOKIES = ['li_at']

    def __init__(self, supabase_client: Optional[Client] = None):
        """Initialize with optional Supabase client."""
        if supabase_client:
            self.supabase = supabase_client
        else:
            from supabase import create_client
            from app.config import settings
            self.supabase = create_client(settings.supabase_url, settings.supabase_key)
        
        self.encryption = CookieEncryption()

    async def create_session(
        self,
        company_id: str,
        user_id: str,
        cookies: Dict[str, Any],
        user_timezone: Optional[str] = None,
        user_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new LinkedIn session.

        Args:
            company_id: Company UUID
            user_id: User UUID
            cookies: LinkedIn cookies from browser
            user_timezone: User's timezone (e.g., "America/Los_Angeles")
            user_location: User's location (e.g., "San Francisco, CA")

        Returns:
            Session info including session_id
        """
        # Validate required cookies
        if not self._validate_cookies(cookies):
            raise ValueError("Missing required LinkedIn cookies (li_at)")

        # Check for existing session
        existing = await self.get_session_by_user(company_id, user_id)
        if existing:
            # Update existing session instead of creating new
            return await self.refresh_session(existing['id'], cookies)

        # Extract LinkedIn user info from cookies if available
        linkedin_user_id = None
        linkedin_name = None

        # Encrypt cookies
        encrypted_cookies = self.encryption.encrypt_cookies(cookies)

        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.SESSION_EXPIRY_DAYS)

        # Create session record
        session_data = {
            'company_id': company_id,
            'user_id': user_id,
            'cookies_encrypted': encrypted_cookies,
            'linkedin_user_id': linkedin_user_id,
            'linkedin_name': linkedin_name,
            'user_location': user_location,
            'user_timezone': user_timezone or 'UTC',
            'status': 'active',
            'health': 'healthy',
            'expires_at': expires_at.isoformat(),
            'connected_at': datetime.now(timezone.utc).isoformat()
        }

        result = self.supabase.table('linkedin_sessions').insert(session_data).execute()

        if not result.data:
            raise Exception("Failed to create LinkedIn session")

        session = result.data[0]

        return {
            'session_id': session['id'],
            'status': 'connected',
            'linkedin_name': linkedin_name,
            'expires_at': expires_at.isoformat(),
            'message': 'LinkedIn connected successfully'
        }

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        result = self.supabase.table('linkedin_sessions')\
            .select('*')\
            .eq('id', session_id)\
            .execute()

        if not result.data:
            return None

        return result.data[0]

    async def get_session_by_user(self, company_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session by company and user."""
        result = self.supabase.table('linkedin_sessions')\
            .select('*')\
            .eq('company_id', company_id)\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()

        if not result.data:
            return None

        return result.data[0]

    async def get_session_cookies(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get decrypted cookies for a session."""
        session = await self.get_session(session_id)

        if not session:
            return None

        if session['status'] != 'active':
            return None

        # Decrypt cookies
        return self.encryption.decrypt_cookies(session['cookies_encrypted'])

    async def refresh_session(self, session_id: str, cookies: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh session with new cookies.

        Args:
            session_id: Session UUID
            cookies: New LinkedIn cookies

        Returns:
            Updated session info
        """
        if not self._validate_cookies(cookies):
            raise ValueError("Missing required LinkedIn cookies")

        # Encrypt new cookies
        encrypted_cookies = self.encryption.encrypt_cookies(cookies)

        # Extend expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.SESSION_EXPIRY_DAYS)

        # Update session
        result = self.supabase.table('linkedin_sessions')\
            .update({
                'cookies_encrypted': encrypted_cookies,
                'expires_at': expires_at.isoformat(),
                'status': 'active',
                'health': 'healthy',
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', session_id)\
            .execute()

        if not result.data:
            raise Exception("Failed to refresh session")

        return {
            'session_id': session_id,
            'status': 'refreshed',
            'expires_at': expires_at.isoformat(),
            'message': 'Session refreshed successfully'
        }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session status."""
        session = await self.get_session(session_id)

        if not session:
            return {
                'status': 'not_found',
                'message': 'Session not found'
            }

        return {
            'status': session['status'],
            'health': session['health'],
            'connections_extracted': session.get('connections_extracted', 0),
            'profiles_enriched': session.get('profiles_enriched', 0),
            'messages_sent': session.get('messages_sent', 0),
            'expires_at': session['expires_at'],
            'last_activity_at': session.get('last_activity_at'),
            'paused_until': session.get('paused_until')
        }

    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete (disconnect) a session.

        This clears all stored cookies and marks session as disconnected.
        """
        # Update status instead of hard delete (for audit trail)
        result = self.supabase.table('linkedin_sessions')\
            .update({
                'status': 'disconnected',
                'cookies_encrypted': None,  # Clear cookies
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', session_id)\
            .execute()

        return {
            'status': 'disconnected',
            'message': 'LinkedIn session deleted'
        }

    async def pause_session(self, session_id: str, hours: int = 72) -> Dict[str, Any]:
        """
        Pause a session (e.g., after detecting LinkedIn warning).

        Args:
            session_id: Session UUID
            hours: Hours to pause for (default 72)
        """
        paused_until = datetime.now(timezone.utc) + timedelta(hours=hours)

        result = self.supabase.table('linkedin_sessions')\
            .update({
                'status': 'paused',
                'paused_until': paused_until.isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', session_id)\
            .execute()

        return {
            'status': 'paused',
            'paused_until': paused_until.isoformat(),
            'message': f'Session paused for {hours} hours'
        }

    async def update_health(self, session_id: str, health: str) -> None:
        """
        Update session health status.

        Args:
            session_id: Session UUID
            health: 'healthy', 'warning', or 'restricted'
        """
        self.supabase.table('linkedin_sessions')\
            .update({
                'health': health,
                'updated_at': datetime.now(timezone.utc).isoformat()
            })\
            .eq('id', session_id)\
            .execute()

    async def record_activity(
        self,
        session_id: str,
        activity_type: str,
        count: int = 1
    ) -> None:
        """
        Record activity on session (for rate limiting).

        Args:
            session_id: Session UUID
            activity_type: 'extraction', 'enrichment', or 'message'
            count: Number of activities
        """
        session = await self.get_session(session_id)
        if not session:
            return

        update_data = {
            'last_activity_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        # Increment appropriate counter
        if activity_type == 'extraction':
            update_data['connections_extracted'] = (
                session.get('connections_extracted', 0) + count
            )
        elif activity_type == 'enrichment':
            update_data['profiles_enriched'] = (
                session.get('profiles_enriched', 0) + count
            )
            update_data['daily_enrichment_count'] = (
                session.get('daily_enrichment_count', 0) + count
            )
        elif activity_type == 'message':
            update_data['messages_sent'] = (
                session.get('messages_sent', 0) + count
            )
            update_data['daily_message_count'] = (
                session.get('daily_message_count', 0) + count
            )

        self.supabase.table('linkedin_sessions')\
            .update(update_data)\
            .eq('id', session_id)\
            .execute()

    async def reset_daily_counts(self) -> int:
        """
        Reset daily activity counts for all sessions.
        Should be called by a daily cron job.

        Returns:
            Number of sessions reset
        """
        result = self.supabase.table('linkedin_sessions')\
            .update({
                'daily_message_count': 0,
                'daily_enrichment_count': 0
            })\
            .neq('status', 'disconnected')\
            .execute()

        return len(result.data) if result.data else 0

    async def get_active_sessions(self, company_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a company."""
        result = self.supabase.table('linkedin_sessions')\
            .select('id, user_id, linkedin_name, status, health, connected_at, expires_at')\
            .eq('company_id', company_id)\
            .eq('status', 'active')\
            .execute()

        return result.data or []

    def _validate_cookies(self, cookies: Dict[str, Any]) -> bool:
        """Check if cookies contain required values."""
        for required in self.REQUIRED_COOKIES:
            if required not in cookies:
                return False
            if not cookies[required].get('value'):
                return False
        return True
