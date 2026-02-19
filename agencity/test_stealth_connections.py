#!/usr/bin/env python3
"""
Integration test: Stealth browser + natural navigation → connection extraction.

This test verifies that the new StealthBrowser module and natural navigation
chain can:

  1. Launch a stealth browser with a persistent profile
  2. Load cookies from an existing session
  3. Navigate feed → mynetwork → connections (natural chain)
  4. Reach the connections page *without* being redirected to login
  5. Extract at least some connection data

Usage
-----

  # Option A — use an existing session ID from Supabase:
  export LINKEDIN_SESSION_ID="<uuid>"
  python test_stealth_connections.py

  # Option B — use saved cookies directly (JSON file):
  python test_stealth_connections.py --cookies cookies.json

  # Option C — authenticate first, then extract:
  export LINKEDIN_TEST_EMAIL="your@email.com"
  export LINKEDIN_TEST_PASSWORD="your-password"
  python test_stealth_connections.py --login

  # Run a specific phase only:
  python test_stealth_connections.py --phase stealth    # Just test stealth evasion
  python test_stealth_connections.py --phase nav        # Just test navigation chain
  python test_stealth_connections.py --phase extract    # Full extraction
"""

import asyncio
import argparse
import json
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project root is on sys.path so `app.*` imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.linkedin.stealth_browser import StealthBrowser
from app.services.linkedin.human_behavior import GhostCursor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cookies_dict_to_list(cookies: dict) -> list:
    """Convert {name: {value, domain, ...}} → [{name, value, domain, ...}]."""
    result = []
    for name, data in cookies.items():
        cookie = {
            'name': name,
            'value': data['value'],
            'domain': data.get('domain', '.linkedin.com'),
            'path': data.get('path', '/'),
            'secure': data.get('secure', True),
            'httpOnly': data.get('httpOnly', False),
        }
        if data.get('expirationDate'):
            cookie['expires'] = data['expirationDate']
        result.append(cookie)
    return result


async def _get_cookies_from_session(session_id: str) -> dict:
    """Fetch and decrypt cookies from Supabase for the given session."""
    from app.services.linkedin.session_manager import LinkedInSessionManager
    mgr = LinkedInSessionManager()
    cookies = await mgr.get_session_cookies(session_id)
    if not cookies:
        raise RuntimeError(f"Session {session_id} not found or expired")
    return cookies


async def _authenticate(email: str, password: str) -> dict:
    """Log in to LinkedIn and return cookies."""
    from app.services.linkedin.credential_auth import LinkedInCredentialAuth
    auth = LinkedInCredentialAuth()
    result = await auth.login(email=email, password=password)

    if result['status'] == '2fa_required':
        code = input("Enter 2FA code: ").strip()
        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state'),
        )

    if result['status'] != 'connected':
        raise RuntimeError(f"Login failed: {result.get('error', result)}")

    return result['cookies']


# ─────────────────────────────────────────────────────────────────────────────
# Phase 0 — Ghost cursor visual test
# ─────────────────────────────────────────────────────────────────────────────

