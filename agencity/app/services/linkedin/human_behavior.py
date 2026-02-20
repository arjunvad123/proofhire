"""
Human behavior simulation for LinkedIn automation.

Implements realistic human-like patterns:
- Ghost cursor: cubic Bezier mouse paths with easing + overshoot
- Natural typing with variable WPM, typos, and corrections
- Mouse-wheel scrolling (not window.scrollBy)
- Profile viewing with variable dwell time
- Session management with breaks
- Click-before-type pattern (move mouse → click field → type)
- Idle/distraction patterns (phone checks, thinking pauses, mini-breaks)
- Warmup mode for new accounts (slower start, ramping up)
"""

import math
import random
import asyncio
import logging
from typing import Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from playwright.async_api import Page

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Configuration Presets
# ─────────────────────────────────────────────────────────────────────────────

class ExtractionMode(Enum):
    """Extraction speed/safety presets."""
    CAUTIOUS = "cautious"  # For new accounts - 2x slower, more idle pauses
    NORMAL = "normal"      # For established accounts


@dataclass
class ExtractionConfig:
    """
    Configuration for connection extraction behavior.

    Presets balance extraction speed vs. detection risk.
    """
    scroll_delay_min: float
    scroll_delay_max: float
    read_pause_min: float
    read_pause_max: float
    warmup_connections: int
    idle_frequency_multiplier: float
    back_scroll_chance: float
    card_inspection_chance: float

    @classmethod
    def cautious(cls) -> "ExtractionConfig":
        """For new accounts - extra careful, much slower."""
        return cls(
            scroll_delay_min=3.5,
            scroll_delay_max=8.0,
            read_pause_min=2.0,
            read_pause_max=5.0,
            warmup_connections=20,
            idle_frequency_multiplier=1.5,
            back_scroll_chance=0.25,
            card_inspection_chance=0.12,
        )

    @classmethod
    def normal(cls) -> "ExtractionConfig":
        """For established accounts - faster but still human-like."""
        return cls(
            scroll_delay_min=3.0,
            scroll_delay_max=7.0,
            read_pause_min=1.5,
            read_pause_max=4.5,
            warmup_connections=10,
            idle_frequency_multiplier=1.0,
            back_scroll_chance=0.20,
            card_inspection_chance=0.10,
        )

    @classmethod
    def from_mode(cls, mode: ExtractionMode) -> "ExtractionConfig":
        """Get config for a given mode."""
        if mode == ExtractionMode.CAUTIOUS:
            return cls.cautious()
        return cls.normal()


# ─────────────────────────────────────────────────────────────────────────────
# Idle Pattern Generator
# ─────────────────────────────────────────────────────────────────────────────

