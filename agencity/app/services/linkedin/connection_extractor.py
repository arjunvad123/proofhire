"""
LinkedIn connection extraction service (Phase 2).

Implements Comet-style extraction with human-like behavior:
- Natural navigation chain (feed → mynetwork → connections)
- Gradual scrolling with natural delays
- Realistic reading patterns
- Respects rate limits
- Session management
- Idle/distraction patterns (phone checks, thinking pauses)
- Warmup mode for new accounts
- Card inspection simulation

Uses StealthBrowser for context-level stealth + extra evasion scripts.
"""

import asyncio
import os
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from playwright.async_api import Page, BrowserContext

from .human_behavior import (
    HumanBehaviorEngine,
    GhostCursor,
    GhostCursorIntegration,
    IdlePatternGenerator,
    ExtractionConfig,
    ExtractionMode,
)
from .session_manager import LinkedInSessionManager
from .stealth_browser import StealthBrowser
from .warning_detection import check_and_handle_warnings

logger = logging.getLogger(__name__)


class LinkedInConnectionExtractor:
    """Extract LinkedIn connections with human-like behavior."""

    # LinkedIn loads approximately 50 connections per scroll
    CONNECTIONS_PER_SCROLL = 50

    # Default scroll delays (seconds) - hardened values
    # These are overridden by ExtractionConfig when in cautious mode
    MIN_SCROLL_DELAY = 3.0
    MAX_SCROLL_DELAY = 7.0

    # Reading pause - simulate actually looking at connections
    MIN_READ_PAUSE = 1.5
    MAX_READ_PAUSE = 4.5

    # Back-scroll chance (increased from 15% to 20-25%)
    BACK_SCROLL_CHANCE = 0.22

    # Card inspection chance
    CARD_INSPECTION_CHANCE = 0.10

    def __init__(
        self,
        session_manager: LinkedInSessionManager,
        cautious_mode: bool = False,
        use_proxy: bool = True,
    ):
        """
        Initialize extractor.

        Args:
            session_manager: Session manager for cookie handling
            cautious_mode: Use extra-safe timing for new accounts
            use_proxy: Whether to use residential proxy (disable for local testing)
        """
        self.session_manager = session_manager
        self.use_proxy = use_proxy
        self.behavior = HumanBehaviorEngine()

        # Determine extraction mode from parameter or environment
        env_cautious = os.environ.get('LINKEDIN_CAUTIOUS_MODE', '').lower() in ('1', 'true', 'yes')
        self.cautious_mode = cautious_mode or env_cautious

        # Load appropriate configuration
        mode = ExtractionMode.CAUTIOUS if self.cautious_mode else ExtractionMode.NORMAL
        self.config = ExtractionConfig.from_mode(mode)

        # Initialize idle pattern generator
        self.idle_generator = IdlePatternGenerator(
            frequency_multiplier=self.config.idle_frequency_multiplier
        )

        # Apply config values to instance
        self.MIN_SCROLL_DELAY = self.config.scroll_delay_min
        self.MAX_SCROLL_DELAY = self.config.scroll_delay_max
        self.MIN_READ_PAUSE = self.config.read_pause_min
        self.MAX_READ_PAUSE = self.config.read_pause_max
        self.BACK_SCROLL_CHANCE = self.config.back_scroll_chance
        self.CARD_INSPECTION_CHANCE = self.config.card_inspection_chance

        logger.info(
            f"Extractor initialized: mode={'CAUTIOUS' if self.cautious_mode else 'NORMAL'}, "
            f"scroll_delay={self.MIN_SCROLL_DELAY}-{self.MAX_SCROLL_DELAY}s, "
            f"warmup_connections={self.config.warmup_connections}"
        )

    async def extract_connections(
        self,
        session_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Extract all connections from LinkedIn.

        Uses StealthBrowser with persistent profile + natural navigation chain
        to avoid LinkedIn's server-side session invalidation.

        Args:
            session_id: LinkedIn session ID
            progress_callback: Optional callback(connections_found, total_estimated)

        Returns:
            {
                'status': 'success' | 'error',
                'connections': [...],
                'total': int,
                'duration_seconds': float,
                'error': str (if error)
            }
        """
        start_time = datetime.now()

        try:
            # Get session cookies
            cookies = await self.session_manager.get_session_cookies(session_id)
            if not cookies:
                return {
                    'status': 'error',
                    'error': 'Session not found or expired'
                }

            # Get session info
            session = await self.session_manager.get_session(session_id)
            user_location = session.get('user_location') if self.use_proxy else None

            # Use the email-hashed profile_id so we share the same browser
            # profile that was used during authentication. This is critical —
            # LinkedIn ties session validity to the browser profile/fingerprint.
            browser_profile_id = session.get('profile_id') or session_id
            logger.info(f"Using browser profile: {browser_profile_id}")

            async with StealthBrowser.launch_persistent(
                session_id=browser_profile_id,
                headless=False,
                user_location=user_location,
            ) as sb:
                # Use the persistent profile's cookies as-is.
                # The credential_auth already logged in using this same
                # profile, so all necessary cookies (li_at, JSESSIONID,
                # bcookie, bscookie, and ~25 tracking/analytics cookies)
                # are already present and valid.
                #
                # DO NOT clear and re-inject! LinkedIn expects all the
                # cookies set during browsing, not just the 7 we store.
                current_cookies = await sb.context.cookies()
                has_li_at = any(c['name'] == 'li_at' for c in current_cookies)
                logger.info(f"Browser profile cookies: {len(current_cookies)}, li_at: {has_li_at}")

                if not has_li_at:
                    # Profile has no li_at at all — inject from session
                    logger.warning("Profile missing li_at — injecting session cookies")
                    await self._add_session_cookies(sb.context, cookies)
                    after_cookies = await sb.context.cookies()
                    logger.info(f"After injection: {len(after_cookies)} cookies")

                page = await sb.new_page()

                try:
                    # Start behavior session
                    self.behavior.start_session()

                    # ── Natural navigation chain ──
                    # Instead of jumping straight to /connections (which LinkedIn
                    # detects as suspicious), walk through the natural page flow
                    # like a real user would.
                    navigated = await self._navigate_to_connections_naturally(page, cookies)
                    if not navigated:
                        return {
                            'status': 'error',
                            'error': 'Session expired or invalid — could not reach connections page'
                        }

                    # Wait for React to render and connections to appear
                    await self._wait_for_connections_to_load(page)

                    # Verify we're logged in (not redirected)
                    if not await self._is_logged_in(page):
                        return {
                            'status': 'error',
                            'error': 'Session expired or invalid'
                        }

                    # Check for warnings before starting extraction
                    await check_and_handle_warnings(
                        page, session_id, self.session_manager, raise_on_warning=True
                    )

                    # Extract connections with human-like scrolling
                    connections = await self._extract_all_connections(
                        page, session_id, progress_callback
                    )

                    # Record activity
                    await self.session_manager.record_activity(
                        session_id,
                        'extraction',
                        len(connections)
                    )

                    duration = (datetime.now() - start_time).total_seconds()

                    return {
                        'status': 'success',
                        'connections': connections,
                        'total': len(connections),
                        'duration_seconds': duration
                    }

                finally:
                    # StealthBrowser context manager handles cleanup
                    pass

        except Exception as e:
            logger.exception("Connection extraction failed")
            return {
                'status': 'error',
                'error': f'Extraction failed: {str(e)}'
            }

    # ──────────────────────────────────────────────────────────────────────
    # Natural navigation chain
    # ──────────────────────────────────────────────────────────────────────

    async def _navigate_to_connections_naturally(self, page: Page, cookies: Dict[str, Any] = None) -> bool:
        """
        Navigate from feed → mynetwork → connections with realistic delays.

        LinkedIn validates the Referer header and navigation chain. Jumping
        directly to /connections/ from a blank tab is flagged as automation.
        Walking through the normal UI flow avoids this.

        Args:
            page: Playwright page

        Returns:
            True if we successfully reached the connections page while logged in.
        """
        try:
            # Step 1: Go to feed (the "homepage" a real user always lands on)
            logger.info("Navigation chain: step 1 — loading feed")
            await page.goto(
                'https://www.linkedin.com/feed/',
                wait_until='load',
                timeout=30000
            )
            await asyncio.sleep(random.uniform(2.0, 4.0))

            logger.info(f"After feed navigation, URL: {page.url}")

            # Quick check: are we logged in?
            if not await self._is_logged_in(page):
                logger.warning(f"Not logged in after feed navigation — URL: {page.url}")
                await page.screenshot(path='debug_nav_feed_fail.png')
                return False

            # Simulate reading the feed briefly (scroll a bit, pause)
            await self._simulate_feed_browsing(page)

            # Step 2: Click "My Network" in the top nav
            logger.info("Navigation chain: step 2 — clicking My Network")

            # Scroll back to top so the nav bar is visible
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(random.uniform(0.3, 0.6))

            # Try up to 2 times — the first click sometimes misses
            for attempt in range(2):
                if '/mynetwork' in page.url:
                    break
                clicked = await self._click_nav_link(page, 'mynetwork')
                if clicked:
                    break
                logger.info(f"My Network click attempt {attempt + 1} failed, URL: {page.url}")

                # If we ended up at homepage (/) — still authenticated,
                # retry from here
                if page.url.rstrip('/') == 'https://www.linkedin.com':
                    await page.evaluate('window.scrollTo(0, 0)')
                    await asyncio.sleep(1.0)

            await asyncio.sleep(random.uniform(1.5, 3.5))
            logger.info(f"After mynetwork navigation, URL: {page.url}")

            # Check if we're still on an authenticated page
            if not await self._is_logged_in(page):
                logger.warning(f"Not logged in after My Network — URL: {page.url}")
                handled = await self._handle_login_redirect(page, cookies)
                if not handled:
                    await page.screenshot(path='debug_nav_mynetwork_fail.png')
                    return False

            # Step 3: Navigate to Connections page
            logger.info("Navigation chain: step 3 — navigating to Connections")

            # If we're on /mynetwork/, look for a "Connections" link to click
            if '/mynetwork' in page.url:
                clicked = await self._click_connections_link(page)

            # If not on connections yet, try SPA-style navigation first
            if '/connections' not in page.url:
                logger.info(f"Trying SPA navigation to connections from {page.url}")
                # Use the My Network nav click to get to connections
                spa_success = await self._click_nav_link(page, 'mynetwork/invite-connect/connections')
                if not spa_success:
                    # page.goto as last resort
                    logger.info("SPA nav failed, using page.goto to connections")
                    await page.goto(
                        'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                        wait_until='load',
                        timeout=30000
                    )

            await asyncio.sleep(random.uniform(1.5, 3.0))
            logger.info(f"After connections navigation, URL: {page.url}")

            if not await self._is_logged_in(page):
                logger.warning(f"Not logged in after Connections — URL: {page.url}")
                handled = await self._handle_login_redirect(page, cookies)
                if not handled:
                    await page.screenshot(path='debug_nav_connections_fail.png')
                    return False

            logger.info("Navigation chain: successfully reached connections page")
            return True

        except Exception as e:
            logger.error(f"Navigation chain failed: {e}")
            try:
                await page.screenshot(path='debug_nav_exception.png')
            except Exception:
                pass
            return False

    async def _simulate_feed_browsing(self, page: Page) -> None:
        """
        Briefly browse the feed to build a realistic session history.

        A real user spends 5-15 seconds on the feed before navigating away.
        Uses mouse-wheel scrolling (not window.scrollBy) to avoid detection.
        """
        cursor = GhostCursor(page)

        # Small scroll (read a post or two) — via mouse wheel
        await cursor.scroll(random.randint(300, 600))

        # Pause as if reading
        await asyncio.sleep(random.uniform(2.0, 5.0))

        # Occasionally scroll back up
        if random.random() < 0.3:
            await cursor.scroll(-150)
            await asyncio.sleep(random.uniform(0.5, 1.0))

    async def _click_nav_link(self, page: Page, target: str) -> bool:
        """
        Click a link in LinkedIn's top navigation bar.

        Strategy:
        1. First try GhostCursor click on the specific nav element
        2. If that misses (nav bar elements are tricky due to fixed positioning),
           fall back to Playwright's native click
        3. As last resort, use page.evaluate to programmatically click

        LinkedIn uses SPA-style client-side navigation, so we wait for URL
        change rather than a full page load event.

        Args:
            page: Playwright page
            target: URL substring to match (e.g. 'mynetwork', 'messaging')

        Returns:
            True if navigation succeeded (URL contains target)
        """
        selector = f'a[href*="/{target}"]'

        # Dump nav links for debugging
        try:
            nav_info = await page.evaluate(r'''(target) => {
                const links = document.querySelectorAll('a[href*="/' + target + '"]');
                return Array.from(links).map(a => ({
                    href: a.href,
                    text: a.textContent?.trim().substring(0, 50),
                    visible: a.offsetParent !== null,
                    rect: a.getBoundingClientRect().toJSON(),
                }));
            }''', target)
            logger.info(f"Found {len(nav_info)} links matching '/{target}': {nav_info}")
        except Exception as e:
            logger.debug(f"Could not dump nav info: {e}")

        locator = page.locator(selector).first
        count = await page.locator(selector).count()
        if count == 0:
            logger.info(f"No links found matching '{selector}'")
            return False

        # Check bounding box
        box = await locator.bounding_box(timeout=3000)
        if not box:
            logger.info(f"Nav link has no bounding box (hidden)")
            return False

        logger.info(f"Nav link box: x={box['x']:.0f}, y={box['y']:.0f}, "
                   f"w={box['width']:.0f}, h={box['height']:.0f}")

        before_url = page.url

        # Attempt 1: GhostCursor click (most human-like)
        # First move the cursor near the target, THEN click the element.
        # This avoids the Bezier path from (0,0) crossing other nav elements.
        try:
            logger.info("Attempt 1: GhostCursor click on nav link")
            cursor = GhostCursor(page)

            # Pre-position cursor near the element (below and slightly left)
            # to avoid the Bezier path crossing the LinkedIn logo
            near_x = box['x'] + box['width'] * 0.5
            near_y = box['y'] + box['height'] + 50  # Below the nav bar
            await cursor.move_to(near_x, near_y, duration=0.3)
            await asyncio.sleep(random.uniform(0.1, 0.3))

            # Now click the element — short path, less chance of missing
            await cursor.click_element(selector)

            # Wait for SPA navigation to complete — LinkedIn can take several seconds
            try:
                await page.wait_for_url(f'**/{target}/**', timeout=10000)
            except Exception:
                pass
            await asyncio.sleep(1.0)

            if f'/{target}' in page.url:
                logger.info(f"  GhostCursor click succeeded — URL: {page.url}")
                return True
            logger.info(f"  GhostCursor click missed — URL: {page.url}")
        except asyncio.TimeoutError:
            logger.warning("  GhostCursor click timed out")
        except Exception as e:
            logger.debug(f"  GhostCursor click error: {e}")

        # Attempt 2: Re-fetch bounding box on current page and try mouse click
        # DO NOT navigate back to feed — page.goto breaks SPA session state.
        # Instead, retry the click from whatever page we're on now.
        try:
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)

            # Re-fetch bounding box on current page
            locator = page.locator(selector).first
            if await page.locator(selector).count() > 0:
                box = await locator.bounding_box(timeout=3000)
                if box:
                    cx = box['x'] + box['width'] / 2
                    cy = box['y'] + box['height'] / 2
                    logger.info(f"Attempt 2: page.mouse.click at ({cx:.0f}, {cy:.0f})")
                    await page.mouse.click(cx, cy)

                    # Poll for URL change
                    for i in range(20):  # 10 seconds
                        await asyncio.sleep(0.5)
                        if f'/{target}' in page.url:
                            logger.info(f"  Mouse click succeeded — URL: {page.url}")
                            try:
                                await page.wait_for_load_state('load', timeout=10000)
                            except Exception:
                                pass
                            return True

                    logger.info(f"  Mouse click did not reach /{target} — URL: {page.url}")
        except Exception as e:
            logger.warning(f"  Mouse click failed: {e}")

        return False

    async def _click_connections_link(self, page: Page) -> bool:
        """
        Click a 'Connections' link on the My Network page.

        LinkedIn's My Network page (/mynetwork/ or /mynetwork/grow/) shows
        connection management options. We need to find and click the link
        to the connections list.
        """
        # First, log what connection-related links exist on this page
        try:
            conn_links = await page.evaluate(r'''() => {
                const links = document.querySelectorAll('a[href*="connection"]');
                return Array.from(links).map(a => ({
                    href: a.href,
                    text: a.textContent?.trim().substring(0, 80),
                    visible: a.offsetParent !== null,
                }));
            }''')
            logger.info(f"Connection-related links on page: {conn_links}")
        except Exception:
            pass

        selectors = [
            'a[href*="/invite-connect/connections"]',
            'a[href*="/mynetwork/invite-connect/connections"]',
            'a[href*="connections"]',
        ]

        for selector in selectors:
            try:
                locator = page.locator(selector).first
                count = await page.locator(selector).count()
                if count == 0:
                    continue

                logger.info(f"Trying connections selector '{selector}' ({count} matches)")

                box = await locator.bounding_box(timeout=3000)
                if not box:
                    logger.info(f"  No bounding box for '{selector}'")
                    continue

                before_url = page.url
                try:
                    await asyncio.wait_for(
                        GhostCursorIntegration.click_naturally(page, selector),
                        timeout=10.0
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"  GhostCursor click timed out for '{selector}'")
                    # Try native click as immediate fallback
                    try:
                        await locator.click(timeout=5000)
                    except Exception:
                        continue

                try:
                    await page.wait_for_url('**/connections/**', timeout=8000)
                except Exception:
                    pass

                await asyncio.sleep(0.5)

                if '/connections' in page.url:
                    logger.info(f"  Connections click succeeded — navigated to {page.url}")
                    return True

                logger.info(f"  Click on '{selector}' did not reach connections (at {page.url})")

            except Exception as e:
                logger.debug(f"  Selector '{selector}' failed: {e}")
                continue

        # Final fallback: try native Playwright click
        try:
            locator = page.locator('a[href*="connections"]').first
            if await locator.count() > 0:
                logger.info("Trying native click on first connections link")
                await locator.click(timeout=5000)
                await asyncio.sleep(1.0)
                if '/connections' in page.url:
                    return True
        except Exception:
            pass

        return False

    async def _handle_login_redirect(self, page: Page, cookies: Dict[str, Any] = None) -> bool:
        """
        Handle a login redirect by re-injecting cookies and navigating to feed.

        LinkedIn sometimes redirects to a login page when navigating via
        page.goto() even though the session is valid. This happens because
        page.goto() does a full page navigation which doesn't carry the SPA
        state. The solution is to re-inject cookies and navigate to a known
        working page (/feed/).

        Returns True if we successfully got past the login page.
        """
        try:
            url = page.url
            logger.info(f"Handling login redirect at: {url}")

            # Strategy 1: Try navigating to /feed/ — if cookies are valid in
            # the browser profile, this should work
            logger.info("Attempting to navigate back to /feed/")
            await page.goto(
                'https://www.linkedin.com/feed/',
                wait_until='load',
                timeout=15000
            )
            await asyncio.sleep(2)

            if await self._is_logged_in(page):
                logger.info(f"  Feed navigation worked — now at: {page.url}")
                return True

            # Strategy 2: Re-inject cookies and try again
            if cookies:
                logger.info("Re-injecting cookies and trying feed again")
                context = page.context
                # Clear LinkedIn cookies
                current_cookies = await context.cookies()
                linkedin_domains = {'.linkedin.com', '.www.linkedin.com'}
                non_li = [c for c in current_cookies if c.get('domain', '') not in linkedin_domains]
                await context.clear_cookies()
                if non_li:
                    await context.add_cookies(non_li)
                await self._add_session_cookies(context, cookies)

                await page.goto(
                    'https://www.linkedin.com/feed/',
                    wait_until='load',
                    timeout=15000
                )
                await asyncio.sleep(2)

                if await self._is_logged_in(page):
                    logger.info(f"  Cookie re-injection worked — now at: {page.url}")
                    return True

            logger.warning("Could not handle login redirect automatically")
            return False

        except Exception as e:
            logger.error(f"Error handling login redirect: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────
    # Connection extraction (unchanged core logic)
    # ──────────────────────────────────────────────────────────────────────

    async def _extract_all_connections(
        self,
        page: Page,
        session_id: str,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract all connections by scrolling through the list.

        Uses intelligent pagination:
        - Detects total connection count from page header
        - Waits for new content after each scroll
        - Handles LinkedIn's lazy loading
        - Natural scrolling with ghost cursor
        - Idle patterns (phone checks, thinking, distractions)
        - Warmup period for new accounts
        - Card inspection simulation

        Args:
            page: Playwright page
            session_id: Session ID for warning checks
            progress_callback: Optional progress callback

        Returns:
            List of connection dicts
        """
        connections = []
        seen_urls = set()
        no_new_count = 0

        # Start idle pattern tracking
        self.idle_generator.start_session()

        # Try to get total connection count from page
        total_count = await self._get_total_connection_count(page)
        if total_count:
            logger.info(f"Total connections detected: {total_count}")

        # ── Diagnostic: dump page structure to understand selectors ──
        try:
            dom_info = await page.evaluate(r'''() => {
                const info = {};
                // Check for our expected selectors
                info.componentkey_cards = document.querySelectorAll('[componentkey^="auto-component-"]').length;
                info.connections_list = document.querySelectorAll('[data-view-name="connections-list"]').length;
                info.connections_profile = document.querySelectorAll('[data-view-name="connections-profile"]').length;
                info.profile_links = document.querySelectorAll('a[href*="/in/"]').length;

                // Find all unique data-view-name values
                const viewNames = new Set();
                document.querySelectorAll('[data-view-name]').forEach(el => {
                    viewNames.add(el.getAttribute('data-view-name'));
                });
                info.data_view_names = Array.from(viewNames);

                // Find all unique componentkey prefixes
                const compKeys = new Set();
                document.querySelectorAll('[componentkey]').forEach(el => {
                    compKeys.add(el.getAttribute('componentkey'));
                });
                info.componentkeys = Array.from(compKeys).slice(0, 20);

                // Sample the first few profile links
                const links = document.querySelectorAll('a[href*="/in/"]');
                info.sample_profile_links = Array.from(links).slice(0, 5).map(a => ({
                    href: a.href,
                    text: a.textContent?.trim().substring(0, 60),
                    parent_tag: a.parentElement?.tagName,
                    grandparent_tag: a.parentElement?.parentElement?.tagName,
                }));

                // Look at list-like containers
                const lists = document.querySelectorAll('ul, ol, [role="list"]');
                info.list_elements = Array.from(lists).map(l => ({
                    tag: l.tagName,
                    role: l.getAttribute('role'),
                    children: l.children.length,
                    class: l.className?.substring(0, 80),
                })).filter(l => l.children > 3).slice(0, 10);

                return info;
            }''')
            logger.info(f"DOM diagnostic: {dom_info}")
        except Exception as e:
            logger.debug(f"DOM diagnostic failed: {e}")

        while True:
            # Check if should take break
            if self.behavior.should_take_break():
                logger.info("Session break triggered — stopping extraction")
                break

            # Check for LinkedIn warnings every ~50 connections
            if len(connections) % 50 == 0 and len(connections) > 0:
                await check_and_handle_warnings(
                    page, session_id, self.session_manager, raise_on_warning=True
                )

            # Extract visible connections
            visible = await self._extract_visible_connections(page)

            # Add new connections
            new_connections = 0
            for conn in visible:
                url = conn.get('linkedin_url')
                if url and url not in seen_urls:
                    connections.append(conn)
                    seen_urls.add(url)
                    new_connections += 1
                    self.idle_generator.record_connection()

            # Progress callback with estimated total
            if progress_callback:
                estimated_total = total_count if total_count else len(connections) + 500
                await progress_callback(len(connections), estimated_total)

            # Check if we've extracted all connections
            if total_count and len(connections) >= total_count:
                logger.info(f"Reached total count: {len(connections)}/{total_count}")
                break

            # Check if we've reached the end (no new connections after scrolling)
            if new_connections == 0:
                no_new_count += 1
                if no_new_count >= 3:  # No new connections in 3 scrolls
                    logger.info("No new connections after 3 scrolls — assuming end of list")
                    break
            else:
                no_new_count = 0

            # Calculate warmup multiplier (slower at start of session)
            warmup_mult = self.idle_generator.get_warmup_multiplier_by_count(
                self.config.warmup_connections
            )

            # Simulate reading the visible connections before scrolling
            # A real user spends time looking at names/titles
            reading_time = random.uniform(self.MIN_READ_PAUSE, self.MAX_READ_PAUSE)
            reading_time *= warmup_mult
            await asyncio.sleep(reading_time)

            # ── Idle pattern checks ──
            # Run idle checks (phone, thinking, distraction, mini-break)
            idle_event = await self.idle_generator.run_idle_check(page)
            if idle_event != "none":
                logger.info(f"Idle event occurred: {idle_event}")

            # Card inspection simulation (hover without click)
            if random.random() < self.CARD_INSPECTION_CHANCE:
                inspected = await self.idle_generator.inspect_random_card(page)
                if inspected:
                    logger.debug("Inspected random connection card")

            # Scroll down with human-like behavior (multiple small scrolls)
            await self._scroll_connections_page(page)

            # Wait for new content to load (LinkedIn lazy loads)
            await self._wait_for_new_content(page, len(seen_urls))

            # Human-like delay between scroll sessions (with warmup multiplier)
            delay = random.uniform(self.MIN_SCROLL_DELAY, self.MAX_SCROLL_DELAY)
            delay *= warmup_mult
            await asyncio.sleep(delay)

            # Occasional variation: scroll back up slightly (re-reading)
            # Increased from 15% to configurable (20-25%)
            if random.random() < self.BACK_SCROLL_CHANCE:
                cursor = GhostCursor(page)
                # Variable scroll-back distance
                back_distance = random.randint(-350, -150)
                await cursor.scroll(back_distance)
                await asyncio.sleep(random.uniform(1.5, 3.5))

                # Sometimes do a small "reading scan" after scrolling back
                if random.random() < 0.3:
                    await cursor.reading_scan()

        logger.info(f"Extraction complete: {len(connections)} connections found")
        return connections

    async def _get_total_connection_count(self, page: Page) -> Optional[int]:
        """
        Extract total connection count from the page header.

        LinkedIn displays "X connections" at the top of the connections page.
        """
        try:
            count_text = await page.evaluate(r'''() => {
                // Look for text like "500 connections" or "1,234 Connections"
                const selectors = [
                    'h1',
                    '[class*="header"]',
                    '[class*="count"]',
                    'span',
                    'p'
                ];

                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const text = el.textContent?.trim() || '';
                        // Match patterns like "500 connections" or "1,234 Connections"
                        const match = text.match(/^([\d,]+)\s*connections?$/i);
                        if (match) {
                            return match[1].replace(/,/g, '');
                        }
                    }
                }
                return null;
            }''')

            if count_text:
                return int(count_text)
        except Exception as e:
            logger.debug(f"Could not extract total count: {e}")

        return None

    async def _wait_for_new_content(self, page: Page, previous_count: int) -> None:
        """
        Wait for new connection cards to load after scrolling.

        LinkedIn lazy-loads ~50 connections per scroll. We wait up to 5 seconds
        for new content to appear.
        """
        for _ in range(10):
            try:
                current_count = await page.evaluate(r'''() => {
                    const links = document.querySelectorAll('a[href*="/in/"]');
                    const urls = new Set();
                    links.forEach(link => urls.add(link.href.split('?')[0]));
                    return urls.size;
                }''')

                if current_count > previous_count:
                    return
            except Exception:
                # Page may have navigated — wait and retry
                pass

            await asyncio.sleep(0.5)

        # Timeout — continue anyway

    async def _wait_for_connections_to_load(self, page: Page) -> None:
        """
        Wait for LinkedIn to render connection cards.
        LinkedIn uses React and lazy loading, so we need to wait and potentially scroll.

        Uses stable data-view-name and componentkey attributes (Feb 2026 structure).
        """
        # Priority order: most specific to broadest
        possible_selectors = [
            '[data-view-name="connections-list"]',  # Main list container
            '[data-view-name="connections-profile"]',  # Individual profile links
            '[componentkey^="auto-component-"]',  # Card containers
            'a[href*="/in/"]',  # Broad fallback — any profile link on page
        ]

        for attempt in range(10):
            for selector in possible_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        logger.debug(f"Found {count} elements matching '{selector}'")
                        await asyncio.sleep(2)
                        return
                except Exception:
                    continue

            await asyncio.sleep(1)
            if attempt == 3:
                # Try scrolling to trigger lazy loading
                cursor = GhostCursor(page)
                await cursor.scroll(500)
                await asyncio.sleep(0.5)

    async def _extract_visible_connections(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract connection data from currently visible connection cards.

        Uses LinkedIn's data-view-name="connections-profile" links as the
        primary anchor, then walks up to find the containing card (which has
        a componentkey attribute — any UUID, not just "auto-component-" prefix).

        LinkedIn DOM structure (Feb 2026):
        - List containers: [data-view-name="connections-list"] (one per card)
        - Card container: [componentkey] (any UUID value)
        - Profile links: [data-view-name="connections-profile"] (2 per card: image + text)
        - Name: <a> inside <p> with short text (the name-only link)
        - Headline: <p> element with job description text
        - Connected date: <p> with "Connected" text
        """
        cards_data = await page.evaluate(r'''() => {
            const connections = [];
            const seenUrls = new Set();

            // Strategy: find all connection profile links, deduplicate by URL,
            // walk up to the card container, extract data from there.
            const profileLinks = document.querySelectorAll(
                '[data-view-name="connections-profile"], a[href*="/in/"]'
            );

            profileLinks.forEach(link => {
                const url = link.href?.split('?')[0];
                if (!url || !url.includes('/in/') || seenUrls.has(url)) return;
                seenUrls.add(url);

                // Walk up to find the card container (element with componentkey)
                let card = link;
                for (let i = 0; i < 10 && card; i++) {
                    if (card.hasAttribute && card.hasAttribute('componentkey')) break;
                    card = card.parentElement;
                }
                if (!card || !card.hasAttribute || !card.hasAttribute('componentkey')) return;

                // Extract name — find the shortest <a> text that links to this profile
                // (the name-only link, not the one with name+headline concatenated)
                let name = null;
                const allProfileLinks = card.querySelectorAll('a[href*="/in/"]');
                let shortestName = null;
                let shortestLen = Infinity;

                for (const a of allProfileLinks) {
                    // Look for <a> inside <p> — this is the name-only pattern
                    if (a.parentElement?.tagName === 'P') {
                        const text = a.textContent?.trim();
                        if (text && text.length >= 2 && text.length < 60) {
                            name = text;
                            break;
                        }
                    }
                    // Track shortest non-empty text as fallback
                    const text = a.textContent?.trim();
                    if (text && text.length >= 2 && text.length < 60 && text.length < shortestLen) {
                        shortestName = text;
                        shortestLen = text.length;
                    }
                }

                if (!name) name = shortestName;

                // Fallback: aria-label on figure element
                if (!name) {
                    const figure = card.querySelector('figure[aria-label]');
                    if (figure) {
                        const ariaLabel = figure.getAttribute('aria-label');
                        if (ariaLabel?.includes("'s profile picture")) {
                            name = ariaLabel.replace("'s profile picture", "").trim();
                        }
                    }
                }

                if (!name || name.length < 2) return;

                // Extract headline and connected date from <p> elements
                let headline = null;
                let connectedDate = null;
                const paragraphs = card.querySelectorAll('p');

                for (const p of paragraphs) {
                    const text = p.textContent?.trim();
                    if (!text || text.length < 3) continue;

                    // Skip the name itself
                    if (text === name) continue;

                    // Connected date
                    if (text.startsWith('Connected')) {
                        connectedDate = text;
                        continue;
                    }

                    // Skip UI buttons/labels
                    if (/^(Message|Connect|Follow|Pending|Send|InMail|Remove|More)$/i.test(text)) continue;

                    // Headline: longer text that's not the name
                    if (!headline && text.length >= 5 && text.length <= 250) {
                        // Make sure it's not the name + headline concatenated
                        if (!text.startsWith(name)) {
                            headline = text;
                        }
                    }
                }

                // Extract profile image
                const img = card.querySelector('img[src*="licdn"], img[src*="profile-displayphoto"]');
                const imgUrl = img?.src || null;

                connections.push({
                    name,
                    headline,
                    url,
                    imgUrl,
                    connectedDate
                });
            });

            return connections;
        }''')

        logger.info(f"_extract_visible: JS returned {len(cards_data)} cards")
        if len(cards_data) > 0:
            logger.info(f"Extracted {len(cards_data)} visible connections (sample: {cards_data[0].get('name', '?')})")
        else:
            # Debug: check why extraction found nothing
            try:
                debug_info = await page.evaluate(r'''() => {
                    const links = document.querySelectorAll('a[href*="/in/"]');
                    const results = [];
                    const seenUrls = new Set();
                    for (const link of links) {
                        const url = link.href?.split('?')[0];
                        if (!url || !url.includes('/in/') || seenUrls.has(url)) continue;
                        seenUrls.add(url);
                        // Walk up to find componentkey
                        let el = link;
                        let depth = 0;
                        let foundKey = null;
                        for (let i = 0; i < 20 && el; i++) {
                            if (el.hasAttribute && el.hasAttribute('componentkey')) {
                                foundKey = el.getAttribute('componentkey');
                                depth = i;
                                break;
                            }
                            el = el.parentElement;
                        }
                        results.push({
                            url: url.substring(url.lastIndexOf('/in/')),
                            text: link.textContent?.trim().substring(0, 30),
                            parentTag: link.parentElement?.tagName,
                            compkeyDepth: foundKey ? depth : -1,
                            compkey: foundKey?.substring(0, 20),
                        });
                        if (results.length >= 5) break;
                    }
                    return results;
                }''')
                logger.info(f"  Debug card walk-up: {debug_info}")
            except Exception:
                pass

        connections = []
        for card_data in cards_data:
            url = card_data['url']
            if url:
                url = url.split('?')[0]

            title, company = self._parse_occupation(card_data['headline'])

            connections.append({
                'full_name': card_data['name'],
                'linkedin_url': url,
                'current_title': title,
                'current_company': company,
                'headline': card_data['headline'],
                'profile_image_url': card_data['imgUrl'],
                'extracted_at': datetime.now(timezone.utc).isoformat()
            })

        return connections

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _parse_occupation(self, occupation: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Parse 'Title at Company' into (title, company)."""
        if not occupation:
            return None, None
        if ' at ' in occupation:
            parts = occupation.split(' at ', 1)
            return parts[0].strip(), parts[1].strip()
        if ' | ' in occupation:
            parts = occupation.split(' | ', 1)
            return parts[0].strip(), parts[1].strip()
        return occupation.strip(), None

    async def _scroll_connections_page(self, page: Page) -> None:
        """
        Scroll the connections page using mouse-wheel events.

        Uses multiple small scrolls instead of one big jump to appear more natural.
        A real user scrolls in increments, pausing to read.

        Randomly alternates between:
        - Standard incremental scrolling
        - Momentum-based scrolling (more natural physics)
        """
        cursor = GhostCursor(page)

        # 40% chance to use momentum-based scrolling
        use_momentum = random.random() < 0.40

        if use_momentum:
            # Use momentum-based scroll with natural acceleration/deceleration
            total_distance = random.randint(500, 800)
            await cursor.scroll_with_momentum(total_distance)
        else:
            # Standard incremental scrolling
            # Break the scroll into 2-4 smaller increments
            num_scrolls = random.randint(2, 4)
            total_distance = random.randint(500, 800)
            distance_per_scroll = total_distance // num_scrolls

            for i in range(num_scrolls):
                # Each small scroll
                await cursor.scroll(distance_per_scroll + random.randint(-50, 50))

                # Brief pause between small scrolls (simulating reading)
                if i < num_scrolls - 1:
                    await asyncio.sleep(random.uniform(self.MIN_READ_PAUSE, self.MAX_READ_PAUSE))

    async def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in (not redirected to login/checkpoint)."""
        url = page.url
        if '/login' in url or '/checkpoint' in url:
            return False
        if any(segment in url for segment in ('/mynetwork', '/feed', '/connections', '/in/')):
            return True
        try:
            nav = await page.locator('nav, header[role="banner"]').count()
            return nav > 0
        except Exception:
            return False

    async def _add_session_cookies(
        self,
        context: BrowserContext,
        cookies: Dict[str, Any]
    ) -> None:
        """Add session cookies to browser context."""
        cookie_list = []
        for name, data in cookies.items():
            cookie = {
                'name': name,
                'value': data['value'],
                'domain': data.get('domain', '.linkedin.com'),
                'path': data.get('path', '/'),
                'secure': data.get('secure', True),
                'httpOnly': data.get('httpOnly', False)
            }
            if data.get('expirationDate'):
                cookie['expires'] = data['expirationDate']
            cookie_list.append(cookie)

        await context.add_cookies(cookie_list)