async def test_ghost_cursor():
    """
    Visual test: watch the ghost cursor move, type, and scroll on a real page.

    Opens a browser with a simple HTML form, then:
      1. Moves the mouse along a Bezier curve to the first input
      2. Clicks and types into it with human rhythm (typos, variable speed)
      3. Tabs to the next field and types again
      4. Scrolls down using mouse-wheel events
      5. Clicks a button
    """
    logger.info("=" * 60)
    logger.info("PHASE 0: Ghost cursor visual test")
    logger.info("=" * 60)

    async with StealthBrowser.launch(headless=False) as sb:
        page = await sb.new_page()

        # Create a local test page with form fields so we can see the cursor
        await page.set_content('''
        <html>
        <head>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f3f2ef; color: #333;
                    display: flex; justify-content: center; padding-top: 60px;
                }
                .card {
                    background: white; border-radius: 12px; padding: 40px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.12); width: 440px;
                }
                h2 { margin-bottom: 24px; font-size: 22px; }
                label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 14px; }
                input, textarea {
                    width: 100%; padding: 10px 14px; border: 1px solid #ccc;
                    border-radius: 6px; font-size: 15px; margin-bottom: 18px;
                    transition: border-color 0.2s;
                }
                input:focus, textarea:focus { outline: none; border-color: #0a66c2; }
                textarea { height: 100px; resize: vertical; }
                button {
                    background: #0a66c2; color: white; border: none;
                    padding: 12px 28px; border-radius: 24px; font-size: 16px;
                    font-weight: 600; cursor: pointer; width: 100%;
                }
                button:hover { background: #004182; }
                .spacer { height: 600px; }
                #status {
                    margin-top: 18px; padding: 12px; border-radius: 6px;
                    background: #e8f5e9; color: #2e7d32; font-weight: 600;
                    display: none; text-align: center;
                }
                /* Cursor trail visualization */
                .trail {
                    position: fixed; width: 8px; height: 8px;
                    border-radius: 50%; background: rgba(10, 102, 194, 0.3);
                    pointer-events: none; z-index: 9999;
                    transition: opacity 1.5s;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🖱️ Ghost Cursor Test</h2>
                <label for="name">Full Name</label>
                <input type="text" id="name" placeholder="Enter your name...">
                <label for="email">Email Address</label>
                <input type="email" id="email" placeholder="Enter your email...">
                <label for="message">Message</label>
                <textarea id="message" placeholder="Type a message..."></textarea>
                <button id="submit" onclick="document.getElementById('status').style.display='block'">
                    Submit
                </button>
                <div id="status">✅ Form submitted successfully!</div>
                <div class="spacer"></div>
            </div>
            <script>
                // Visualize mouse trail
                document.addEventListener('mousemove', (e) => {
                    const dot = document.createElement('div');
                    dot.className = 'trail';
                    dot.style.left = (e.clientX - 4) + 'px';
                    dot.style.top = (e.clientY - 4) + 'px';
                    document.body.appendChild(dot);
                    setTimeout(() => { dot.style.opacity = '0'; }, 100);
                    setTimeout(() => dot.remove(), 1600);
                });
            </script>
        </body>
        </html>
        ''')
        await asyncio.sleep(1)

        cursor = GhostCursor(page)

        # 1. Move to name field and type
        logger.info("  Moving to name field and typing...")
        await cursor.type_into('#name', 'Aidan Nguyen')
        await asyncio.sleep(0.5)

        # 2. Move to email field and type
        logger.info("  Moving to email field and typing...")
        await cursor.type_into('#email', 'aidan@proofhire.com')
        await asyncio.sleep(0.5)

        # 3. Move to message field and type
        logger.info("  Moving to message field and typing...")
        await cursor.type_into('#message', 'Testing the ghost cursor integration')
        await asyncio.sleep(0.5)

        # 4. Scroll down using mouse wheel
        logger.info("  Scrolling down with mouse wheel...")
        await cursor.scroll(400)
        await asyncio.sleep(1)

        # 5. Scroll back up
        logger.info("  Scrolling back up...")
        await cursor.scroll(-300)
        await asyncio.sleep(0.5)

        # 6. Click the submit button
        logger.info("  Clicking submit button...")
        await cursor.click_element('#submit')
        await asyncio.sleep(2)

        # Take screenshot
        screenshot_path = f"ghost_cursor_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"  Screenshot saved: {screenshot_path}")

        # Verify the form was filled
        name_val = await page.input_value('#name')
        email_val = await page.input_value('#email')
        msg_val = await page.input_value('#message')

        logger.info(f"  Name field: '{name_val}'")
        logger.info(f"  Email field: '{email_val}'")
        logger.info(f"  Message field: '{msg_val}'")

        passed = bool(name_val and email_val and msg_val)
        if passed:
            logger.info("  ✅ Ghost cursor test passed — all fields filled!")
        else:
            logger.warning("  ❌ Ghost cursor test failed — some fields empty")

        return passed


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Stealth evasion check
# ─────────────────────────────────────────────────────────────────────────────

