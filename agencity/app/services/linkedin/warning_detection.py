"""
LinkedIn warning detection and handling.

Monitors for LinkedIn restrictions, warnings, and unusual activity alerts.
Automatically pauses sessions and notifies users when issues are detected.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from playwright.async_api import Page


class LinkedInWarningDetector:
    """Detect and handle LinkedIn warnings and restrictions."""

    # Warning selectors to monitor
    WARNING_SELECTORS = [
        # Restriction banners
        '[data-test-id="restriction-notice"]',
        '.restriction-banner',
        '.artdeco-banner--warning',

        # Unusual activity messages
        'text="unusual activity"',
        'text="temporarily restricted"',
        'text="verify your identity"',
        'text="suspicious activity"',

        # CAPTCHA challenges
        '[id*="captcha"]',
        '[class*="captcha"]',
        'text="Please verify you\'re a human"',

        # Security checkpoint
        'text="Security Verification"',
        'text="Let\'s verify your identity"',

        # Account restrictions
        'text="account has been restricted"',
        'text="violated our User Agreement"',
    ]

    async def check_for_warnings(self, page: Page) -> Optional[Dict[str, Any]]:
        """
        Check page for LinkedIn warnings or restrictions.

        Args:
            page: Playwright page to check

        Returns:
            Warning details if detected, None otherwise:
            {
                'type': 'restriction' | 'captcha' | 'verification' | 'unusual_activity',
                'message': str,
                'selector': str (which selector matched),
                'timestamp': datetime
            }
        """
        for selector in self.WARNING_SELECTORS:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    # Found a warning - extract details
                    warning_type = self._classify_warning(selector)

                    # Try to get warning message text
                    try:
                        element = page.locator(selector).first
                        message = await element.text_content(timeout=2000)
                    except:
                        message = f"Warning detected via selector: {selector}"

                    return {
                        'type': warning_type,
                        'message': message.strip() if message else "LinkedIn warning detected",
                        'selector': selector,
                        'timestamp': datetime.now(timezone.utc),
                        'page_url': page.url
                    }
            except Exception as e:
                # Selector failed - continue checking others
                continue

        return None

    def _classify_warning(self, selector: str) -> str:
        """
        Classify warning type based on selector.

        Args:
            selector: CSS selector or text that matched

        Returns:
            Warning type string
        """
        selector_lower = selector.lower()

        if 'captcha' in selector_lower:
            return 'captcha'
        elif 'verify' in selector_lower or 'identity' in selector_lower:
            return 'verification'
        elif 'restricted' in selector_lower or 'violated' in selector_lower:
            return 'restriction'
        elif 'unusual' in selector_lower or 'suspicious' in selector_lower:
            return 'unusual_activity'
        else:
            return 'unknown'

    async def check_for_rate_limit_indicators(self, page: Page) -> bool:
        """
        Check for soft rate limit indicators (slower responses, empty results).

        Args:
            page: Playwright page

        Returns:
            True if rate limiting detected
        """
        # Check for empty results that might indicate throttling
        try:
            # LinkedIn often shows "No results" when rate limited
            no_results_selectors = [
                'text="No results found"',
                'text="Try adjusting your search"',
                '.search-results-empty',
                '.artdeco-empty-state'
            ]

            for selector in no_results_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    # Could be legitimate empty results or rate limiting
                    # Return True only if URL suggests there should be results
                    url = page.url
                    if '/search/' in url or '/mynetwork/' in url:
                        return True
        except:
            pass

        return False


class WarningHandler:
    """Handle LinkedIn warnings by pausing sessions and notifying users."""

    def __init__(self, session_manager):
        """
        Initialize warning handler.

        Args:
            session_manager: LinkedInSessionManager instance
        """
        self.session_manager = session_manager

    async def handle_warning(
        self,
        session_id: str,
        warning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle detected warning by pausing session and notifying user.

        Args:
            session_id: Session ID
            warning: Warning details from detector

        Returns:
            Action taken details
        """
        # Determine pause duration based on warning type
        pause_hours = self._get_pause_duration(warning['type'])

        # Pause session
        await self.session_manager.pause_session(
            session_id,
            hours=pause_hours,
            reason=f"{warning['type']}: {warning['message']}"
        )

        # Record warning event
        await self.session_manager.record_warning(
            session_id,
            warning_type=warning['type'],
            message=warning['message'],
            selector=warning['selector'],
            page_url=warning.get('page_url')
        )

        # TODO: Send notification to user
        # await send_notification(
        #     session_id,
        #     title="LinkedIn Activity Paused",
        #     message=f"We detected a {warning['type']} warning and paused activity for {pause_hours} hours."
        # )

        return {
            'action': 'paused',
            'pause_hours': pause_hours,
            'warning_type': warning['type'],
            'message': warning['message'],
            'resume_at': (datetime.now(timezone.utc) + timedelta(hours=pause_hours)).isoformat()
        }

    def _get_pause_duration(self, warning_type: str) -> int:
        """
        Get pause duration based on warning severity.

        Args:
            warning_type: Type of warning

        Returns:
            Hours to pause
        """
        pause_durations = {
            'captcha': 24,              # 24 hours for CAPTCHA
            'verification': 48,          # 48 hours for identity verification
            'restriction': 72,           # 72 hours for account restrictions
            'unusual_activity': 48,      # 48 hours for unusual activity
            'unknown': 24                # 24 hours default
        }

        return pause_durations.get(warning_type, 24)

    async def should_reduce_limits(self, session_id: str) -> bool:
        """
        Check if session should have reduced limits after warning.

        Args:
            session_id: Session ID

        Returns:
            True if limits should be reduced
        """
        # Get recent warnings for this session
        recent_warnings = await self.session_manager.get_recent_warnings(
            session_id,
            hours=168  # Last 7 days
        )

        # If 2+ warnings in last week, reduce limits
        return len(recent_warnings) >= 2

    async def get_recommended_limits(
        self,
        session_id: str,
        base_limits: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Get recommended rate limits for session based on history.

        Args:
            session_id: Session ID
            base_limits: Base rate limits

        Returns:
            Adjusted limits
        """
        if await self.should_reduce_limits(session_id):
            # Reduce all limits to 50%
            return {
                key: int(value * 0.5)
                for key, value in base_limits.items()
            }
        else:
            return base_limits


# Convenience function for use in extraction/automation flows
async def check_and_handle_warnings(
    page: Page,
    session_id: str,
    session_manager,
    raise_on_warning: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Check for warnings and handle if found.

    Args:
        page: Playwright page
        session_id: Session ID
        session_manager: LinkedInSessionManager instance
        raise_on_warning: If True, raise exception when warning detected

    Returns:
        Warning handling result if warning detected, None otherwise

    Raises:
        LinkedInWarningException: If warning detected and raise_on_warning=True
    """
    detector = LinkedInWarningDetector()
    warning = await detector.check_for_warnings(page)

    if warning:
        handler = WarningHandler(session_manager)
        result = await handler.handle_warning(session_id, warning)

        if raise_on_warning:
            raise LinkedInWarningException(
                f"LinkedIn {warning['type']} detected: {warning['message']}",
                warning=warning,
                handling_result=result
            )

        return result

    return None


class LinkedInWarningException(Exception):
    """Exception raised when LinkedIn warning is detected."""

    def __init__(self, message: str, warning: Dict[str, Any], handling_result: Dict[str, Any]):
        """
        Initialize exception.

        Args:
            message: Error message
            warning: Warning details
            handling_result: Result of warning handling
        """
        super().__init__(message)
        self.warning = warning
        self.handling_result = handling_result
