"""
LinkedIn connection extraction service (Phase 2).

Implements Comet-style extraction with human-like behavior:
- Gradual scrolling with natural delays
- Realistic reading patterns
- Respects rate limits
- Session management
"""

import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth

from .human_behavior import HumanBehaviorEngine, GhostCursorIntegration
from .session_manager import LinkedInSessionManager
from .warning_detection import check_and_handle_warnings


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

            async with async_playwright() as p:
                # Use persistent context (browser profile) for this user
                context = await self._launch_persistent_context(p, session_id, user_location)

                # Add cookies if not already in persistent profile
                current_cookies = await context.cookies()
                if not any(c['name'] == 'li_at' for c in current_cookies):
                    await self._add_session_cookies(context, cookies)

                page = await context.new_page()

                # Apply stealth to avoid detection
                await Stealth().apply_stealth_async(page)

                try:
                    # Start behavior session
                    self.behavior.start_session()

                    # Navigate to connections page
                    # Use 'load' instead of 'networkidle' - LinkedIn has persistent connections
                    await page.goto(
                        'https://www.linkedin.com/mynetwork/invite-connect/connections/',
                        wait_until='load',
                        timeout=30000
                    )

                    # Wait for React to render and connections to appear
                    # LinkedIn lazy-loads content, so we need to wait and scroll
                    await self._wait_for_connections_to_load(page)

                    # Verify we're logged in
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
                    await context.close()

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Extraction failed: {str(e)}'
            }

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
            progress_callback: Optional progress callback

        Returns:
            List of connection dicts
        """
        connections = []
        seen_urls = set()
        last_count = 0
        no_new_count = 0

        while True:
            # Check if should take break
            if self.behavior.should_take_break():
                break_duration = self.behavior.get_break_duration()
                # In production, pause and resume later
                # For now, just end the session
                break

            # Check for LinkedIn warnings every few iterations
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

            # Occasional variation: scroll back up slightly (re-reading)
            if random.random() < 0.1:  # 10% chance
                await page.evaluate('window.scrollBy(0, -200)')
                await asyncio.sleep(random.uniform(0.5, 1.5))

        return connections

    async def _wait_for_connections_to_load(self, page: Page) -> None:
        """
        Wait for LinkedIn to render connection cards.
        LinkedIn uses React and lazy loading, so we need to wait and potentially scroll.
        """
        # Try multiple possible selectors (LinkedIn may change their HTML)
        possible_selectors = [
            'li.mn-connection-card',
            'li[class*="reusable-search__result"]',
            'div.scaffold-finite-scroll__content li',
            'ul[class*="list"] > li[class*="list-item"]'
        ]

        # Wait up to 10 seconds for any connection cards to appear
        for attempt in range(10):
            for selector in possible_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    # Found connections! Wait a bit more for more to load
                    await asyncio.sleep(2)
                    return

            # No connections yet, wait and try a small scroll to trigger lazy loading
            await asyncio.sleep(1)
            if attempt == 3:  # After 3 seconds, try scrolling
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(0.5)

        # If we get here, no connections found - let the extraction handle it

    async def _extract_visible_connections(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract connection data from currently visible connection cards.

        Args:
            page: Playwright page

        Returns:
            List of connection dicts
        """
        connections = []

        # LinkedIn uses dynamic class names, so we need to find cards by structure
        # Connection cards have:
        #  - A div with data-view-name="connections-list"
        #  - Inside are divs with a profile link (a[href*="/in/"])
        #  - Each card has componentkey starting with "auto-component-"

        # Use JavaScript to find connection cards more reliably
        cards_data = await page.evaluate('''() => {
            // Find all divs that contain profile links
            const profileLinks = document.querySelectorAll('a[href*="/in/"]');
            const cards = [];

            profileLinks.forEach(link => {
                // Find the card container - look for parent with componentkey
                let container = link.closest('[componentkey^="auto-component"]');

                if (container && !cards.includes(container)) {
                    // Extract data directly from HTML
                    const nameLink = container.querySelector('a.de3d5865.ee709ba4, a[href*="/in/"] p a');
                    const name = nameLink ? nameLink.textContent.trim() : null;

                    const headlineEl = container.querySelector('p[class*="fed20de1"], div.bab11c20 p');
                    const headline = headlineEl ? headlineEl.textContent.trim() : null;

                    const profileLink = container.querySelector('a[href*="/in/"]');
                    const url = profileLink ? profileLink.href : null;

                    const img = container.querySelector('img[alt*="profile picture"]');
                    const imgUrl = img ? img.src : null;

                    if (name && url) {
                        cards.push({
                            name,
                            headline,
                            url,
                            imgUrl
                        });
                    }
                }
            });

            return cards;
        }''')

        # Convert JavaScript results to connection objects
        for card_data in cards_data:
            # Clean URL (remove query params)
            url = card_data['url']
            if url:
                url = url.split('?')[0]

            # Parse headline into title and company
            title, company = self._parse_occupation(card_data['headline'])

            connection = {
                'full_name': card_data['name'],
                'linkedin_url': url,
                'current_title': title,
                'current_company': company,
                'headline': card_data['headline'],
                'profile_image_url': card_data['imgUrl'],
                'extracted_at': datetime.now(timezone.utc).isoformat()
            }

            connections.append(connection)

        return connections

    async def _safe_text_content(self, element, selector: str) -> Optional[str]:
        """Safely extract text content from element."""
        try:
            locator = element.locator(selector).first
            text = await locator.text_content()
            return text.strip() if text else None
        except:
            return None

    def _parse_occupation(self, occupation: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """
        Parse occupation string into title and company.

        Format usually: "Title at Company"

        Args:
            occupation: Occupation string

        Returns:
            (title, company)
        """
        if not occupation:
            return None, None

        # Try "at" separator
        if ' at ' in occupation:
            parts = occupation.split(' at ', 1)
            return parts[0].strip(), parts[1].strip()

        # Try " | " separator (sometimes used)
        if ' | ' in occupation:
            parts = occupation.split(' | ', 1)
            return parts[0].strip(), parts[1].strip()

        # If no separator, treat as title only
        return occupation.strip(), None

    async def _scroll_connections_page(self, page: Page) -> None:
        """
        Scroll the connections page smoothly like a human.

        Args:
            page: Playwright page
        """
        # Smooth scroll (not instant jump)
        scroll_distance = random.randint(800, 1200)
        steps = random.randint(8, 15)
        step_distance = scroll_distance / steps
        step_delay = 0.05  # 50ms between steps

        for _ in range(steps):
            await page.evaluate(f'window.scrollBy(0, {step_distance})')
            await asyncio.sleep(step_delay)

    async def _is_logged_in(self, page: Page) -> bool:
        """Check if user is logged in."""
        # Check if we're on the connections page (not redirected to login)
        url = page.url
        if '/login' in url or '/checkpoint' in url:
            return False
        # If we're on /mynetwork, we're logged in
        if '/mynetwork' in url:
            return True
        # Also check for navigation elements as fallback
        try:
            # New LinkedIn uses different selectors
            nav = await page.locator('nav, header[role="banner"]').count()
            return nav > 0
        except:
            return False

    async def _launch_persistent_context(
        self,
        playwright,
        session_id: str,
        user_location: Optional[str] = None
    ) -> BrowserContext:
        """
        Launch persistent browser context (profile) for user.

        This creates a dedicated browser profile for each user that persists
        cookies and cache between sessions, mimicking real browser usage.

        Args:
            playwright: Playwright instance
            session_id: User session ID
            user_location: User location for proxy

        Returns:
            Persistent browser context
        """
        # Create browser profiles directory
        profiles_dir = Path('./browser_profiles')
        profiles_dir.mkdir(exist_ok=True)

        user_profile_dir = profiles_dir / session_id

        # Get proxy if location provided
        # TODO: Integrate ProxyManager
        proxy = None

        # Launch persistent context (browser profile)
        # NOT headless - appears more legitimate and reduces detection risk
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_profile_dir),
            headless=False,
            proxy=proxy,
            user_agent=self._get_realistic_user_agent(),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Los_Angeles',
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        return context

    async def _add_session_cookies(
        self,
        context: BrowserContext,
        cookies: Dict[str, Any]
    ) -> None:
        """
        Add session cookies to browser context.

        Args:
            context: Browser context
            cookies: LinkedIn cookies
        """
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

            # Add expiration if present
            if data.get('expirationDate'):
                cookie['expires'] = data['expirationDate']

            cookie_list.append(cookie)

        await context.add_cookies(cookie_list)

    def _get_realistic_user_agent(self) -> str:
        """Get realistic user agent string."""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
        ]
        return random.choice(user_agents)
