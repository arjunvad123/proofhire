"""
LinkedIn credential authentication service.

Handles:
- Direct login with email/password
- "Welcome Back" remembered account flow
- 2FA code handling
- Cookie extraction
- Residential proxy usage

Uses an adaptive state-machine approach to handle LinkedIn's varying login flows:
1. Detect current page state (login form, welcome back, 2FA, logged in, etc.)
2. Take appropriate action based on state
3. Repeat until logged in or error

Uses StealthBrowser for context-level stealth + extra evasion scripts.
"""

import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import BrowserContext, Page

from .encryption import CookieEncryption
from .human_behavior import HumanBehaviorEngine, GhostCursor
from .stealth_browser import StealthBrowser
from .account_manager import AccountManager

logger = logging.getLogger(__name__)


class LoginState:
    """Possible states during LinkedIn login flow."""
    UNKNOWN = "unknown"
    LOGIN_FORM = "login_form"           # Standard email/password form
    WELCOME_BACK = "welcome_back"        # Remembered account selector
    PASSWORD_ONLY = "password_only"      # Only password needed (email remembered)
    TWO_FA = "2fa"                       # 2FA verification required
    CHECKPOINT = "checkpoint"            # Security checkpoint
    LOGGED_IN = "logged_in"              # Successfully logged in
    ERROR = "error"                      # Login error/captcha


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
        Authenticate and extract cookies using adaptive state-machine approach.

        LinkedIn's login flow varies - sometimes showing:
        - Standard email/password form
        - "Welcome Back" remembered account selector
        - Password-only form (email pre-filled)
        - 2FA challenges
        - Security checkpoints

        This method detects the current state and takes appropriate action,
        looping until logged in or an error occurs.

        Args:
            email: LinkedIn email
            password: LinkedIn password
            user_id: If provided, uses a persistent browser profile keyed to this
                     user so LinkedIn recognises the same "device" across logins.
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
            # Use a persistent browser profile keyed to the EMAIL (not user_id)
            # This ensures each LinkedIn account gets its own isolated browser profile
            # The email hash guarantees no cross-account cookie pollution
            if email:
                profile_id = AccountManager.get_profile_id(email)
                browser_ctx = StealthBrowser.launch_persistent(
                    session_id=profile_id,
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
                        return await self._resume_2fa_flow(
                            sb.context, page, resume_state, verification_code
                        )

                    # Navigate to login page
                    await page.goto(
                        'https://www.linkedin.com/login',
                        wait_until='load',
                        timeout=30000
                    )
                    await asyncio.sleep(2)

                    # State machine loop - handle whatever LinkedIn throws at us
                    max_iterations = 10  # Prevent infinite loops
                    for iteration in range(max_iterations):
                        state = await self._detect_login_state(page, email)
                        logger.info(f"Login iteration {iteration + 1}: state={state}")

                        if state == LoginState.LOGGED_IN:
                            # Success! Extract cookies
                            cookies = await sb.context.cookies()
                            linkedin_cookies = self._extract_linkedin_cookies(cookies)
                            if linkedin_cookies.get('li_at'):
                                return {
                                    'status': 'connected',
                                    'cookies': linkedin_cookies,
                                    'message': 'Successfully authenticated with LinkedIn'
                                }
                            else:
                                return {
                                    'status': 'error',
                                    'error': 'Logged in but failed to extract cookies'
                                }

                        elif state == LoginState.TWO_FA:
                            if verification_code:
                                await self._submit_2fa_code(page, verification_code)
                                await page.wait_for_load_state('load', timeout=15000)
                                await asyncio.sleep(2)
                                continue  # Check state again
                            else:
                                # Need to ask user for 2FA code
                                browser_state = await self._serialize_browser_state(sb.context)
                                return {
                                    'status': '2fa_required',
                                    'verification_state': browser_state,
                                    'message': 'Please enter the verification code sent to your device'
                                }

                        elif state == LoginState.WELCOME_BACK:
                            clicked = await self._handle_welcome_back(page, email)
                            if clicked:
                                await page.wait_for_load_state('load', timeout=15000)
                                await asyncio.sleep(2)
                                continue  # Check state again
                            else:
                                # Couldn't click account, try "Sign in using another account"
                                await self._click_sign_in_another_account(page)
                                await asyncio.sleep(2)
                                continue

                        elif state == LoginState.LOGIN_FORM:
                            await self._fill_login_form(page, email, password)
                            await page.wait_for_load_state('load', timeout=15000)
                            await asyncio.sleep(2)
                            continue  # Check state again

                        elif state == LoginState.PASSWORD_ONLY:
                            await self._fill_password_only(page, password)
                            await page.wait_for_load_state('load', timeout=15000)
                            await asyncio.sleep(2)
                            continue  # Check state again

                        elif state == LoginState.CHECKPOINT:
                            # Security checkpoint - wait for user to complete in browser
                            # This is normal for new devices - LinkedIn requires human verification
                            logger.info("Checkpoint detected - waiting for user to complete verification")

                            # Wait up to 5 minutes for user to complete checkpoint
                            checkpoint_timeout = 300  # 5 minutes
                            start_time = asyncio.get_event_loop().time()

                            while (asyncio.get_event_loop().time() - start_time) < checkpoint_timeout:
                                await asyncio.sleep(3)
                                new_state = await self._detect_login_state(page, email)

                                if new_state == LoginState.LOGGED_IN:
                                    # User completed checkpoint!
                                    logger.info("User completed checkpoint successfully")
                                    break
                                elif new_state == LoginState.CHECKPOINT:
                                    # Still on checkpoint, keep waiting
                                    continue
                                elif new_state == LoginState.TWO_FA:
                                    # Moved to 2FA after checkpoint
                                    state = new_state
                                    break
                                else:
                                    # State changed to something else
                                    state = new_state
                                    break
                            else:
                                # Timeout - user didn't complete in time
                                return {
                                    'status': 'checkpoint_required',
                                    'error': 'Security checkpoint requires verification. Please complete in browser.',
                                    'message': 'LinkedIn requires additional verification for this device. Please complete the security check in the browser window.'
                                }
                            continue  # Re-check state after checkpoint

                        elif state == LoginState.ERROR:
                            return {
                                'status': 'error',
                                'error': 'Login error detected. Invalid credentials or account locked.'
                            }

                        else:
                            # Unknown state - wait and try again
                            await asyncio.sleep(2)
                            continue

                    # Max iterations reached
                    return {
                        'status': 'error',
                        'error': 'Login flow did not complete. Please try again.'
                    }

                except Exception as e:
                    logger.exception("Login failed")
                    return {
                        'status': 'error',
                        'error': f'Login failed: {str(e)}'
                    }

        except Exception as e:
            logger.exception("Browser error")
            return {
                'status': 'error',
                'error': f'Browser error: {str(e)}'
            }

    async def _detect_login_state(self, page: Page, email: str) -> str:
        """
        Detect the current state of the login flow.

        Returns one of the LoginState constants.
        """
        url = page.url

        # Check if already logged in
        if await self._is_logged_in(page):
            return LoginState.LOGGED_IN

        # Check URL-based states
        if '/checkpoint' in url:
            if await self._is_2fa_required(page):
                return LoginState.TWO_FA
            return LoginState.CHECKPOINT

        # Check for 2FA (can appear on various URLs)
        if await self._is_2fa_required(page):
            return LoginState.TWO_FA

        # Check for login error messages
        error_selectors = [
            'text="Wrong email or password"',
            'text="Please enter a valid email"',
            'text="Incorrect password"',
            'text="account has been restricted"',
            '[data-error="true"]',
        ]
        for selector in error_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    return LoginState.ERROR
            except:
                pass

        # Check for login/password forms FIRST — these take priority over
        # "Welcome Back" text since clicking the Welcome Back card leads to
        # a password form that may still contain "Welcome Back" text.

        # Check for standard login form
        try:
            email_input = await page.locator('input[name="session_key"]').count()
            password_input = await page.locator('input[name="session_password"]').count()
            if email_input > 0 and password_input > 0:
                return LoginState.LOGIN_FORM
        except:
            pass

        # Check for password-only form (email pre-filled or remembered)
        try:
            password_only = await page.locator('input[type="password"]').count()
            if password_only > 0:
                return LoginState.PASSWORD_ONLY
        except:
            pass

        # Check for "Welcome Back" account selector (only if no form inputs found)
        try:
            welcome_back = await page.locator('text="Welcome Back"').count()
            has_account_card = await page.locator('text=/[a-z]\\*+@/i').count()  # Masked email
            if welcome_back > 0 or has_account_card > 0:
                return LoginState.WELCOME_BACK
        except:
            pass

        return LoginState.UNKNOWN

    async def _handle_welcome_back(self, page: Page, email: str) -> bool:
        """
        Handle the 'Welcome Back' account selector screen.

        Clicks on the remembered account card.
        Returns True if clicked successfully.
        """
        cursor = GhostCursor(page)

        try:
            # Try to find the account card with masked email
            # LinkedIn shows emails like "a*****@ucsd.edu"
            masked_email_locator = page.locator('text=/[a-z]\\*+@/i')
            if await masked_email_locator.count() > 0:
                # Click the parent container (the card)
                card = masked_email_locator.first.locator('xpath=ancestor::div[contains(@class, "card") or @role="button" or contains(@class, "account")]').first
                try:
                    await card.click()
                    return True
                except:
                    # Fallback: click directly on the masked email text
                    await masked_email_locator.first.click()
                    return True
        except Exception as e:
            logger.debug(f"Could not click masked email: {e}")

        # Try other selectors for the account card
        selectors = [
            'div[role="button"]:has-text("@")',
            'button:has-text("@")',
            'a:has-text("@")',
        ]

        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await cursor.click_element(selector)
                    return True
            except:
                continue

        return False

    async def _click_sign_in_another_account(self, page: Page) -> bool:
        """Click 'Sign in using another account' link."""
        selectors = [
            'text="Sign in using another account"',
            'text="Use another account"',
            'a:has-text("another account")',
        ]

        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.locator(selector).click()
                    return True
            except:
                continue

        return False

    async def _fill_login_form(self, page: Page, email: str, password: str) -> None:
        """Fill the standard email/password login form."""
        cursor = GhostCursor(page)

        # Clear and fill email
        await cursor.type_into('input[name="session_key"]', email)
        await asyncio.sleep(random.uniform(0.3, 0.8))

        # Clear and fill password
        await cursor.type_into('input[name="session_password"]', password)
        await asyncio.sleep(random.uniform(0.2, 0.5))

        # Click submit
        await cursor.click_element('button[type="submit"]')

    async def _fill_password_only(self, page: Page, password: str) -> None:
        """Fill password when email is already pre-filled."""
        cursor = GhostCursor(page)

        # Find and fill password field
        password_selectors = [
            'input[name="session_password"]',
            'input[type="password"]',
            'input[id*="password"]',
        ]

        for selector in password_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await cursor.type_into(selector, password)
                    await asyncio.sleep(random.uniform(0.2, 0.5))
                    break
            except:
                continue

        # Click submit
        submit_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Continue")',
        ]

        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await cursor.click_element(selector)
                    return
            except:
                continue

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
