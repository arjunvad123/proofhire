"""
LinkedIn connection extraction service (Phase 2).

Implements Comet-style extraction with human-like behavior:
- Natural navigation chain (feed → mynetwork → connections)
- Gradual scrolling with natural delays
- Realistic reading patterns
- Respects rate limits
- Session management

Uses StealthBrowser for context-level stealth + extra evasion scripts.
"""

import asyncio
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from playwright.async_api import Page, BrowserContext

from .human_behavior import HumanBehaviorEngine, GhostCursor, GhostCursorIntegration
from .session_manager import LinkedInSessionManager
from .stealth_browser import StealthBrowser
from .warning_detection import check_and_handle_warnings

logger = logging.getLogger(__name__)


class LinkedInConnectionExtractor:
    """Extract LinkedIn connections with human-like behavior."""

    # LinkedIn loads approximately 50 connections per scroll
    CONNECTIONS_PER_SCROLL = 50

    # Scroll delays (seconds)
    MIN_SCROLL_DELAY = 1.0
    MAX_SCROLL_DELAY = 3.0

    def __init__(self, session_manager: LinkedInSessionManager):
        """
        Initialize extractor.

        Args:
            session_manager: Session manager for cookie handling
        """
        self.session_manager = session_manager
        self.behavior = HumanBehaviorEngine()

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

            # Get proxy for session
            session = await self.session_manager.get_session(session_id)
            user_location = session.get('user_location')

            async with StealthBrowser.launch_persistent(
                session_id=session_id,
                headless=False,
                user_location=user_location,
            ) as sb:
                # Add cookies if not already in persistent profile
                current_cookies = await sb.context.cookies()
                if not any(c['name'] == 'li_at' for c in current_cookies):
                    await self._add_session_cookies(sb.context, cookies)

                page = await sb.new_page()

                try:
                    # Start behavior session
                    self.behavior.start_session()

                    # ── Natural navigation chain ──
                    # Instead of jumping straight to /connections (which LinkedIn
                    # detects as suspicious), walk through the natural page flow
                    # like a real user would.
                    navigated = await self._navigate_to_connections_naturally(page)
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

    async def _navigate_to_connections_naturally(self, page: Page) -> bool:
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

            # Quick check: are we logged in?
            if not await self._is_logged_in(page):
                logger.warning("Not logged in after feed navigation")
                return False

            # Simulate reading the feed briefly (scroll a bit, pause)
            await self._simulate_feed_browsing(page)

            # Step 2: Navigate to My Network (via top nav or URL)
            logger.info("Navigation chain: step 2 — loading My Network")
            clicked = await self._click_my_network_link(page)
            if not clicked:
                # Fallback: navigate directly (still has Referer from feed)
                await page.goto(
                    'https://www.linkedin.com/mynetwork/',
                    wait_until='load',
                    timeout=30000
                )
            await asyncio.sleep(random.uniform(1.5, 3.5))

            if not await self._is_logged_in(page):
                logger.warning("Not logged in after My Network navigation")
                return False

            # Step 3: Navigate to Connections
            logger.info("Navigation chain: step 3 — loading Connections page")
            clicked = await self._click_connections_link(page)
            if not clicked:
                # Fallback: navigate directly (Referer = /mynetwork/)
                await page.goto(
                    'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                    wait_until='load',
                    timeout=30000
                )
            await asyncio.sleep(random.uniform(1.5, 3.0))

            if not await self._is_logged_in(page):
                logger.warning("Not logged in after Connections navigation")
                return False

            logger.info("Navigation chain: successfully reached connections page")
            return True

        except Exception as e:
            logger.error(f"Navigation chain failed: {e}")
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

    async def _click_my_network_link(self, page: Page) -> bool:
        """Try to click the 'My Network' link in the top navigation bar."""
        selectors = [
            'a[href*="/mynetwork/"]',
            'a:has-text("My Network")',
            'nav a[href*="mynetwork"]',
            'li.global-nav__primary-item a[href*="mynetwork"]',
        ]
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    await GhostCursorIntegration.click_naturally(page, selector)
                    await page.wait_for_load_state('load', timeout=15000)
                    return True
            except Exception:
                continue
        return False

    async def _click_connections_link(self, page: Page) -> bool:
        """Try to click a 'Connections' link on the My Network page."""
        selectors = [
            'a[href*="/invite-connect/connections"]',
            'a:has-text("Connections")',
            'a:has-text("See all")',
            'a[href*="connections"]',
        ]
        for selector in selectors:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    await GhostCursorIntegration.click_naturally(page, selector)
                    await page.wait_for_load_state('load', timeout=15000)
                    return True
            except Exception:
                continue
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

            # Progress callback
            if progress_callback:
                await progress_callback(len(connections), len(connections) + 500)

            # Check if we've reached the end
            if new_connections == 0:
                no_new_count += 1
                if no_new_count >= 3:  # No new connections in 3 scrolls
                    break
            else:
                no_new_count = 0

            # Scroll down with human-like delay
            await self._scroll_connections_page(page)

            # Human-like delay between scrolls
            delay = random.uniform(self.MIN_SCROLL_DELAY, self.MAX_SCROLL_DELAY)
            await asyncio.sleep(delay)

            # Occasional variation: scroll back up slightly (re-reading) — 10%
            if random.random() < 0.1:
                cursor = GhostCursor(page)
                await cursor.scroll(-200)
                await asyncio.sleep(random.uniform(0.5, 1.5))

        logger.info(f"Extraction complete: {len(connections)} connections found")
        return connections

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

        Uses LinkedIn's stable data-view-name attributes and componentkey
        attributes to find cards reliably despite obfuscated class names.

        LinkedIn DOM structure (Feb 2026):
        - List container: [data-view-name="connections-list"]
        - Card container: [componentkey^="auto-component-"]
        - Profile links: [data-view-name="connections-profile"]
        - Name: innermost <a> or <p> with profile link text
        - Headline: <p> element with job description text
        - Connected date: <p> with "Connected on" text
        """
        cards_data = await page.evaluate(r'''() => {
            const connections = [];
            const seenUrls = new Set();

            // Find the connections list container
            const listContainer = document.querySelector('[data-view-name="connections-list"]');
            if (!listContainer) {
                // Fallback: search entire document
                console.warn('connections-list container not found, searching document');
            }

            const searchRoot = listContainer || document;

            // Find all connection cards by componentkey (stable attribute)
            const cards = searchRoot.querySelectorAll('[componentkey^="auto-component-"]');

            cards.forEach(card => {
                // Find profile link within this card
                const profileLinks = card.querySelectorAll('a[href*="/in/"]');
                if (profileLinks.length === 0) return;

                // Get the profile URL from the first link
                const profileLink = profileLinks[0];
                const url = profileLink.href?.split('?')[0];
                if (!url || seenUrls.has(url)) return;
                seenUrls.add(url);

                // Extract name - look for the innermost text in a profile link
                let name = null;
                for (const link of profileLinks) {
                    // Check for nested <a> with just the name
                    const innerA = link.querySelector('a');
                    if (innerA && innerA.textContent?.trim()) {
                        name = innerA.textContent.trim();
                        break;
                    }
                    // Check for <p> containing <a> with name
                    const pWithA = link.querySelector('p a');
                    if (pWithA && pWithA.textContent?.trim()) {
                        name = pWithA.textContent.trim();
                        break;
                    }
                    // Fallback: use link text if it looks like a name
                    const linkText = link.textContent?.trim();
                    if (linkText && linkText.length > 2 && linkText.length < 60 && !linkText.includes('@')) {
                        // Skip if it contains headline indicators
                        if (!linkText.includes(' | ') && !linkText.includes(' at ')) {
                            name = linkText;
                            break;
                        }
                    }
                }

                // Extract headline - find <p> elements with job description
                let headline = null;
                let connectedDate = null;
                const paragraphs = card.querySelectorAll('p');
                for (const p of paragraphs) {
                    const text = p.textContent?.trim();
                    if (!text || text.length < 5) continue;

                    // Skip if it's the name
                    if (text === name) continue;

                    // Check for connected date
                    if (text.startsWith('Connected on') || text.startsWith('Connected ')) {
                        connectedDate = text;
                        continue;
                    }

                    // Skip UI elements
                    if (/^(Message|Connect|Follow|Pending|Send|InMail)$/i.test(text)) continue;

                    // This is likely the headline (job title / company)
                    if (!headline && text.length >= 10 && text.length <= 200) {
                        headline = text;
                    }
                }

                // If no name found from links, try to extract from aria-label
                if (!name) {
                    const figure = card.querySelector('figure[aria-label]');
                    if (figure) {
                        const ariaLabel = figure.getAttribute('aria-label');
                        if (ariaLabel && ariaLabel.includes("'s profile picture")) {
                            name = ariaLabel.replace("'s profile picture", "").trim();
                        }
                    }
                }

                // Skip if we couldn't find a name
                if (!name || name.length < 2) return;

                // Extract profile image
                const img = card.querySelector('img[src*="licdn"], img[src*="profile"]');
                const imgUrl = img?.src || null;

                connections.push({
                    name,
                    headline,
                    url,
                    imgUrl,
                    connectedDate
                });
            });

            // Fallback: if no cards found via componentkey, try profile links directly
            if (connections.length === 0) {
                const profileLinks = searchRoot.querySelectorAll('[data-view-name="connections-profile"]');
                const processedUrls = new Set();

                profileLinks.forEach(link => {
                    const url = link.href?.split('?')[0];
                    if (!url || processedUrls.has(url)) return;
                    processedUrls.add(url);

                    // Walk up to find the containing card
                    let card = link.parentElement;
                    for (let i = 0; i < 8 && card; i++) {
                        if (card.hasAttribute('componentkey')) break;
                        card = card.parentElement;
                    }

                    if (!card) return;

                    // Extract data similar to above
                    let name = null;
                    const nameLink = card.querySelector('a[href*="/in/"] p a, p a[href*="/in/"]');
                    if (nameLink) {
                        name = nameLink.textContent?.trim();
                    } else {
                        // Try aria-label
                        const figure = card.querySelector('figure[aria-label]');
                        if (figure) {
                            const ariaLabel = figure.getAttribute('aria-label');
                            if (ariaLabel?.includes("'s profile picture")) {
                                name = ariaLabel.replace("'s profile picture", "").trim();
                            }
                        }
                    }

                    if (!name) return;

                    let headline = null;
                    const paragraphs = card.querySelectorAll('p');
                    for (const p of paragraphs) {
                        const text = p.textContent?.trim();
                        if (!text || text === name || text.length < 10) continue;
                        if (text.startsWith('Connected')) continue;
                        if (/^(Message|Connect|Follow)$/i.test(text)) continue;
                        headline = text;
                        break;
                    }

                    const img = card.querySelector('img[src*="licdn"]');

                    connections.push({
                        name,
                        headline,
                        url,
                        imgUrl: img?.src || null,
                        connectedDate: null
                    });
                });
            }

            return connections;
        }''')

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
        """Scroll the connections page using mouse-wheel events (not scrollBy)."""
        cursor = GhostCursor(page)
        await cursor.scroll(random.randint(800, 1200))

    async def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in (not redirected to login/checkpoint)."""
        url = page.url
        if '/login' in url or '/checkpoint' in url:
            return False
        if '/mynetwork' in url or '/feed' in url:
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