class IdlePatternGenerator:
    """
    Generates realistic idle/distraction patterns that mimic real user behavior.

    Real users don't maintain constant attention:
    - Check phone (5-15s pause)
    - Think about something (3-8s pause)
    - Re-read content (scroll back, pause)
    - Get distracted mid-session (30-60s pause)
    - Occasional longer break (2-5 min within session)
    """

    # Probability weights for different idle behaviors (per scroll cycle)
    PHONE_CHECK_CHANCE = 0.08        # 8% chance per scroll cycle
    THINKING_PAUSE_CHANCE = 0.12     # 12% chance
    DISTRACTION_CHANCE = 0.03        # 3% chance for longer distraction
    MINI_BREAK_CHANCE = 0.02         # 2% chance for 2-5 min break

    def __init__(self, frequency_multiplier: float = 1.0):
        """
        Initialize idle pattern generator.

        Args:
            frequency_multiplier: Scale idle event frequency (1.5 = 50% more frequent)
        """
        self.frequency_multiplier = frequency_multiplier
        self.session_start_time: Optional[datetime] = None
        self.connections_processed = 0

    def start_session(self) -> None:
        """Mark the start of an extraction session."""
        self.session_start_time = datetime.now()
        self.connections_processed = 0

    def record_connection(self) -> None:
        """Record that a connection was processed."""
        self.connections_processed += 1

    def get_warmup_multiplier(self, minutes_active: Optional[float] = None) -> float:
        """
        New accounts/sessions should start slower and ramp up.

        First 5 min: 2x delays (very cautious)
        5-15 min: 1.5x delays
        15-30 min: 1.2x delays
        30+ min: normal (1x)

        Args:
            minutes_active: Override for testing. If None, uses actual session time.

        Returns:
            Multiplier for delays (higher = slower)
        """
        if minutes_active is None:
            if self.session_start_time is None:
                return 2.0  # Not started yet, be very cautious
            elapsed = (datetime.now() - self.session_start_time).total_seconds() / 60
        else:
            elapsed = minutes_active

        if elapsed < 5:
            return 2.0
        elif elapsed < 15:
            return 1.5
        elif elapsed < 30:
            return 1.2
        else:
            return 1.0

    def get_warmup_multiplier_by_count(self, warmup_threshold: int) -> float:
        """
        Alternative warmup based on connection count.

        First N connections are slower regardless of time.

        Args:
            warmup_threshold: Number of connections for warmup period

        Returns:
            Multiplier for delays
        """
        if self.connections_processed < warmup_threshold // 4:
            return 2.0  # First 25% of warmup: very slow
        elif self.connections_processed < warmup_threshold // 2:
            return 1.5  # Next 25%: slower
        elif self.connections_processed < warmup_threshold:
            return 1.2  # Last 50%: slightly slow
        else:
            return 1.0  # Normal speed

    def _should_trigger(self, base_chance: float) -> bool:
        """Check if an idle event should trigger, accounting for frequency multiplier."""
        return random.random() < (base_chance * self.frequency_multiplier)

    async def maybe_phone_check(self, page: Page) -> bool:
        """
        8% chance: pause 5-15s, maybe move mouse away from content.

        Simulates user briefly checking their phone.

        Returns:
            True if a phone check occurred
        """
        if not self._should_trigger(self.PHONE_CHECK_CHANCE):
            return False

        logger.debug("Idle: simulating phone check")

        # Optionally move mouse to edge of screen (looking away)
        if random.random() < 0.4:
            try:
                cursor = GhostCursor(page)
                # Move to corner/edge of viewport
                viewport = page.viewport_size
                if viewport:
                    edge_x = random.choice([10, viewport['width'] - 10])
                    edge_y = random.randint(100, viewport['height'] - 100)
                    await cursor.move_to(edge_x, edge_y)
            except Exception:
                pass  # Non-critical

        # Pause for phone check duration
        pause_duration = random.uniform(5.0, 15.0)
        await asyncio.sleep(pause_duration)
        return True

    async def maybe_thinking_pause(self) -> bool:
        """
        12% chance: pause 3-8s (user thinking about what they see).

        Returns:
            True if a thinking pause occurred
        """
        if not self._should_trigger(self.THINKING_PAUSE_CHANCE):
            return False

        logger.debug("Idle: simulating thinking pause")
        pause_duration = random.uniform(3.0, 8.0)
        await asyncio.sleep(pause_duration)
        return True

    async def maybe_distraction(self) -> bool:
        """
        3% chance: longer pause 30-60s (got distracted by something).

        Returns:
            True if a distraction occurred
        """
        if not self._should_trigger(self.DISTRACTION_CHANCE):
            return False

        logger.debug("Idle: simulating distraction (30-60s)")
        pause_duration = random.uniform(30.0, 60.0)
        await asyncio.sleep(pause_duration)
        return True

    async def maybe_mini_break(self) -> bool:
        """
        2% chance: 2-5 minute break (bathroom, coffee, etc).

        Returns:
            True if a mini break occurred
        """
        if not self._should_trigger(self.MINI_BREAK_CHANCE):
            return False

        logger.info("Idle: taking mini break (2-5 min)")
        pause_duration = random.uniform(120.0, 300.0)  # 2-5 minutes
        await asyncio.sleep(pause_duration)
        return True

    async def run_idle_check(self, page: Page) -> str:
        """
        Run through all idle checks in priority order.

        Only one idle event triggers per check (mini break takes priority).

        Args:
            page: Playwright page for mouse movements

        Returns:
            Name of the idle event that occurred, or "none"
        """
        # Check in priority order (longest first)
        if await self.maybe_mini_break():
            return "mini_break"
        if await self.maybe_distraction():
            return "distraction"
        if await self.maybe_phone_check(page):
            return "phone_check"
        if await self.maybe_thinking_pause():
            return "thinking_pause"
        return "none"

    async def inspect_random_card(self, page: Page, card_selector: str = '[componentkey^="auto-component-"]') -> bool:
        """
        Hover over a visible connection card briefly without clicking.

        Simulates user considering whether to click on someone's profile.

        Args:
            page: Playwright page
            card_selector: CSS selector for connection cards

        Returns:
            True if a card was inspected
        """
        try:
            cards = await page.locator(card_selector).all()
            if not cards:
                return False

            # Pick a random visible card
            card = random.choice(cards)
            box = await card.bounding_box()
            if not box:
                return False

            # Check if card is in viewport
            viewport = page.viewport_size
            if not viewport:
                return False
            if box['y'] < 0 or box['y'] > viewport['height']:
                return False

            logger.debug("Idle: inspecting random card (hover)")

            # Move cursor to card
            cursor = GhostCursor(page)
            target_x = box['x'] + box['width'] * random.uniform(0.3, 0.7)
            target_y = box['y'] + box['height'] * random.uniform(0.3, 0.7)
            await cursor.move_to(target_x, target_y)

            # Hover duration (considering the profile)
            await asyncio.sleep(random.uniform(1.0, 3.0))

            return True
        except Exception as e:
            logger.debug(f"Card inspection failed: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Ghost cursor — pure-Python Bezier mouse movement
# ─────────────────────────────────────────────────────────────────────────────

class GhostCursor:
    """
    Realistic mouse movement using cubic Bezier curves with easing.

    Reproduces what the Node.js ``ghost-cursor`` library does:
      - Cubic Bezier path between current and target positions
      - Random control-point offsets (so every path is unique)
      - Ease-in-out timing (fast in the middle, slow at start/end)
      - Slight overshoot + correction on ~25 % of moves
      - Tracks actual mouse position across calls (no "teleporting")

    Usage::

        cursor = GhostCursor(page)
        await cursor.move_to_element('button.submit')
        await cursor.click()                     # clicks at current position
        await cursor.click_element('#email')     # move + click
        await cursor.type_into('#email', 'hi')   # move + click + type
    """

    def __init__(self, page: Page):
        self._page = page
        # Track the actual mouse position so subsequent moves start correctly
        self._x: float = random.uniform(200, 600)
        self._y: float = random.uniform(200, 400)

    # ── Public API ──────────────────────────────────────────────────────

    async def move_to(self, x: float, y: float, duration: Optional[float] = None) -> None:
        """Move mouse to absolute (x, y) along a Bezier curve."""
        if duration is None:
            # Duration proportional to distance (0.4 – 1.2 s)
            dist = math.hypot(x - self._x, y - self._y)
            duration = max(0.4, min(1.2, dist / 800))

        points = self._bezier_path(self._x, self._y, x, y)
        timings = self._ease_in_out_timings(len(points), duration)

        for (px, py), dt in zip(points, timings):
            await self._page.mouse.move(px, py)
            await asyncio.sleep(dt)

        # Overshoot + correct (~25 % of the time)
        if random.random() < 0.25:
            overshoot = random.uniform(3, 12)
            ox = x + random.uniform(-overshoot, overshoot)
            oy = y + random.uniform(-overshoot, overshoot)
            await self._page.mouse.move(ox, oy)
            await asyncio.sleep(random.uniform(0.04, 0.08))
            await self._page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.02, 0.05))

        self._x, self._y = x, y

    async def move_to_element(self, selector: str) -> None:
        """Move mouse to a random point inside the element's bounding box."""
        box = await self._get_box(selector)
        if not box:
            return
        # Don't aim for the dead center — humans never do
        tx = box['x'] + box['width'] * random.uniform(0.25, 0.75)
        ty = box['y'] + box['height'] * random.uniform(0.30, 0.70)
        await self.move_to(tx, ty)

    async def click(self) -> None:
        """Click at the current mouse position."""
        await asyncio.sleep(random.uniform(0.05, 0.15))  # reaction time
        await self._page.mouse.down()
        await asyncio.sleep(random.uniform(0.04, 0.12))   # hold duration
        await self._page.mouse.up()

    async def click_element(self, selector: str) -> None:
        """Move to element, then click."""
        await self.move_to_element(selector)
        await self.click()

    async def type_into(self, selector: str, text: str, wpm: Optional[float] = None) -> None:
        """
        Move to an input field, click it, then type with human-like rhythm.

        Includes variable speed, occasional typos + backspace corrections,
        and natural pauses between words.
        """
        await self.click_element(selector)
        await asyncio.sleep(random.uniform(0.15, 0.35))
        await self._type_human(text, wpm)

    async def scroll(self, distance: int, duration: Optional[float] = None) -> None:
        """
        Scroll using the mouse wheel (not ``window.scrollBy``).

        Mouse-wheel events are what LinkedIn expects from real users.
        ``window.scrollBy`` calls are trivially detectable.

        Args:
            distance: Pixels to scroll (positive = down, negative = up).
            duration: Total time for the scroll gesture.
        """
        if duration is None:
            duration = random.uniform(0.8, 1.8)

        # Break into realistic "notches" — a real scroll wheel sends
        # discrete events of ~100 px each
        notch_size = random.randint(80, 120)
        notches = max(1, abs(distance) // notch_size)
        direction = 1 if distance > 0 else -1
        remainder = abs(distance) - notches * notch_size

        delays = self._ease_in_out_timings(notches, duration)

        for i, dt in enumerate(delays):
            delta = direction * notch_size
            # Last notch gets the remainder
            if i == notches - 1 and remainder > 0:
                delta += direction * remainder
            await self._page.mouse.wheel(0, delta)
            await asyncio.sleep(dt)

    async def scroll_with_momentum(self, target_distance: int) -> None:
        """
        Scroll with realistic momentum pattern.

        Mimics natural scrolling:
        1. Start slow (finger/wrist building up)
        2. Speed up in middle (fluid motion)
        3. Slow down at end (deceleration/stopping)

        Adds variable scroll segment sizes to avoid detection of
        perfectly uniform scroll increments.

        Args:
            target_distance: Total pixels to scroll (positive = down)
        """
        if target_distance == 0:
            return

        direction = 1 if target_distance > 0 else -1
        remaining = abs(target_distance)

        # Divide into 4-8 segments with momentum curve
        num_segments = random.randint(4, 8)
        segment_base = remaining / num_segments

        # Generate momentum weights: slow → fast → slow
        # Using sine curve for natural acceleration/deceleration
        weights = []
        for i in range(num_segments):
            # 0 to pi gives: 0 → 1 → 0 (sine curve)
            t = (i + 0.5) / num_segments * math.pi
            weight = 0.3 + 0.7 * math.sin(t)  # Range: 0.3 to 1.0
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        for i, weight in enumerate(weights):
            # Calculate segment distance with some randomness
            segment_distance = int(remaining * weight * random.uniform(0.85, 1.15))
            segment_distance = max(50, min(segment_distance, remaining))

            # Scroll this segment
            await self._page.mouse.wheel(0, direction * segment_distance)
            remaining -= segment_distance

            if remaining <= 0:
                break

            # Delay between segments (shorter in middle, longer at start/end)
            if i < num_segments // 3:
                # Starting: longer pauses
                delay = random.uniform(0.12, 0.25)
            elif i > 2 * num_segments // 3:
                # Ending: longer pauses
                delay = random.uniform(0.15, 0.30)
            else:
                # Middle: quick, fluid
                delay = random.uniform(0.05, 0.12)

            await asyncio.sleep(delay)

        # Handle any remaining distance
        if remaining > 0:
            await self._page.mouse.wheel(0, direction * remaining)

    async def reading_scan(self, page_height: int = 400) -> None:
        """
        Simulate small jittery movements while "reading" content.

        Real users don't hold the mouse perfectly still - there are
        micro-movements as they scan text with their eyes.

        Args:
            page_height: Approximate height of content being read
        """
        # Small scroll jitters (1-3 micro-scrolls)
        num_jitters = random.randint(1, 3)
        for _ in range(num_jitters):
            # Very small scroll (reading adjustment)
            jitter_distance = random.randint(-30, 50)
            if jitter_distance != 0:
                await self._page.mouse.wheel(0, jitter_distance)
            await asyncio.sleep(random.uniform(0.8, 2.5))

    # ── Bezier path generation ──────────────────────────────────────────

    def _bezier_path(
        self, x0: float, y0: float, x1: float, y1: float, steps: int = 0
    ) -> List[Tuple[float, float]]:
        """Generate a cubic Bezier path with random control points."""
        dist = math.hypot(x1 - x0, y1 - y0)
        if steps == 0:
            steps = max(15, min(60, int(dist / 10)))

        # Two random control points to make the curve feel "natural"
        spread = max(30, dist * 0.3)
        cx1 = x0 + (x1 - x0) * random.uniform(0.15, 0.40) + random.uniform(-spread, spread)
        cy1 = y0 + (y1 - y0) * random.uniform(0.15, 0.40) + random.uniform(-spread, spread)
        cx2 = x0 + (x1 - x0) * random.uniform(0.60, 0.85) + random.uniform(-spread, spread)
        cy2 = y0 + (y1 - y0) * random.uniform(0.60, 0.85) + random.uniform(-spread, spread)

        points: List[Tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            # Cubic Bezier formula:  B(t) = (1-t)^3·P0 + 3(1-t)^2·t·P1 + 3(1-t)·t^2·P2 + t^3·P3
            u = 1 - t
            px = u**3 * x0 + 3 * u**2 * t * cx1 + 3 * u * t**2 * cx2 + t**3 * x1
            py = u**3 * y0 + 3 * u**2 * t * cy1 + 3 * u * t**2 * cy2 + t**3 * y1
            # Add micro-jitter (± 0.5 px) to avoid perfectly smooth paths
            px += random.uniform(-0.5, 0.5)
            py += random.uniform(-0.5, 0.5)
            points.append((px, py))

        return points

    # ── Easing ──────────────────────────────────────────────────────────

    @staticmethod
    def _ease_in_out_timings(n: int, total: float) -> List[float]:
        """
        Distribute ``total`` seconds across ``n`` steps with ease-in-out.

        Start slow, accelerate through the middle, slow down at the end —
        exactly like a human arm movement.
        """
        if n <= 0:
            return []
        # Use a sine-based easing curve
        raw = []
        for i in range(n):
            t = i / max(n - 1, 1)
            # ease-in-out: slow start/end, fast middle
            weight = 1 - math.cos(math.pi * t)  # 0 → 2 → 0
            raw.append(max(weight, 0.15))  # Floor so we don't stall

        total_weight = sum(raw)
        return [w / total_weight * total for w in raw]

    # ── Typing ──────────────────────────────────────────────────────────

    async def _type_human(self, text: str, wpm: Optional[float] = None) -> None:
        """Type text character-by-character with human-like rhythm."""
        if wpm is None:
            wpm = random.uniform(45, 85)

        base_delay = 60 / (wpm * 5)  # seconds per character (assuming 5 chars/word)

        for i, ch in enumerate(text):
            # Variable per-key delay
            delay = base_delay * random.uniform(0.6, 1.4)

            # Spaces get a slightly longer pause (word boundary)
            if ch == ' ':
                delay *= random.uniform(1.3, 2.0)

            if len(ch) == 1:
                await self._page.keyboard.type(ch, delay=0)
            await asyncio.sleep(delay)

            # Occasional typo + correction (4 % chance, not on spaces)
            if ch != ' ' and random.random() < 0.04:
                wrong = random.choice('abcdefghijklmnopqrstuvwxyz')
                await self._page.keyboard.type(wrong, delay=0)
                await asyncio.sleep(random.uniform(0.15, 0.35))  # notice mistake
                await self._page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.08, 0.18))

        # Reviewing pause after finishing typing
        await asyncio.sleep(random.uniform(0.5, 1.5))

    # ── Helpers ─────────────────────────────────────────────────────────

    async def _get_box(self, selector: str) -> Optional[dict]:
        """Get bounding box for selector, return None on failure."""
        try:
            loc = self._page.locator(selector).first
            box = await loc.bounding_box()
            return box
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
# Legacy GhostCursorIntegration wrapper (used by connection_extractor.py)
# ─────────────────────────────────────────────────────────────────────────────

