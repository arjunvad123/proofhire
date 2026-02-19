"""
Human behavior simulation for LinkedIn automation.

Implements realistic human-like patterns:
- Profile viewing with variable dwell time
- Natural reading/scrolling patterns
- Realistic typing with WPM variation
- Session management with breaks
- Ghost cursor integration for mouse movement
"""

import random
import asyncio
from typing import Optional, Tuple
from datetime import datetime, timedelta
from playwright.async_api import Page


class HumanBehaviorEngine:
    """Simulates human-like behavior patterns for LinkedIn automation."""

    # Typing speed range (words per minute)
    MIN_WPM = 40
    MAX_WPM = 80

    # Profile dwell time range (seconds)
    MIN_PROFILE_DWELL = 20
    MAX_PROFILE_DWELL = 60

    # Session limits
    MIN_SESSION_MINUTES = 45
    MAX_SESSION_MINUTES = 90
    MIN_BREAK_MINUTES = 120  # 2 hours
    MAX_BREAK_MINUTES = 360  # 6 hours

    def __init__(self):
        """Initialize behavior engine."""
        self.session_start: Optional[datetime] = None
        self.actions_in_session = 0
        self.last_action_time: Optional[datetime] = None

    # ===== Session Management =====

    def start_session(self) -> None:
        """Start a new automation session."""
        self.session_start = datetime.now()
        self.actions_in_session = 0
        self.last_action_time = datetime.now()

    def should_take_break(self) -> bool:
        """
        Check if should take a break based on session length.

        Returns:
            True if session should end and break should be taken
        """
        if not self.session_start:
            return False

        session_duration = (datetime.now() - self.session_start).total_seconds() / 60

        # Random session length between 45-90 minutes
        max_session = random.uniform(self.MIN_SESSION_MINUTES, self.MAX_SESSION_MINUTES)

        return session_duration >= max_session

    def get_break_duration(self) -> int:
        """
        Get break duration in seconds.

        Returns:
            Break duration (2-6 hours)
        """
        minutes = random.uniform(self.MIN_BREAK_MINUTES, self.MAX_BREAK_MINUTES)
        return int(minutes * 60)

    def should_take_micro_break(self, messages_sent: int) -> bool:
        """
        Check if should take a micro-break during session.

        Humans naturally pause every 15-25 actions.

        Args:
            messages_sent: Number of messages sent so far

        Returns:
            True if should take 30-60 minute break
        """
        if messages_sent > 0 and messages_sent % random.randint(15, 25) == 0:
            return True
        return False

    def get_micro_break_duration(self) -> int:
        """Get micro-break duration (30-60 minutes)."""
        return random.randint(1800, 3600)

    # ===== Profile Viewing Behavior =====

    def get_profile_dwell_time(self, profile_complexity: str = 'medium') -> float:
        """
        Get realistic profile dwell time based on content.

        Args:
            profile_complexity: 'simple', 'medium', or 'complex'
                - simple: Few experiences, minimal content (20-35s)
                - medium: Standard profile (35-50s)
                - complex: Extensive experience, projects (50-60s)

        Returns:
            Dwell time in seconds
        """
        if profile_complexity == 'simple':
            return random.uniform(20, 35)
        elif profile_complexity == 'complex':
            return random.uniform(50, 60)
        else:  # medium
            return random.uniform(35, 50)

    async def simulate_profile_reading(self, page: Page, profile_complexity: str = 'medium') -> None:
        """
        Simulate human reading pattern on a profile.

        Pattern:
        1. Brief pause at top (read headline/summary)
        2. Scroll down to experience section
        3. Read through experiences with pauses
        4. Occasionally scroll back up
        5. Scroll to bottom
        6. Final decision pause

        Args:
            page: Playwright page object
            profile_complexity: Profile content complexity
        """
        dwell_time = self.get_profile_dwell_time(profile_complexity)

        # 1. Pause at top (read headline)
        await asyncio.sleep(random.uniform(2, 4))

        # 2. Scroll down to experience section (humans don't jump instantly)
        await self._smooth_scroll(page, distance=300, duration=1.5)
        await asyncio.sleep(random.uniform(3, 6))

        # 3. Continue scrolling through experience
        await self._smooth_scroll(page, distance=400, duration=2)
        await asyncio.sleep(random.uniform(4, 7))

        # 4. Occasionally scroll back up (re-reading)
        if random.random() < 0.3:  # 30% chance
            await self._smooth_scroll(page, distance=-200, duration=1)
            await asyncio.sleep(random.uniform(2, 3))

        # 5. Scroll to education/skills
        await self._smooth_scroll(page, distance=300, duration=1.5)
        await asyncio.sleep(random.uniform(2, 4))

        # 6. Final decision pause
        remaining_time = dwell_time - 15  # Subtract time already spent
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)

    async def _smooth_scroll(self, page: Page, distance: int, duration: float) -> None:
        """
        Scroll smoothly like a human (not instant jump).

        Args:
            page: Playwright page
            distance: Pixels to scroll (negative for up)
            duration: Time to take for scroll (seconds)
        """
        steps = random.randint(10, 20)  # Number of scroll events
        step_distance = distance / steps
        step_delay = duration / steps

        for _ in range(steps):
            await page.evaluate(f'window.scrollBy(0, {step_distance})')
            await asyncio.sleep(step_delay)

    # ===== Search/Browse Behavior =====

    async def simulate_search_browsing(self, page: Page, profiles_to_view: int) -> list[int]:
        """
        Simulate human browsing through search results.

        Pattern:
        - Don't click every profile linearly
        - Scroll through results
        - Skip some profiles
        - Occasionally go back to results
        - Random selection pattern

        Args:
            page: Playwright page
            profiles_to_view: Number of profiles to select

        Returns:
            List of profile indices to view (not sequential)
        """
        # Generate non-linear browsing pattern
        total_visible = profiles_to_view * 3  # Assume 3x profiles visible
        selected_indices = []

        current_position = 0
        while len(selected_indices) < profiles_to_view and current_position < total_visible:
            # Sometimes skip 1-3 profiles
            skip = random.randint(0, 3)
            current_position += skip

            if current_position < total_visible:
                selected_indices.append(current_position)
                current_position += 1

                # Occasionally scroll past a few without clicking
                if random.random() < 0.2:  # 20% chance
                    current_position += random.randint(2, 5)

        return selected_indices

    # ===== Message Typing Behavior =====

    async def type_message_humanlike(
        self,
        page: Page,
        selector: str,
        message: str,
        wpm: Optional[int] = None
    ) -> None:
        """
        Type a message with realistic human typing pattern.

        Features:
        - Variable WPM (40-80)
        - Occasional typos + corrections
        - Natural pauses between words
        - Random variation in typing speed

        Args:
            page: Playwright page
            selector: Input field selector
            message: Message to type
            wpm: Words per minute (defaults to random 40-80)
        """
        if wpm is None:
            wpm = random.uniform(self.MIN_WPM, self.MAX_WPM)

        # Calculate base delay between characters
        chars_per_second = (wpm * 5) / 60  # Assuming 5 chars per word
        base_delay = 1 / chars_per_second

        # Clear field first
        await page.fill(selector, '')

        words = message.split()
        current_text = ''

        for i, word in enumerate(words):
            # Type word character by character
            for char in word:
                # Vary typing speed per character
                char_delay = base_delay * random.uniform(0.7, 1.3)

                current_text += char
                await page.fill(selector, current_text)
                await asyncio.sleep(char_delay)

                # Occasionally make a typo (5% chance)
                if random.random() < 0.05:
                    # Add wrong character
                    wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    current_text += wrong_char
                    await page.fill(selector, current_text)
                    await asyncio.sleep(char_delay)

                    # Pause (realized mistake)
                    await asyncio.sleep(random.uniform(0.2, 0.4))

                    # Backspace
                    current_text = current_text[:-1]
                    await page.fill(selector, current_text)
                    await asyncio.sleep(char_delay)

            # Add space after word (except last word)
            if i < len(words) - 1:
                current_text += ' '
                await page.fill(selector, current_text)

                # Longer pause between words
                await asyncio.sleep(base_delay * random.uniform(1.5, 2.5))

        # Final pause (reviewing message)
        await asyncio.sleep(random.uniform(1, 3))

    # ===== Delay Utilities =====

    def get_delay_between_messages(self) -> float:
        """
        Get random delay between sending messages.

        Returns:
            Delay in seconds (30s - 5min, skewed toward ~90s)
        """
        return random.triangular(30, 300, 90)

    def get_delay_between_profiles(self) -> float:
        """
        Get delay between viewing profiles.

        Returns:
            Delay in seconds (10-30s)
        """
        return random.uniform(10, 30)

    # ===== Working Hours =====

    def is_working_hours(self, timezone: str = 'America/Los_Angeles') -> bool:
        """
        Check if current time is working hours.

        Working hours: 8am - 8pm in user's timezone.

        Args:
            timezone: User's timezone string

        Returns:
            True if within working hours
        """
        try:
            import pytz
            tz = pytz.timezone(timezone)
            user_time = datetime.now(tz)
            return 8 <= user_time.hour <= 20
        except:
            # Fallback if pytz not available or timezone invalid
            hour = datetime.now().hour
            return 8 <= hour <= 20

    def is_weekday(self) -> bool:
        """
        Check if today is a weekday.

        Returns:
            True if Monday-Friday
        """
        return datetime.now().weekday() < 5

    # ===== Rate Limiting =====

    def should_send_message(
        self,
        messages_sent_today: int,
        daily_limit: int = 50
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if should send another message based on rate limits.

        Args:
            messages_sent_today: Messages sent so far today
            daily_limit: Maximum messages per day

        Returns:
            (can_send, reason_if_not)
        """
        # Check daily limit
        if messages_sent_today >= daily_limit:
            return False, f"Daily limit reached ({daily_limit})"

        # Check working hours
        if not self.is_working_hours():
            return False, "Outside working hours (8am-8pm)"

        # Check weekday
        if not self.is_weekday():
            return False, "Weekend - no sending"

        # Check if need session break
        if self.should_take_break():
            return False, "Session limit reached - need break"

        return True, None


class GhostCursorIntegration:
    """
    Integration with ghost-cursor for realistic mouse movements.

    Note: ghost-cursor is a Node.js package. For Python, we simulate similar behavior
    or can use Playwright's native mouse movement with realistic patterns.
    """

    @staticmethod
    async def move_to_element_naturally(
        page: Page,
        selector: str,
        duration: float = 1.0
    ) -> None:
        """
        Move mouse to element with natural curved path.

        Args:
            page: Playwright page
            selector: Element selector
            duration: Time to take for movement
        """
        # Get element position
        element = page.locator(selector)
        box = await element.bounding_box()

        if not box:
            return

        # Target point (with slight randomness, not exact center)
        target_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
        target_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)

        # Current position (approximation)
        current_x = random.randint(100, 800)
        current_y = random.randint(100, 600)

        # Move in steps with curved path (Bezier-like)
        steps = random.randint(15, 30)
        for i in range(steps):
            t = i / steps

            # Add bezier curve effect
            curve_factor = 4 * t * (1 - t)  # Parabolic curve
            curve_offset_x = random.uniform(-20, 20) * curve_factor
            curve_offset_y = random.uniform(-20, 20) * curve_factor

            # Interpolate position
            x = current_x + (target_x - current_x) * t + curve_offset_x
            y = current_y + (target_y - current_y) * t + curve_offset_y

            # Move mouse
            await page.mouse.move(x, y)
            await asyncio.sleep(duration / steps)

    @staticmethod
    async def click_naturally(page: Page, selector: str) -> None:
        """
        Click element with natural mouse movement.

        Args:
            page: Playwright page
            selector: Element selector
        """
        # Move to element naturally
        await GhostCursorIntegration.move_to_element_naturally(page, selector)

        # Brief pause before click (human reaction time)
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Click
        await page.click(selector)
