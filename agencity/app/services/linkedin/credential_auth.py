"""
LinkedIn credential authentication service.

Handles:
- Direct login with email/password
- 2FA code handling
- Cookie extraction
- Residential proxy usage

Uses StealthBrowser for context-level stealth + extra evasion scripts.
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext, Page

from .encryption import CookieEncryption
from .human_behavior import HumanBehaviorEngine, GhostCursor
from .stealth_browser import StealthBrowser


class LinkedInCredentialAuth:
    """Authenticate LinkedIn using credentials with 2FA support."""

    def __init__(self, encryption: Optional[CookieEncryption] = None):
        """Initialize with optional encryption service."""
        self.encryption = encryption or CookieEncryption()
        self._browser_state: Optional[Dict[str, Any]] = None

    async def login(
        self,
        email: str,
        password: str,
        user_id: Optional[str] = None,
        user_location: Optional[str] = None,
        verification_code: Optional[str] = None,
        resume_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate and extract cookies.

        Uses StealthBrowser which wraps playwright-stealth at the context level
        and injects extra evasion scripts (WebGL, canvas, audio fingerprint,
        chrome.runtime, plugins, permissions, etc.) automatically.

        Args:
            email: LinkedIn email
            password: LinkedIn password
            user_id: If provided, uses a persistent browser profile keyed to this
                     user so LinkedIn recognises the same "device" across logins.
                     Only the first login triggers a sign-in notification email;
                     subsequent logins from the same profile are silent.
            user_location: User's location for proxy selection
            verification_code: 2FA code if required
            resume_state: Browser state to resume 2FA flow

        Returns:
            {
                'status': 'connected' | '2fa_required' | 'error',
                'cookies': {...} if success,
                'verification_state': {...} if 2FA required,
                'error': str if error
            }
        """
        try:
            # Use a persistent browser profile when a user_id is supplied so
            # LinkedIn binds trust to a stable "device".  Without this, every
            # launch gets a fresh fingerprint and triggers a sign-in email.
            if user_id:
                browser_ctx = StealthBrowser.launch_persistent(
                    session_id=f"auth_{user_id}",
                    headless=False,
                    user_location=user_location,
                )
            else:
                browser_ctx = StealthBrowser.launch(
                    headless=False,
                    user_location=user_location,
                )

            async with browser_ctx as sb:
                page = await sb.new_page()

                try:
                    # If resuming 2FA flow
                    if resume_state and verification_code:
                        result = await self._resume_2fa_flow(
                            sb.context, page, resume_state, verification_code
                        )
                        return result

                    # Navigate to login page
                    await page.goto(
                        'https://www.linkedin.com/login',
                        wait_until='networkidle',
                        timeout=30000
                    )

                    # Fill credentials using ghost cursor (move → click → type)
                    cursor = GhostCursor(page)

                    # Move to email field, click, type
                    await cursor.type_into('input[name="session_key"]', email)
                    await asyncio.sleep(random.uniform(0.3, 0.8))

                    # Move to password field, click, type
                    await cursor.type_into('input[name="session_password"]', password)
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                    # Move to login button and click naturally
                    await cursor.click_element('button[type="submit"]')

                    # Wait for navigation or 2FA
                    # Use 'load' instead of 'networkidle' — LinkedIn has persistent connections
                    await page.wait_for_load_state('load', timeout=15000)
                    await asyncio.sleep(2)  # Additional wait for dynamic content

                    # Check for 2FA challenge
                    if await self._is_2fa_required(page):
                        if not verification_code:
                            # Save browser state for resuming
                            state = await self._serialize_browser_state(sb.context)

                            return {
                                'status': '2fa_required',
                                'verification_state': state,
                                'message': 'Please enter the verification code sent to your device'
                            }
                        else:
                            # Submit 2FA code
                            await self._submit_2fa_code(page, verification_code)
                            await page.wait_for_load_state('load', timeout=15000)
                            await asyncio.sleep(2)

                    # Check if login successful
                    if not await self._is_logged_in(page):
                        return {
                            'status': 'error',
                            'error': 'Invalid credentials or login failed. Please check your email and password.'
                        }

                    # Extract cookies
                    cookies = await sb.context.cookies()
                    linkedin_cookies = self._extract_linkedin_cookies(cookies)

                    # Verify we have required cookies
                    if not linkedin_cookies.get('li_at'):
                        return {
                            'status': 'error',
                            'error': 'Failed to extract authentication cookies'
                        }

                    return {
                        'status': 'connected',
                        'cookies': linkedin_cookies,
                        'message': 'Successfully authenticated with LinkedIn'
                    }

                except Exception as e:
                    return {
                        'status': 'error',
                        'error': f'Login failed: {str(e)}'
                    }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Browser error: {str(e)}'
            }

    async def _resume_2fa_flow(
        self,
        context: BrowserContext,
        page: Page,
        state: Dict[str, Any],
        verification_code: str
    ) -> Dict[str, Any]:
        """Resume 2FA flow with saved browser state."""
        try:
            # Restore cookies from state
            if state.get('cookies'):
                await context.add_cookies(state['cookies'])

            # Navigate to LinkedIn
            await page.goto('https://www.linkedin.com/checkpoint/challenge/', wait_until='load')
            await asyncio.sleep(1)

            # Submit 2FA code
            await self._submit_2fa_code(page, verification_code)
            await page.wait_for_load_state('load', timeout=15000)
            await asyncio.sleep(2)

            # Check if successful
            if await self._is_logged_in(page):
                cookies = await context.cookies()
                linkedin_cookies = self._extract_linkedin_cookies(cookies)

                return {
                    'status': 'connected',
                    'cookies': linkedin_cookies,
                    'message': 'Successfully authenticated with 2FA'
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Invalid verification code'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'2FA verification failed: {str(e)}'
            }

    async def _is_2fa_required(self, page: Page) -> bool:
        """Check if 2FA challenge is present."""
        selectors = [
            'input[name="pin"]',
            'input[id="verification-code"]',
            'input[id="input__email_verification_pin"]',
            'text="Enter the verification code"',
            'text="Let\'s verify your identity"'
        ]

        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    return True
            except:
                continue

        return False

    async def _submit_2fa_code(self, page: Page, code: str) -> None:
        """Submit 2FA verification code using ghost cursor."""
        cursor = GhostCursor(page)

        # Try different input selectors
        selectors = [
            'input[name="pin"]',
            'input[id="verification-code"]',
            'input[id="input__email_verification_pin"]'
        ]

        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    # Move to 2FA input, click, type the code naturally
                    await cursor.type_into(selector, code)
                    await asyncio.sleep(random.uniform(0.3, 0.8))

                    # Click submit button naturally
                    submit_selectors = [
                        'button[type="submit"]',
                        'button:has-text("Submit")',
                        'button:has-text("Verify")'
                    ]

                    for submit_selector in submit_selectors:
                        try:
                            submit_count = await page.locator(submit_selector).count()
                            if submit_count > 0:
                                await cursor.click_element(submit_selector)
                                return
                        except:
                            continue
                    return
            except:
                continue

        raise Exception("Could not find 2FA code input field")

    async def _is_logged_in(self, page: Page) -> bool:
        """Check if successfully logged in."""
        url = page.url

        # Success indicators
        success_paths = ['/feed', '/mynetwork', '/messaging', '/in/']
        for path in success_paths:
            if path in url:
                return True

        # Also check if checkpoint/challenge page is gone
        if '/checkpoint/challenge' not in url and '/login' not in url:
            # Verify by checking for LinkedIn nav elements
            try:
                nav_count = await page.locator('nav.global-nav').count()
                return nav_count > 0
            except:
                pass

        return False

    def _extract_linkedin_cookies(self, cookies: list) -> Dict[str, Any]:
        """Extract and format LinkedIn cookies."""
        required = ['li_at', 'JSESSIONID', 'bcookie', 'bscookie']
        result = {}

        for cookie in cookies:
            if cookie['name'] in required or cookie['name'].startswith('li_'):
                result[cookie['name']] = {
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path'],
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False),
                    'expirationDate': cookie.get('expires', None)
                }

        return result

    async def _serialize_browser_state(self, context: BrowserContext) -> Dict[str, Any]:
        """Serialize browser state for resuming 2FA."""
        cookies = await context.cookies()
        return {
            'cookies': cookies,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