async def test_stealth_evasion():
    """
    Launch a stealth browser and verify that key detection vectors are hidden.
    """
    logger.info("=" * 60)
    logger.info("PHASE 1: Stealth evasion check")
    logger.info("=" * 60)

    async with StealthBrowser.launch(headless=False) as sb:
        page = await sb.new_page()

        # Navigate to a bot-detection test page
        await page.goto('https://bot.sannysoft.com/', wait_until='load', timeout=30000)
        await asyncio.sleep(3)

        # Check navigator.webdriver
        webdriver = await page.evaluate('navigator.webdriver')
        logger.info(f"  navigator.webdriver = {webdriver}  {'✅' if not webdriver else '❌'}")

        # Check chrome.runtime
        chrome_runtime = await page.evaluate('typeof window.chrome !== "undefined"')
        logger.info(f"  window.chrome exists = {chrome_runtime}  {'✅' if chrome_runtime else '❌'}")

        # Check plugins
        plugins_count = await page.evaluate('navigator.plugins.length')
        logger.info(f"  navigator.plugins.length = {plugins_count}  {'✅' if plugins_count > 0 else '❌'}")

        # Check hardware concurrency
        cores = await page.evaluate('navigator.hardwareConcurrency')
        logger.info(f"  hardwareConcurrency = {cores}  {'✅' if cores >= 4 else '❌'}")

        # Take screenshot for visual confirmation
        screenshot_path = f"stealth_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"  Screenshot saved: {screenshot_path}")

        passed = (not webdriver) and chrome_runtime and (plugins_count > 0) and (cores >= 4)
        if passed:
            logger.info("  ✅ All stealth checks passed!")
        else:
            logger.warning("  ⚠️  Some stealth checks failed — review screenshot")

        return passed


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Natural navigation chain
# ─────────────────────────────────────────────────────────────────────────────

