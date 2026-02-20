#!/usr/bin/env python3
"""
Live test of LinkedIn connection extraction with hardened behavior.

Uses credential authentication (email/password) to test the full extraction
flow with cautious mode enabled.

Usage:
    python test_extraction_live.py [--cautious] [--max-connections N]

Options:
    --cautious          Use cautious mode (2x slower, more idle pauses)
    --max-connections   Stop after extracting N connections (default: 50)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.linkedin.stealth_browser import StealthBrowser
from app.services.linkedin.human_behavior import (
    GhostCursor,
    IdlePatternGenerator,
    ExtractionConfig,
    ExtractionMode,
)
from app.services.linkedin.credential_auth import LinkedInCredentialAuth, LoginState


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Live test of LinkedIn connection extraction"
    )
    parser.add_argument(
        "--cautious",
        action="store_true",
        help="Use cautious mode (2x slower, more idle pauses)"
    )
    parser.add_argument(
        "--max-connections",
        type=int,
        default=50,
        help="Stop after extracting N connections (default: 50)"
    )
    return parser.parse_args()


async def test_live_extraction(cautious_mode: bool = False, max_connections: int = 50):
    """
    Run live extraction test with hardened behavior.

    Args:
        cautious_mode: Use extra-safe timing
        max_connections: Stop after this many connections
    """
    print("=" * 70)
    print("LIVE EXTRACTION TEST - Hardened Behavior")
    print("=" * 70)

    mode = ExtractionMode.CAUTIOUS if cautious_mode else ExtractionMode.NORMAL
    config = ExtractionConfig.from_mode(mode)

    print(f"\nMode: {'CAUTIOUS' if cautious_mode else 'NORMAL'}")
    print(f"Scroll delays: {config.scroll_delay_min}-{config.scroll_delay_max}s")
    print(f"Read pauses: {config.read_pause_min}-{config.read_pause_max}s")
    print(f"Warmup connections: {config.warmup_connections}")
    print(f"Back-scroll chance: {config.back_scroll_chance * 100:.0f}%")
    print(f"Card inspection chance: {config.card_inspection_chance * 100:.0f}%")
    print(f"Max connections to extract: {max_connections}")

    # Get credentials
    email = os.environ.get('LINKEDIN_TEST_EMAIL')
    password = os.environ.get('LINKEDIN_TEST_PASSWORD')

    if not email or not password:
        print("\n❌ LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD must be set in .env")
        return

    print(f"\nUsing account: {email}")

    # Initialize idle pattern generator
    idle_gen = IdlePatternGenerator(frequency_multiplier=config.idle_frequency_multiplier)
    idle_gen.start_session()

    # Stats tracking
    stats = {
        'connections_found': 0,
        'idle_events': {
            'phone_check': 0,
            'thinking_pause': 0,
            'distraction': 0,
            'mini_break': 0,
        },
        'card_inspections': 0,
        'back_scrolls': 0,
        'momentum_scrolls': 0,
        'start_time': datetime.now(),
    }

    async with StealthBrowser.launch_persistent(
        session_id="live_extraction_test",
        headless=False
    ) as sb:
        page = await sb.new_page()

        # Step 1: Authenticate
        print("\n" + "-" * 70)
        print("STEP 1: Authentication")
        print("-" * 70)

        auth = LinkedInCredentialAuth()

        # Navigate to LinkedIn
        await page.goto("https://www.linkedin.com/login", wait_until="load", timeout=30000)
        await asyncio.sleep(2)

        # Handle login states
        max_iterations = 10
        for iteration in range(max_iterations):
            state = await auth._detect_login_state(page, email)
            print(f"Login state: {state}")

            if state == LoginState.LOGGED_IN:
                print("✅ Already logged in")
                break
            elif state == LoginState.WELCOME_BACK:
                clicked = await auth._handle_welcome_back(page, email)
                if not clicked:
                    await auth._click_sign_in_another_account(page)
                await page.wait_for_load_state("load", timeout=15000)
                await asyncio.sleep(2)
            elif state == LoginState.LOGIN_FORM:
                await auth._fill_login_form(page, email, password)
                await page.wait_for_load_state("load", timeout=15000)
                await asyncio.sleep(2)
            elif state == LoginState.PASSWORD_ONLY:
                await auth._fill_password_only(page, password)
                await page.wait_for_load_state("load", timeout=15000)
                await asyncio.sleep(2)
            elif state == LoginState.TWO_FA:
                print("⚠️  2FA required - please enter code manually in browser")
                print("   Waiting 60 seconds...")
                await asyncio.sleep(60)
            elif state == LoginState.ERROR:
                print("❌ Login error")
                await page.screenshot(path="login_error.png")
                return
            else:
                await asyncio.sleep(2)

        # Verify login
        if "/feed" not in page.url and "/mynetwork" not in page.url:
            print(f"⚠️  Current URL: {page.url}")
            print("   Waiting for manual login completion...")
            await asyncio.sleep(30)

        print(f"✅ Logged in, current URL: {page.url}")

        # Step 2: Navigate to connections
        print("\n" + "-" * 70)
        print("STEP 2: Navigate to Connections")
        print("-" * 70)

        # Natural navigation: feed → mynetwork → connections
        if "/feed" not in page.url:
            print("Navigating to feed first...")
            await page.goto("https://www.linkedin.com/feed/", wait_until="load", timeout=30000)
            await asyncio.sleep(3)

        # Browse feed briefly (natural behavior)
        cursor = GhostCursor(page)
        print("Browsing feed briefly...")
        await cursor.scroll(300)
        await asyncio.sleep(2)

        # Navigate to connections
        print("Navigating to connections...")
        await page.goto(
            "https://www.linkedin.com/mynetwork/invite-connect/connections/",
            wait_until="load",
            timeout=30000
        )
        await asyncio.sleep(5)

        if "/login" in page.url or "/checkpoint" in page.url:
            print("❌ Session invalid - redirected to login")
            return

        print(f"✅ Connections page loaded: {page.url}")

        # Step 3: Extract connections with hardened behavior
        print("\n" + "-" * 70)
        print("STEP 3: Extract Connections (Hardened Behavior)")
        print("-" * 70)

        connections = []
        seen_urls = set()
        no_new_count = 0
        import random

        while len(connections) < max_connections:
            # Extract visible connections
            cards_data = await page.evaluate(r'''() => {
                const connections = [];
                const seenUrls = new Set();

                const listContainer = document.querySelector('[data-view-name="connections-list"]');
                const searchRoot = listContainer || document;
                const cards = searchRoot.querySelectorAll('[componentkey^="auto-component-"]');

                cards.forEach(card => {
                    const profileLinks = card.querySelectorAll('a[href*="/in/"]');
                    if (profileLinks.length === 0) return;

                    const profileLink = profileLinks[0];
                    const url = profileLink.href?.split('?')[0];
                    if (!url || seenUrls.has(url)) return;
                    seenUrls.add(url);

                    let name = null;
                    for (const link of profileLinks) {
                        const innerA = link.querySelector('a');
                        if (innerA && innerA.textContent?.trim()) {
                            name = innerA.textContent.trim();
                            break;
                        }
                        const pWithA = link.querySelector('p a');
                        if (pWithA && pWithA.textContent?.trim()) {
                            name = pWithA.textContent.trim();
                            break;
                        }
                        const linkText = link.textContent?.trim();
                        if (linkText && linkText.length > 2 && linkText.length < 60) {
                            if (!linkText.includes(' | ') && !linkText.includes(' at ')) {
                                name = linkText;
                                break;
                            }
                        }
                    }

                    let headline = null;
                    const paragraphs = card.querySelectorAll('p');
                    for (const p of paragraphs) {
                        const text = p.textContent?.trim();
                        if (!text || text.length < 5 || text === name) continue;
                        if (text.startsWith('Connected')) continue;
                        if (/^(Message|Connect|Follow)$/i.test(text)) continue;
                        if (!headline && text.length >= 10 && text.length <= 200) {
                            headline = text;
                        }
                    }

                    if (!name) {
                        const figure = card.querySelector('figure[aria-label]');
                        if (figure) {
                            const ariaLabel = figure.getAttribute('aria-label');
                            if (ariaLabel?.includes("'s profile picture")) {
                                name = ariaLabel.replace("'s profile picture", "").trim();
                            }
                        }
                    }

                    if (name && name.length >= 2) {
                        connections.push({ name, headline, url });
                    }
                });

                return connections;
            }''')

            # Add new connections
            new_count = 0
            for card in cards_data:
                url = card.get('url')
                if url and url not in seen_urls:
                    connections.append(card)
                    seen_urls.add(url)
                    new_count += 1
                    idle_gen.record_connection()

            stats['connections_found'] = len(connections)

            # Check if done
            if new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    print(f"\nNo new connections after 3 scrolls - extraction complete")
                    break
            else:
                no_new_count = 0

            print(f"\rConnections: {len(connections)}/{max_connections} | "
                  f"Idle: {sum(stats['idle_events'].values())} | "
                  f"Back-scrolls: {stats['back_scrolls']} | "
                  f"Card inspections: {stats['card_inspections']}", end="", flush=True)

            # Calculate warmup multiplier
            warmup_mult = idle_gen.get_warmup_multiplier_by_count(config.warmup_connections)

            # Reading pause
            read_time = random.uniform(config.read_pause_min, config.read_pause_max) * warmup_mult
            await asyncio.sleep(read_time)

            # Run idle checks
            idle_event = await idle_gen.run_idle_check(page)
            if idle_event != "none":
                stats['idle_events'][idle_event] = stats['idle_events'].get(idle_event, 0) + 1
                print(f"\n  [Idle: {idle_event}]")

            # Card inspection
            if random.random() < config.card_inspection_chance:
                inspected = await idle_gen.inspect_random_card(page)
                if inspected:
                    stats['card_inspections'] += 1

            # Scroll
            use_momentum = random.random() < 0.40
            if use_momentum:
                await cursor.scroll_with_momentum(random.randint(500, 800))
                stats['momentum_scrolls'] += 1
            else:
                await cursor.scroll(random.randint(500, 800))

            # Wait for content
            await asyncio.sleep(1)

            # Scroll delay
            delay = random.uniform(config.scroll_delay_min, config.scroll_delay_max) * warmup_mult
            await asyncio.sleep(delay)

            # Back-scroll
            if random.random() < config.back_scroll_chance:
                back_distance = random.randint(-150, -350)
                await cursor.scroll(back_distance)
                await asyncio.sleep(random.uniform(1.5, 3.5))
                stats['back_scrolls'] += 1

                # Reading scan after back-scroll
                if random.random() < 0.3:
                    await cursor.reading_scan()

        # Step 4: Results
        print("\n\n" + "-" * 70)
        print("STEP 4: Results")
        print("-" * 70)

        duration = (datetime.now() - stats['start_time']).total_seconds()

        print(f"\n✅ Extraction complete!")
        print(f"\nStats:")
        print(f"  Connections extracted: {len(connections)}")
        print(f"  Duration: {duration:.1f}s ({duration/60:.1f} min)")
        print(f"  Rate: {len(connections) / (duration/60):.1f} connections/min")
        print(f"\nIdle events:")
        for event, count in stats['idle_events'].items():
            print(f"  {event}: {count}")
        print(f"\nBehavior:")
        print(f"  Back-scrolls: {stats['back_scrolls']}")
        print(f"  Card inspections: {stats['card_inspections']}")
        print(f"  Momentum scrolls: {stats['momentum_scrolls']}")

        print(f"\nSample connections:")
        for conn in connections[:10]:
            print(f"  - {conn['name']}")
            if conn.get('headline'):
                print(f"    {conn['headline'][:60]}...")

        if len(connections) > 10:
            print(f"  ... and {len(connections) - 10} more")

        # Save results
        results = {
            'mode': 'CAUTIOUS' if cautious_mode else 'NORMAL',
            'connections': connections,
            'stats': {
                'total': len(connections),
                'duration_seconds': duration,
                'idle_events': stats['idle_events'],
                'back_scrolls': stats['back_scrolls'],
                'card_inspections': stats['card_inspections'],
            }
        }

        with open('live_extraction_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Results saved to: live_extraction_results.json")

        # Screenshot
        await page.screenshot(path="live_extraction_final.png", full_page=True)
        print(f"📸 Screenshot saved: live_extraction_final.png")

        # Keep browser open briefly
        print("\nKeeping browser open for 5 seconds...")
        await asyncio.sleep(5)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(test_live_extraction(
        cautious_mode=args.cautious,
        max_connections=args.max_connections
    ))