class GhostCursorIntegration:
    """
    Static-method wrapper around GhostCursor for backward compatibility.

    The connection_extractor and other modules call:
        await GhostCursorIntegration.click_naturally(page, selector)

    This now delegates to the full GhostCursor implementation.
    """

    @staticmethod
    async def move_to_element_naturally(
        page: Page, selector: str, duration: float = 1.0
    ) -> None:
        """Move mouse to element with natural Bezier path."""
        cursor = GhostCursor(page)
        await cursor.move_to_element(selector)

    @staticmethod
    async def click_naturally(page: Page, selector: str) -> None:
        """Move to element and click with natural movement."""
        cursor = GhostCursor(page)
        await cursor.click_element(selector)

    @staticmethod
    async def type_naturally(
        page: Page, selector: str, text: str, wpm: Optional[float] = None
    ) -> None:
        """Move to input, click it, then type with human rhythm."""
        cursor = GhostCursor(page)
        await cursor.type_into(selector, text, wpm)

    @staticmethod
    async def scroll_naturally(page: Page, distance: int) -> None:
        """Scroll using mouse wheel events."""
        cursor = GhostCursor(page)
        await cursor.scroll(distance)


# ─────────────────────────────────────────────────────────────────────────────
# HumanBehaviorEngine (session management, rate limiting, dwell time)
# ─────────────────────────────────────────────────────────────────────────────

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
    MIN_BREAK_MINUTES = 120   # 2 hours
    MAX_BREAK_MINUTES = 360   # 6 hours

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
        """Check if should take a break based on session length."""
        if not self.session_start:
            return False
        session_duration = (datetime.now() - self.session_start).total_seconds() / 60
        max_session = random.uniform(self.MIN_SESSION_MINUTES, self.MAX_SESSION_MINUTES)
        return session_duration >= max_session

    def get_break_duration(self) -> int:
        """Get break duration in seconds (2-6 hours)."""
        minutes = random.uniform(self.MIN_BREAK_MINUTES, self.MAX_BREAK_MINUTES)
        return int(minutes * 60)

    def should_take_micro_break(self, messages_sent: int) -> bool:
        """Check if should take a micro-break (every 15-25 actions)."""
        if messages_sent > 0 and messages_sent % random.randint(15, 25) == 0:
            return True
        return False

    def get_micro_break_duration(self) -> int:
        """Get micro-break duration (30-60 minutes)."""
        return random.randint(1800, 3600)

    # ===== Profile Viewing Behavior =====

    def get_profile_dwell_time(self, profile_complexity: str = 'medium') -> float:
        """Get realistic profile dwell time based on content."""
        if profile_complexity == 'simple':
            return random.uniform(20, 35)
        elif profile_complexity == 'complex':
            return random.uniform(50, 60)
        else:
            return random.uniform(35, 50)

    async def simulate_profile_reading(self, page: Page, profile_complexity: str = 'medium') -> None:
        """
        Simulate human reading pattern on a profile using mouse-wheel scrolling.
        """
        dwell_time = self.get_profile_dwell_time(profile_complexity)
        cursor = GhostCursor(page)

        # 1. Pause at top (read headline)
        await asyncio.sleep(random.uniform(2, 4))

        # 2. Scroll down to experience section
        await cursor.scroll(300, duration=1.5)
        await asyncio.sleep(random.uniform(3, 6))

        # 3. Continue scrolling through experience
        await cursor.scroll(400, duration=2)
        await asyncio.sleep(random.uniform(4, 7))

        # 4. Occasionally scroll back up (re-reading)
        if random.random() < 0.3:
            await cursor.scroll(-200, duration=1)
            await asyncio.sleep(random.uniform(2, 3))

        # 5. Scroll to education/skills
        await cursor.scroll(300, duration=1.5)
        await asyncio.sleep(random.uniform(2, 4))

        # 6. Final decision pause
        remaining_time = dwell_time - 15
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)

    # ===== Search/Browse Behavior =====

    async def simulate_search_browsing(self, page: Page, profiles_to_view: int) -> list[int]:
        """Generate non-linear browsing pattern (skip some profiles, etc.)."""
        total_visible = profiles_to_view * 3
        selected_indices = []
        current_position = 0

        while len(selected_indices) < profiles_to_view and current_position < total_visible:
            skip = random.randint(0, 3)
            current_position += skip
            if current_position < total_visible:
                selected_indices.append(current_position)
                current_position += 1
                if random.random() < 0.2:
                    current_position += random.randint(2, 5)

        return selected_indices

    # ===== Message Typing (legacy — prefer GhostCursor.type_into) =====

    async def type_message_humanlike(
        self, page: Page, selector: str, message: str, wpm: Optional[int] = None
    ) -> None:
        """Type a message with realistic human typing pattern (legacy wrapper)."""
        cursor = GhostCursor(page)
        await cursor.type_into(selector, message, wpm=wpm)

    # ===== Delay Utilities =====

    def get_delay_between_messages(self) -> float:
        """Random delay between messages (30s - 5min, mode ~90s)."""
        return random.triangular(30, 300, 90)

    def get_delay_between_profiles(self) -> float:
        """Delay between viewing profiles (10-30s)."""
        return random.uniform(10, 30)

    # ===== Working Hours =====

    def is_working_hours(self, timezone: str = 'America/Los_Angeles') -> bool:
        """Check if current time is working hours (8am - 8pm)."""
        try:
            import pytz
            tz = pytz.timezone(timezone)
            user_time = datetime.now(tz)
            return 8 <= user_time.hour <= 20
        except Exception:
            hour = datetime.now().hour
            return 8 <= hour <= 20

    def is_weekday(self) -> bool:
        """Check if today is a weekday (Mon-Fri)."""
        return datetime.now().weekday() < 5

    # ===== Rate Limiting =====

    def should_send_message(
        self, messages_sent_today: int, daily_limit: int = 50
    ) -> Tuple[bool, Optional[str]]:
        """Check if should send another message based on rate limits."""
        if messages_sent_today >= daily_limit:
            return False, f"Daily limit reached ({daily_limit})"
        if not self.is_working_hours():
            return False, "Outside working hours (8am-8pm)"
        if not self.is_weekday():
            return False, "Weekend - no sending"
        if self.should_take_break():
            return False, "Session limit reached - need break"
        return True, None