async def test_navigation_chain(cookies: dict, session_id: str = 'test-session'):
    """
    Test the natural navigation: feed → mynetwork → connections.

    This is the critical test — if the connections page loads without
    redirecting to login, the session invalidation issue is resolved.
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: Natural navigation chain")
    logger.info("=" * 60)

    cookie_list = _cookies_dict_to_list(cookies)

    async with StealthBrowser.launch_persistent(
        session_id=session_id,
        headless=False,
    ) as sb:
        # Inject cookies
        await sb.context.add_cookies(cookie_list)
        page = await sb.new_page()

        results = {}

        # Step 1: Feed
        logger.info("  Step 1: Navigating to /feed ...")
        await page.goto('https://www.linkedin.com/feed/', wait_until='load', timeout=30000)
        await asyncio.sleep(3)
        feed_url = page.url
        feed_ok = '/feed' in feed_url and '/login' not in feed_url
        results['feed'] = feed_ok
        logger.info(f"    URL: {feed_url}")
        logger.info(f"    Result: {'✅ Feed loaded' if feed_ok else '❌ Redirected to login'}")

        if not feed_ok:
            logger.error("  Cannot continue — not logged in")
            return results

        # Brief pause (simulate reading)
        await asyncio.sleep(2)

        # Step 2: My Network
        logger.info("  Step 2: Navigating to /mynetwork ...")
        await page.goto('https://www.linkedin.com/mynetwork/', wait_until='load', timeout=30000)
        await asyncio.sleep(3)
        network_url = page.url
        network_ok = '/login' not in network_url
        results['mynetwork'] = network_ok
        logger.info(f"    URL: {network_url}")
        logger.info(f"    Result: {'✅ My Network loaded' if network_ok else '❌ Redirected to login'}")

        if not network_ok:
            logger.error("  Session invalidated at My Network — stopping")
            return results

        await asyncio.sleep(2)

        # Step 3: Connections (the critical page)
        logger.info("  Step 3: Navigating to /connections ...")
        await page.goto(
            'https://www.linkedin.com/mynetwork/invite-connect/connections/',
            wait_until='load',
            timeout=30000
        )
        await asyncio.sleep(3)
        conn_url = page.url
        conn_ok = '/login' not in conn_url and '/checkpoint' not in conn_url
        results['connections'] = conn_ok
        logger.info(f"    URL: {conn_url}")
        logger.info(f"    Result: {'✅ Connections loaded!' if conn_ok else '❌ Redirected to login'}")

        # Take screenshot
        screenshot_path = f"nav_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"    Screenshot: {screenshot_path}")

        # Summary
        logger.info("")
        logger.info("  Navigation chain results:")
        for step, ok in results.items():
            logger.info(f"    {step}: {'✅' if ok else '❌'}")

        if all(results.values()):
            logger.info("  🎉 ALL STEPS PASSED — session invalidation issue may be resolved!")
        else:
            logger.warning("  ⚠️  Some steps failed — see details above")

        return results


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Full extraction
# ─────────────────────────────────────────────────────────────────────────────

async def test_full_extraction(session_id: str):
    """
    Test the full extraction flow using LinkedInConnectionExtractor.
    """
    logger.info("=" * 60)
    logger.info("PHASE 3: Full connection extraction")
    logger.info("=" * 60)

    from app.services.linkedin.session_manager import LinkedInSessionManager
    from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor

    mgr = LinkedInSessionManager()
    extractor = LinkedInConnectionExtractor(session_manager=mgr)

    async def progress(found, estimated):
        logger.info(f"    Progress: {found} connections found (est. {estimated})")

    result = await extractor.extract_connections(
        session_id=session_id,
        progress_callback=progress,
    )

    logger.info(f"  Status: {result['status']}")

    if result['status'] == 'success':
        logger.info(f"  ✅ Extracted {result['total']} connections in {result['duration_seconds']:.1f}s")
        # Print first 5
        for conn in result['connections'][:5]:
            logger.info(f"    - {conn['full_name']} | {conn['headline']} | {conn['linkedin_url']}")
        if result['total'] > 5:
            logger.info(f"    ... and {result['total'] - 5} more")
    else:
        logger.error(f"  ❌ Extraction failed: {result.get('error')}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description='Test stealth browser + connection extraction')
    parser.add_argument('--phase', choices=['cursor', 'stealth', 'nav', 'extract', 'all'], default='all',
                        help='Which phase to run (default: all)')
    parser.add_argument('--cookies', type=str, help='Path to cookies JSON file')
    parser.add_argument('--login', action='store_true', help='Authenticate first with env credentials')
    args = parser.parse_args()

    session_id = os.environ.get('LINKEDIN_SESSION_ID')
    cookies = None

    # ── Resolve cookies ──
    if args.cookies:
        with open(args.cookies) as f:
            cookies = json.load(f)
        logger.info(f"Loaded cookies from {args.cookies}")
    elif args.login:
        email = os.environ.get('LINKEDIN_TEST_EMAIL')
        password = os.environ.get('LINKEDIN_TEST_PASSWORD')
        if not email or not password:
            logger.error("Set LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD env vars")
            sys.exit(1)
        cookies = await _authenticate(email, password)
        logger.info("Authenticated — cookies obtained")
    elif session_id:
        cookies = await _get_cookies_from_session(session_id)
        logger.info(f"Loaded cookies from session {session_id}")

    # ── Run phases ──

    if args.phase in ('cursor', 'all'):
        await test_ghost_cursor()
        print()

    if args.phase in ('stealth', 'all'):
        await test_stealth_evasion()
        print()

    if args.phase in ('nav', 'all'):
        if not cookies:
            logger.error("Cookies required for navigation test. Use --cookies, --login, or set LINKEDIN_SESSION_ID")
            sys.exit(1)
        sid = session_id or 'test-stealth-session'
        await test_navigation_chain(cookies, session_id=sid)
        print()

    if args.phase in ('extract', 'all'):
        if not session_id:
            logger.error("LINKEDIN_SESSION_ID env var required for full extraction test")
            sys.exit(1)
        await test_full_extraction(session_id)
        print()

    logger.info("Done!")


if __name__ == '__main__':
    asyncio.run(main())
