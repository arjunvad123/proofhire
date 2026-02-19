"""
LinkedIn credential authentication service.

Handles:
- Direct login with email/password
- 2FA code handling
- Cookie extraction
- Residential proxy usage
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

from .encryption import CookieEncryption
from .human_behavior import HumanBehaviorEngine


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
        user_location: Optional[str] = None,
        verification_code: Optional[str] = None,
        resume_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate and extract cookies.

        Args:
            email: LinkedIn email
            password: LinkedIn password
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
            # Get proxy if location provided
            proxy = self._get_proxy_for_location(user_location) if user_location else None

            async with async_playwright() as p:
                # Launch browser (NOT headless - appears more legitimate)
                browser = await p.chromium.launch(
                    headless=False,
                    proxy=proxy
                )

                # Create context with realistic settings
                context = await browser.new_context(
                    user_agent=self._get_realistic_user_agent(),
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/Los_Angeles'
                )

                page = await context.new_page()

                # Apply stealth to avoid detection
                await Stealth().apply_stealth_async(page)

                try:
                    # If resuming 2FA flow
                    if resume_state and verification_code:
                        result = await self._resume_2fa_flow(
                            context, page, resume_state, verification_code
                        )
                        await browser.close()
                        return result

                    # Navigate to login page
                    await page.goto(
                        'https://www.linkedin.com/login',
                        wait_until='networkidle',
                        timeout=30000
                    )

                    # Fill credentials with human-like delays
                    await page.fill('input[name="session_key"]', email)
                    await asyncio.sleep(random.uniform(0.3, 0.8))

                    await page.fill('input[name="session_password"]', password)
                    await asyncio.sleep(random.uniform(0.2, 0.5))

                    # Click login button
                    await page.click('button[type="submit"]')

                    # Wait for navigation or 2FA
                    # Use 'load' instead of 'networkidle' - LinkedIn has persistent connections
                    await page.wait_for_load_state('load', timeout=15000)
                    await asyncio.sleep(2)  # Additional wait for dynamic content

                    # Check for 2FA challenge
                    if await self._is_2fa_required(page):
                        if not verification_code:
                            # Save browser state for resuming
                            state = await self._serialize_browser_state(context)
                            await browser.close()

                            return {
                                'status': '2fa_required',
                                'verification_state': state,
                                'message': 'Please enter the verification code sent to your device'
                            }
                        else:
                            # Submit 2FA code
                            await self._submit_2fa_code(page, verification_code)
                            await page.wait_for_load_state('load', timeout=15000)
                            await asyncio.sleep(2)  # Additional wait for dynamic content

                    # Check if login successful
                    if not await self._is_logged_in(page):
                        return {
                            'status': 'error',
                            'error': 'Invalid credentials or login failed. Please check your email and password.'
                        }

                    # Extract cookies
                    cookies = await context.cookies()
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
                finally:
                    await browser.close()

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
        """Submit 2FA verification code."""
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
                    await page.fill(selector, code)
                    await asyncio.sleep(0.5)

                    # Click submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'button:has-text("Submit")',
                        'button:has-text("Verify")'
                    ]

                    for submit_selector in submit_selectors:
                        try:
                            submit_count = await page.locator(submit_selector).count()
                            if submit_count > 0:
                                await page.click(submit_selector)
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

    def _get_proxy_for_location(self, location: Optional[str]) -> Optional[Dict[str, str]]:
        """Get residential proxy for user's location."""
        # TODO: Implement actual proxy selection based on location
        # For now, return None (no proxy)
        # In production, integrate with Smartproxy or Bright Data
        return None

    def _get_realistic_user_agent(self) -> str:
        """Get realistic user agent string."""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        return random.choice(user_agents)
