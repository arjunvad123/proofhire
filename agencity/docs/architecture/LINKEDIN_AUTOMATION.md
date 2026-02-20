# LinkedIn Automation System

## Technical Architecture for Network Intelligence & Outreach

**Version 3.4** | February 2026 | Status: Multi-Account Architecture + Hardened Behavior

---

## Executive Summary

This document outlines Agencity's LinkedIn automation system that enables:
1. **Credential Authentication** - User enters email/password + 2FA code (no extension needed)
2. **Comet-Style Extraction** - Playwright-based automation with human behavior patterns
3. **Smart Enrichment** - Prioritize and enrich profiles using scraper pool
4. **DM Automation** - Send personalized outreach using user's session

**Key Differentiator**: Zero-friction onboarding (30 seconds) + Comet-inspired safety + smart prioritization that delivers actionable shortlists in 2 hours instead of 4 days.

**Architecture Philosophy**: Use **Playwright + playwright-stealth** with persistent browser profiles, **ghost cursor** for human behavior simulation, and comprehensive anti-detection measures. Conservative rate limits and warning detection minimize risk of account restrictions.

**Latest Update (v3.4)**:
- ✅ Multi-account isolation via `AccountManager` (email-hashed browser profiles)
- ✅ Hardened scrolling with idle patterns, warmup mode, momentum scrolling
- ✅ Configurable extraction modes (CAUTIOUS vs NORMAL)
- ⚠️ Known issue: First-time CAPTCHA on new browser profiles (see [Known Issues](#known-issues))

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Multi-Account Architecture](#2-multi-account-architecture)
3. [Stealth & Anti-Detection System](#3-stealth--anti-detection-system)
4. [Hardened Human Behavior](#4-hardened-human-behavior)
5. [Phase 1: Session Authentication](#5-phase-1-session-authentication)
6. [Phase 2: Connection Extraction](#6-phase-2-connection-extraction)
7. [Phase 3: Smart Prioritization](#7-phase-3-smart-prioritization)
8. [Phase 4: Profile Enrichment](#8-phase-4-profile-enrichment)
9. [Phase 5: DM Automation](#9-phase-5-dm-automation)
10. [Risk Mitigation](#10-risk-mitigation)
11. [Known Issues & Solutions](#11-known-issues--solutions)
12. [Database Schema](#12-database-schema)
13. [API Reference](#13-api-reference)
14. [Cost Analysis](#14-cost-analysis)
15. [Implementation & Testing Plan](#15-implementation--testing-plan)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER ONBOARDING                               │
│                        (30 seconds)                                  │
├─────────────────────────────────────────────────────────────────────┤
│  User Enters Credentials → Automated Login (Playwright)             │
│  → 2FA Code Entry (if required) → Extract Session Cookies           │
│  → Encrypt & Store → Backend Ready                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: AUTHENTICATE & CONNECT                   │
│                    (Fully Automated - LOW RISK)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Playwright + playwright-stealth (Residential Proxy)                │
│  → Login with credentials → Handle 2FA challenge                    │
│  → Extract session cookies (li_at, JSESSIONID)                      │
│  → Immediately discard password, store only encrypted cookies       │
│  → Time: ~30 seconds (instant with no 2FA)                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: EXTRACT CONNECTIONS                      │
│                    (Using User's Session - LOW RISK)                 │
├─────────────────────────────────────────────────────────────────────┤
│  User's Cookie + Persistent Browser Profile                         │
│  → Scroll /mynetwork/contacts with human-like delays                │
│  → Extract: Name, Title, Company, LinkedIn URL                      │
│  → Human Behavior: 1-3s scroll delays, occasional back-scroll       │
│  → Time: ~15 minutes for 3,637 connections                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: SMART PRIORITIZATION                     │
│                    (No LinkedIn Access Needed)                       │
├─────────────────────────────────────────────────────────────────────┤
│  Score connections based on:                                         │
│  • Title match to active roles (+30 pts)                            │
│  • Company prestige - FAANG/Unicorn (+25 pts)                       │
│  • Headline keyword match (+20 pts)                                 │
│  • Recent connection (+15 pts)                                      │
│  • Location match (+10 pts)                                         │
│                                                                      │
│  Output: Tier 1 (200) | Tier 2 (500) | Tier 3 (remaining)          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: PROFILE ENRICHMENT                       │
│                    (Using Scraper Pool - ZERO USER RISK)             │
├─────────────────────────────────────────────────────────────────────┤
│  Scraper Account Pool (10-20 accounts)                              │
│  → Each account: 100 profiles/day                                   │
│  → Residential proxies per account                                  │
│  → Extracts: Skills, Experience, Education, Projects                │
│                                                                      │
│  Tier 1: 200 profiles in ~2 hours (via Unipile or self-managed)    │
│  Tier 2-3: Background enrichment over 30 days                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 5: AI ANALYSIS & RANKING                    │
│                    (Kimi Agent Swarm)                                │
├─────────────────────────────────────────────────────────────────────┤
│  Four parallel agents analyze each candidate:                        │
│  • Skill Agent: Technical skill match (40% weight)                  │
│  • Trajectory Agent: Career progression (30% weight)                │
│  • Fit Agent: Culture/stage fit (20% weight)                        │
│  • Timing Agent: Readiness signals (10% weight)                     │
│                                                                      │
│  Output: Ranked shortlist of 15 candidates with reasoning           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 6: DM AUTOMATION                            │
│                    (Using User's Session - MEDIUM RISK)              │
├─────────────────────────────────────────────────────────────────────┤
│  Safe Limits:                                                        │
│  • 20-50 connection requests/day                                    │
│  • 50-100 messages/day to existing connections                      │
│  • Random delays: 30s - 5min between messages                       │
│  • Only during working hours (8am-8pm user timezone)                │
│                                                                      │
│  Protections:                                                        │
│  • Residential proxy matching user location                         │
│  • Human-like behavior simulation                                   │
│  • Immediate pause on LinkedIn warning                              │
│  • User approval required for each campaign                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Account Architecture

### Overview

**Status**: ✅ **IMPLEMENTED** (v3.4)

Each LinkedIn account gets a completely isolated browser profile, preventing cookie pollution between accounts. This is critical for:
- Server deployment managing multiple user accounts
- Testing with multiple accounts without cross-contamination
- Production reliability

### Architecture

```
browser_profiles/
├── 520a247abacf0f04/          # SHA256(account1@email.com)[:16]
│   └── Default/               # Chromium profile data
│       ├── Cookies
│       ├── Local Storage/
│       └── Cache/
├── 8f3a92b1c4d5e6f7/          # SHA256(account2@email.com)[:16]
│   └── Default/
└── account_metadata.json      # Tracks creation/last-used times
```

### AccountManager API

```python
from app.services.linkedin import AccountManager

mgr = AccountManager()

# Get profile ID from email (deterministic hash)
profile_id = AccountManager.get_profile_id("user@example.com")
# Returns: "520a247abacf0f04"

# Get profile path
path = mgr.get_profile_path("user@example.com")
# Returns: Path("./browser_profiles/520a247abacf0f04")

# Check if profile exists (already warmed up)
if mgr.profile_exists("user@example.com"):
    print("Profile is warmed - no CAPTCHA expected")

# Clear profile (reset, requires re-verification)
mgr.clear_profile("user@example.com")

# Delete profile completely
mgr.delete_profile("user@example.com")

# List all profiles with metadata
profiles = mgr.list_profiles()
# Returns: [{"profile_id": "520a...", "size_mb": 45.2, "last_used": "...", ...}]

# Cleanup old profiles (unused for 30+ days)
deleted_count = mgr.cleanup_old_profiles(days_unused=30)
```

### Integration with StealthBrowser

```python
from app.services.linkedin import AccountManager, StealthBrowser

# Get isolated profile ID for this user's email
profile_id = AccountManager.get_profile_id(user_email)

# Launch browser with isolated profile
async with StealthBrowser.launch_persistent(
    session_id=profile_id,  # Uses email hash, not arbitrary ID
    headless=False,
    user_location='San Francisco, CA'
) as sb:
    page = await sb.new_page()
    # This user's cookies are isolated from all other accounts
```

### Key Principles

1. **Email → Profile ID**: Deterministic hash ensures same email always maps to same profile
2. **No Cross-Pollution**: Each account's cookies/cache are completely isolated
3. **Preserve Warmed Profiles**: Never delete profiles that are already trusted by LinkedIn
4. **First-Time Verification**: New profiles require one-time CAPTCHA/email verification

---

## 3. Stealth & Anti-Detection System

### Overview

**Status**: ✅ **IMPLEMENTED & VERIFIED** (v3.3)

LinkedIn employs sophisticated bot detection mechanisms. Our stealth system successfully bypasses these checks, allowing reliable session persistence and page access without authentication redirects.

### Test Results

All stealth tests passing as of February 19, 2026:

| Test Phase | Result | Details |
|------------|--------|---------|
| **Ghost Cursor** | ✅ PASS | Natural Bezier curves, variable typing, mouse-wheel scroll |
| **Stealth Evasion** | ✅ PASS | navigator.webdriver=false, chrome.runtime exists, plugins visible |
| **Navigation Chain** | ✅ PASS | feed → mynetwork → connections (no login redirect) |
| **Connection Page** | ✅ PASS | Page loads, displays connections, no auth challenge |

### Components

#### 1. StealthBrowser (`app/services/linkedin/stealth_browser.py`)

Comprehensive browser automation framework with anti-detection built-in:

**Features:**
- **playwright-stealth** integration at context level
- **Persistent browser profiles** (maintains session state across runs)
- **Extra evasion scripts** injected automatically:
  - WebGL fingerprint randomization
  - Canvas fingerprint spoofing
  - Audio context masking
  - chrome.runtime injection
  - Navigator plugins simulation
  - Permissions API mocking
  - Language/timezone consistency
- **Dual launch modes**:
  - `launch()` - Ephemeral browser for quick tasks
  - `launch_persistent()` - Session-based profile for multi-step flows
- **Residential proxy support** with location-based routing

**Usage:**
```python
from app.services.linkedin.stealth_browser import StealthBrowser

# Ephemeral mode (no profile saved)
async with StealthBrowser.launch(headless=False) as sb:
    page = await sb.new_page()
    await page.goto('https://linkedin.com/feed')

# Persistent mode (profile saved to ./browser_profiles/{session_id}/)
async with StealthBrowser.launch_persistent(
    session_id='user-123',
    headless=False,
    user_location='San Francisco, CA'
) as sb:
    page = await sb.new_page()
    # Session state persists across runs
```

#### 2. GhostCursor (`app/services/linkedin/human_behavior.py`)

Human behavior simulation using pyppeteer-ghost-cursor:

**Features:**
- **Bezier curve mouse movements** (no straight lines between elements)
- **Natural typing rhythm**:
  - Variable speed (50-80 WPM)
  - Character-by-character with random delays
  - Occasional typos and corrections
  - Pauses between words
- **Mouse-wheel scrolling** (discrete notches matching physical scroll wheel)
- **Random delays** between all actions (300-1500ms)
- **Realistic click patterns**:
  - Slight overshoot (moves past target, then corrects)
  - Small random offset from element center
  - Natural click timing

**Usage:**
```python
from app.services.linkedin.human_behavior import GhostCursor

cursor = GhostCursor(page)

# Type into field naturally
await cursor.type_into('#email', 'user@example.com')

# Move and click with Bezier curve
await cursor.click_element('button[type="submit"]')

# Scroll like a human (mouse wheel, not programmatic)
await cursor.scroll(400)  # Scroll down 400px
```

#### 3. Enhanced Cookie Management

Proper cookie handling prevents session invalidation:

**Key Improvements:**
- Correct domain configuration (`.www.linkedin.com` vs `.linkedin.com`)
- Proper path settings for each cookie type
- Secure/httpOnly flags matching LinkedIn's expectations
- Session cookie expiration handling
- Cookie list format conversion for Playwright context

**Critical Cookies:**
- `li_at` - Primary authentication token (httpOnly, secure)
- `JSESSIONID` - Java session ID
- `bcookie` - Browser cookie for tracking
- `bscookie` - Secure browser cookie
- `li_rm` - Remember me token

### Anti-Detection Measures

| Detection Vector | LinkedIn Check | Our Mitigation |
|------------------|----------------|----------------|
| **navigator.webdriver** | Checks if `navigator.webdriver === true` | playwright-stealth sets to `undefined` |
| **window.chrome** | Checks if `window.chrome` exists | Inject chrome.runtime object |
| **Plugins** | Checks `navigator.plugins.length` | Simulate realistic plugin list (3+) |
| **Canvas fingerprint** | Generates canvas hash | Randomize canvas rendering |
| **WebGL fingerprint** | Generates WebGL hash | Randomize WebGL parameters |
| **Audio context** | Generates audio hash | Spoof audio context values |
| **Hardware concurrency** | Checks core count | Report realistic value (4-8 cores) |
| **Mouse movements** | Detects straight lines | Use Bezier curves via ghost cursor |
| **Typing patterns** | Detects instant fills | Character-by-character with delays |
| **Scroll behavior** | Detects instant scrolls | Use mouse-wheel events |

---

## 4. Hardened Human Behavior

### Overview

**Status**: ✅ **IMPLEMENTED** (v3.4)

Enhanced scrolling and idle patterns that mimic real user behavior for safer automation, especially with new accounts.

### Extraction Modes

Two configurable presets balance speed vs. safety:

| Setting | CAUTIOUS (New Accounts) | NORMAL (Established) |
|---------|-------------------------|----------------------|
| Scroll delay | 3.5-8.0s | 3.0-7.0s |
| Read pause | 2.0-5.0s | 1.5-4.5s |
| Warmup connections | 20 | 10 |
| Idle frequency | 1.5x | 1.0x |
| Back-scroll chance | 25% | 20% |
| Card inspection | 12% | 10% |

```python
from app.services.linkedin import ExtractionConfig, ExtractionMode

# Get config for mode
config = ExtractionConfig.from_mode(ExtractionMode.CAUTIOUS)

# Or use presets directly
config = ExtractionConfig.cautious()  # For new accounts
config = ExtractionConfig.normal()    # For established accounts
```

### Idle Pattern Generator

Real users don't maintain constant attention. The `IdlePatternGenerator` simulates:

| Pattern | Chance | Duration | Simulation |
|---------|--------|----------|------------|
| Phone check | 8% | 5-15s | Move mouse to edge, pause |
| Thinking pause | 12% | 3-8s | Just pause (considering content) |
| Distraction | 3% | 30-60s | Got distracted by something |
| Mini break | 2% | 2-5 min | Bathroom, coffee, etc. |

```python
from app.services.linkedin import IdlePatternGenerator

idle_gen = IdlePatternGenerator(frequency_multiplier=1.5)
idle_gen.start_session()

# During extraction loop:
idle_event = await idle_gen.run_idle_check(page)
if idle_event != "none":
    logger.info(f"Idle event: {idle_event}")
```

### Warmup Period

New sessions start slower and ramp up:

| Phase | Delay Multiplier | When |
|-------|------------------|------|
| Very cautious | 2.0x | First 5 min or first 25% of warmup_connections |
| Slower | 1.5x | 5-15 min or 25-50% of warmup_connections |
| Slightly slow | 1.2x | 15-30 min or 50-100% of warmup_connections |
| Normal | 1.0x | After 30 min or warmup complete |

### Momentum Scrolling

Natural scroll physics with acceleration/deceleration:

```python
async def scroll_with_momentum(self, target_distance: int):
    """
    Scroll with realistic momentum:
    1. Start slow (building up)
    2. Speed up in middle (fluid motion)
    3. Slow down at end (deceleration)

    Uses sine curve for natural acceleration.
    """
```

### Card Inspection

Simulates user considering whether to click on a profile:

```python
# 10-12% chance per scroll cycle
if random.random() < config.card_inspection_chance:
    await idle_gen.inspect_random_card(page)
    # Hovers over a visible card for 1-3 seconds without clicking
```

### CLI Usage

```bash
# Test with cautious mode (recommended for new accounts)
python test_extraction_cached.py --cautious --email user@example.com

# Or set environment variable
export LINKEDIN_CAUTIOUS_MODE=true
python test_extraction_cached.py
```

### Time Impact

| Behavior | Risk Reduction | Time Cost |
|----------|----------------|-----------|
| Longer delays | High | +50% |
| Idle patterns | Medium | +20% |
| Warmup period | Medium | First 20 connections slower |
| Card inspection | Low | Minimal |
| **Total** | | **~70% longer extraction** |

This is acceptable for safety - extraction takes ~25 min instead of ~15 min for 3,000 connections.

---

### Testing Suite

Comprehensive test coverage in `test_stealth_connections.py`:

```bash
# Test ghost cursor visual behavior
python test_stealth_connections.py --phase cursor

# Test stealth evasion (navigator.webdriver, chrome.runtime, etc.)
python test_stealth_connections.py --phase stealth

# Test navigation chain (feed → mynetwork → connections)
export LINKEDIN_SESSION_ID="<uuid>"
python test_stealth_connections.py --phase nav

# Test full extraction flow
python test_stealth_connections.py --phase extract

# Run all tests
python test_stealth_connections.py --phase all
```

### Results & Validation

**Before Stealth Implementation:**
- ❌ Session invalidated after 2-3 page loads
- ❌ Redirected to login when accessing /mynetwork
- ❌ Connections page inaccessible
- ❌ Session cookies rejected within minutes

**After Stealth Implementation:**
- ✅ Session persists across multiple page loads
- ✅ Feed, My Network, Connections all accessible
- ✅ No authentication redirects
- ✅ Connection page displays data correctly
- ✅ All anti-detection checks passing

---

## 3. Phase 1: Credential Authentication

### Overview

Users enter their LinkedIn credentials directly in Agencity. We use **Playwright + playwright-stealth** to automate login, handle 2FA, extract session cookies, and immediately discard the password. This provides a **zero-friction onboarding experience** with no browser extension required.

**Why not OAuth?** LinkedIn's OAuth API doesn't provide access to connections or messaging capabilities.

**Why not Chrome Extension?** While we maintain extension support as an option, direct credential auth is faster and works on any device/browser.

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    User enters: email + password on Agencity web app       │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. AUTOMATED LOGIN                                          │
│    Backend (Playwright + playwright-stealth):               │
│    • Launch browser with residential proxy (user location)  │
│    • Navigate to linkedin.com/login                         │
│    • Fill credentials, click submit                         │
│    • Detect if 2FA challenge appears                        │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. 2FA HANDLING (if required)                               │
│    • Create verification_request in DB (status: pending)    │
│    • Return to frontend: { status: "2fa_required" }         │
│    • Show user input field for 6-digit code                 │
│    • User enters code from SMS/email/app                    │
│    • Frontend submits code to backend                       │
│    • Backend enters code in browser, submits                │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. COOKIE EXTRACTION                                        │
│    • Wait for successful login (URL change to feed)         │
│    • Extract all cookies from browser context               │
│    • Filter critical cookies: li_at, JSESSIONID, etc.       │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. SECURE STORAGE                                           │
│    • Immediately discard password from memory               │
│    • Encrypt cookies using Fernet (AES-128)                 │
│    • Store in linkedin_sessions table                       │
│    • Close browser, release resources                       │
│    • Return to frontend: { status: "connected" }            │
└─────────────────────────────────────────────────────────────────┘
```

### Critical Cookies

| Cookie | Purpose | Lifespan |
|--------|---------|----------|
| `li_at` | Main authentication token | 1 year |
| `JSESSIONID` | Session identifier | Session |
| `bcookie` | Browser identifier | 2 years |
| `bscookie` | Secure browser cookie | 2 years |

### Implementation Code

```python
# app/services/linkedin/credential_auth.py

import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from typing import Optional, Dict, Any
from .encryption import CookieEncryption

class LinkedInCredentialAuth:
    """Authenticate LinkedIn using credentials with 2FA support."""

    async def login(
        self,
        email: str,
        password: str,
        user_location: Optional[str] = None,
        verification_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate and extract cookies.

        Returns:
            {
                'status': 'connected' | '2fa_required' | 'error',
                'cookies': {...} if success,
                'verification_id': str if 2FA required,
                'error': str if error
            }
        """
        proxy = self._get_proxy_for_location(user_location)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )

            context = await browser.new_context(
                user_agent=self._get_realistic_user_agent(),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )

            page = await context.new_page()

            # Apply stealth
            await stealth_async(page)

            try:
                # Navigate to login
                await page.goto('https://www.linkedin.com/login',
                               wait_until='networkidle')

                # Fill credentials with human-like delays
                await page.fill('input[name="session_key"]', email)
                await asyncio.sleep(random.uniform(0.3, 0.8))

                await page.fill('input[name="session_password"]', password)
                await asyncio.sleep(random.uniform(0.2, 0.5))

                # Click login
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')

                # Check for 2FA challenge
                if await self._is_2fa_required(page):
                    if not verification_code:
                        return {
                            'status': '2fa_required',
                            'message': 'Please enter verification code'
                        }
                    else:
                        await self._submit_2fa_code(page, verification_code)
                        await page.wait_for_load_state('networkidle')

                # Check if login successful
                if not await self._is_logged_in(page):
                    return {
                        'status': 'error',
                        'error': 'Invalid credentials or login failed'
                    }

                # Extract cookies
                cookies = await context.cookies()
                linkedin_cookies = self._extract_linkedin_cookies(cookies)

                # Password no longer in memory after this point
                return {
                    'status': 'connected',
                    'cookies': linkedin_cookies
                }

            finally:
                await browser.close()
```

### Security Considerations

#### 1. **Password Handling**
- **NEVER store password** in database or logs
- **Transient use only** - exists in memory only during login
- **Immediate disposal** - cleared from memory after cookie extraction
- **No logging** - password never written to logs or error messages

#### 2. **Cookie Encryption**
- **Encrypt at rest** using Fernet (AES-128-CBC)
- **Derived key** from application secret_key
- **Same security** as Chrome extension approach

#### 3. **Proxy & Location Matching**
- **Residential proxies** matching user's location
- **Reduces detection risk** - login appears from user's region
- **Provider**: Smartproxy or Bright Data

#### 4. **Bot Detection Mitigation**
- **playwright-stealth** removes automation fingerprints
- **Realistic user agent** strings
- **Human-like delays** between actions (300-800ms)
- **Proper viewport size** (1920x1080)
- **Cookie persistence** after initial login

#### 5. **Session Lifecycle**
- **Expires after 30 days** - requires re-authentication
- **User can disconnect** anytime (we delete cookies)
- **Automatic cleanup** on expiration

---

## 3. Phase 2: Connection Extraction

### Overview

Extract all LinkedIn connection URLs using user's session with **Comet-style human behavior**. This is **low risk** because we're only viewing the user's own connections list, and we mimic natural human browsing patterns.

### Browser Infrastructure

**Technology Stack:**
- **Playwright** with **playwright-stealth**
- **Persistent browser profiles** per user (stored locally)
- **Residential proxies** pinned to user's exact city/region
- **Human behavior engine** for realistic patterns
- **Warning detection** system

### Human Behavior Patterns

Based on research and Comet/Perplexity's approach, we implement:

1. **Scroll Speed**: 1-3 seconds between scrolls (varies naturally)
2. **Smooth Scrolling**: 8-15 steps per scroll (gradual, not instant jump)
3. **Back-Scroll**: 10% chance to scroll up (re-reading behavior)
4. **Session Length**: 45-90 minute sessions max, then 2-6 hour break
5. **Natural Pauses**: Random delays, not perfectly uniform
6. **Profile Dwell**: 20-60 seconds on profiles (varies by content length)

### Technical Implementation

```python
# Connection extraction with human-like behavior

async def extract_connections(session_id: str) -> List[Connection]:
    # 1. Load user's session cookies
    cookies = await get_session_cookies(session_id)

    # 2. Get residential proxy matching user's EXACT location
    proxy = get_proxy_for_user_city(session_id)  # e.g., "San Francisco, CA"

    # 3. Launch Playwright browser with stealth
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=f"./browser_profiles/{session_id}",
            headless=True,
            proxy=proxy,
            args=['--disable-blink-features=AutomationControlled']
        )

        page = await browser.new_page()
        await stealth_async(page)

        # 4. Navigate to connections page
        await page.goto('https://linkedin.com/mynetwork/invite-connect/connections/')

        # 5. Initialize human behavior engine
        behavior = HumanBehaviorEngine()
        behavior.start_session()

        # 6. Scroll to load all connections with human-like behavior
        connections = []
        no_new_count = 0

        while not behavior.should_take_break():
            # Extract visible connections
            visible = await extract_visible_connections(page)
            new_count = add_new_connections(connections, visible)

            if new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    break  # Reached end

            # Check for LinkedIn warnings
            if await detect_linkedin_warning(page):
                await handle_warning(session_id)
                break

            # Smooth gradual scroll (not instant)
            await smooth_scroll(page, distance=random.randint(800, 1200))

            # Human-like delay between scrolls
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Occasionally scroll back up (re-reading) - 10% chance
            if random.random() < 0.1:
                await smooth_scroll(page, distance=-200)
                await asyncio.sleep(random.uniform(0.5, 1.5))

        return connections
```

### Data Extracted

From the connections list page, we can extract:

| Field | Source | Example |
|-------|--------|---------|
| `full_name` | Profile card | "Sarah Chen" |
| `linkedin_url` | Profile link | "linkedin.com/in/sarahchen" |
| `current_title` | Profile card | "Senior ML Engineer" |
| `current_company` | Profile card | "Stripe" |
| `headline` | Profile card (if visible) | "Building ML systems at scale" |
| `location` | Profile card (if visible) | "San Francisco, CA" |
| `connected_at` | Connection metadata | "Connected 3 months ago" |
| `profile_image` | Profile card | URL |

### Connection Card Selectors

```python
# LinkedIn connection card selectors (updated Feb 2026)

SELECTORS = {
    'card': 'li.mn-connection-card',
    'name': '.mn-connection-card__name',
    'occupation': '.mn-connection-card__occupation',
    'profile_link': 'a[href*="/in/"]',
    'image': 'img.presence-entity__image'
}

# Fallback selectors if UI changes
FALLBACK_SELECTORS = {
    'card': '[data-view-name="connections-hub-card"]',
    'name': '.entity-result__title-text',
    'occupation': '.entity-result__primary-subtitle'
}
```

### Rate Limiting & Human Behavior

| Metric | Limit | Rationale |
|--------|-------|-----------|
| Scroll speed | 1-3 seconds between scrolls | Human-like behavior with variance |
| Smooth scrolling | 8-15 steps per scroll | Gradual movement, not instant jump |
| Back-scroll | 10% chance to scroll up | Humans re-read content |
| Session length | 45-90 minutes | Natural attention span |
| Break duration | 2-6 hours | Realistic work breaks |
| Extraction time | ~15 minutes for 3,637 | LinkedIn loads ~50 per scroll |
| Frequency | Once per user (then incremental) | Minimize account activity |

---

## 4. Phase 3: Smart Prioritization

### Overview

The key innovation: **Don't enrich everyone**. Use data from the connections list to prioritize who matters most for current roles.

### Priority Scoring Algorithm

```python
def calculate_priority_score(connection: dict, active_roles: list) -> int:
    score = 0

    # 1. TITLE MATCH (+30 points max)
    # Does their title match any role we're hiring for?
    for role in active_roles:
        if title_matches(connection['title'], role['title']):
            score += 30
            break

    # 2. COMPANY PRESTIGE (+25 points max)
    # Are they at a top company?
    if is_tier_1_company(connection['company']):  # FAANG, top startups
        score += 25
    elif is_tier_2_company(connection['company']):  # Good companies
        score += 15

    # 3. HEADLINE KEYWORDS (+20 points max)
    # Do they mention skills we need?
    for role in active_roles:
        matches = count_skill_matches(connection['headline'], role['skills'])
        score += min(matches * 7, 20)

    # 4. RECENT CONNECTION (+15 points max)
    # Did we connect recently? (warmer relationship)
    days_since_connected = get_connection_age_days(connection)
    if days_since_connected < 30:
        score += 15
    elif days_since_connected < 90:
        score += 10
    elif days_since_connected < 180:
        score += 5

    # 5. LOCATION MATCH (+10 points max)
    # Are they in a location we're hiring for?
    for role in active_roles:
        if location_matches(connection['location'], role['location']):
            score += 10
            break

    return min(score, 100)
```

### Tier Distribution

| Tier | Size | Priority Score | Enrichment Strategy |
|------|------|----------------|---------------------|
| **Tier 1** | 200 | 50+ | Immediate (2 hours) |
| **Tier 2** | 500 | 25-49 | On-demand (when role created) |
| **Tier 3** | Remaining | 0-24 | Background (30 days) |

---

## 5. Phase 4: Profile Enrichment

### Overview

Enrich profiles using a **scraper account pool** - NOT the user's account. This ensures zero risk to the user.

### Two Options

#### Option A: Unipile API (Recommended for Speed)

```python
# Using Unipile's unofficial LinkedIn API

async def enrich_via_unipile(linkedin_url: str) -> dict:
    response = await httpx.get(
        "https://api.unipile.com/api/v1/linkedin/profile",
        params={"linkedin_url": linkedin_url},
        headers={"Authorization": f"Bearer {UNIPILE_API_KEY}"}
    )

    return response.json()
```

**Unipile Limits**:
- 80-150 profiles/day per connected account
- Cost: $55/month base + $5/additional account
- Speed: 200 profiles in ~2 hours

#### Option B: Self-Managed Scraper Pool

```python
# Using our own scraper accounts

async def enrich_via_scraper_pool(linkedin_url: str) -> dict:
    # Get available scraper account
    scraper = await scraper_pool.get_available_account()

    # Use Playwright with scraper's cookies + stealth
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=f"./scraper_profiles/{scraper['id']}",
            headless=True,
            proxy=scraper['proxy']
        )

        page = await browser.new_page()
        await stealth_async(page)

        await page.goto(linkedin_url)
        await simulate_human_behavior(page)

        data = await extract_profile_data(page)
        await browser.close()

    # Record usage for rate limiting
    await scraper_pool.record_usage(scraper['id'])

    return data
```

**Self-Managed Limits**:
- 10 accounts × 100 profiles/day = 1,000/day
- Cost: ~$200/month (proxies)
- Speed: 200 profiles in ~5 hours

---

## 6. Phase 5: DM Automation

### Overview

Send personalized messages using user's session. This is **higher risk** and requires careful limits.

### Safe Limits (Based on PhantomBuster Research)

| Action | Daily Limit | Weekly Limit | Notes |
|--------|-------------|--------------|-------|
| Connection requests | 20-50 | 100-150 | With personalized note |
| Messages (1st degree) | 50-100 | 300-500 | To existing connections |
| Profile views | 80-150 | 400-700 | Before messaging |
| InMails | 20-30 | 100-150 | Sales Navigator only |

### Human Behavior Simulation

```python
class HumanBehaviorEngine:

    def get_delay_between_messages(self) -> float:
        """Random delay between 30 seconds and 5 minutes."""
        return random.triangular(30, 300, 90)  # Mode at 90 seconds

    def should_take_break(self, messages_sent: int) -> bool:
        """Take break every 15-25 messages."""
        if messages_sent > 0 and messages_sent % random.randint(15, 25) == 0:
            return True
        return False

    def get_break_duration(self) -> int:
        """Break for 30-60 minutes."""
        return random.randint(1800, 3600)

    def is_working_hours(self, user_timezone: str) -> bool:
        """Only send during 8am-8pm in user's timezone."""
        user_time = datetime.now(pytz.timezone(user_timezone))
        return 8 <= user_time.hour <= 20

    def is_weekday(self) -> bool:
        """Don't send on weekends."""
        return datetime.now().weekday() < 5
```

### Warning Detection

```python
async def detect_linkedin_warning(page) -> bool:
    """Check if LinkedIn is showing any warning."""

    warning_selectors = [
        '[data-test-id="restriction-notice"]',
        '.restriction-banner',
        'text="unusual activity"',
        'text="temporarily restricted"',
        'text="verify your identity"'
    ]

    for selector in warning_selectors:
        if await page.locator(selector).count() > 0:
            return True

    return False

async def handle_warning(session_id: str):
    """Immediately pause all activity on warning."""

    # 1. Pause session for 72 hours
    await pause_session(session_id, hours=72)

    # 2. Notify user
    await send_notification(
        session_id,
        title="LinkedIn Activity Paused",
        message="We detected a warning and paused activity for 72 hours."
    )

    # 3. Log for monitoring
    await log_warning_event(session_id)

    # 4. When resuming, use 50% of previous limits
    await reduce_limits(session_id, factor=0.5)
```

---

## 7. Risk Mitigation

### Risk Matrix

| Activity | Risk Level | Consequence | Mitigation |
|----------|------------|-------------|------------|
| Cookie capture | Very Low | None | User consents |
| View own connections | Very Low | None | Normal behavior |
| Scraper pool enrichment | None (to user) | Scraper account banned | Just create new one |
| DM automation | Medium | Temp restriction | Safe limits, pause on warning |

### Account Protection Measures

1. **Residential Proxies**
   - Match user's geographic location
   - Rotate IPs for scraper pool
   - Provider: Smartproxy ($200/month for 100GB)

2. **playwright-stealth**
   - Removes `navigator.webdriver` flag
   - Patches automation detection vectors
   - Makes browser appear like normal Chrome/Firefox

3. **Persistent Browser Profiles**
   - Each user has dedicated profile directory
   - Cookies and cache persist between sessions
   - Mimics real browser usage patterns

4. **Human Behavior**
   - Random delays (30s - 5min)
   - Smooth scrolling before actions
   - Working hours only (8am-8pm)
   - Breaks every 15-25 actions

5. **Conservative Limits**
   - Use 50% of known safe thresholds
   - Gradual ramp-up for new sessions
   - Immediate pause on any warning

6. **Session Health Monitoring**
   - Track success/failure rates
   - Detect CAPTCHA challenges
   - Monitor for restriction banners
   - Auto-pause on anomalies

---

## 11. Known Issues & Solutions

### Issue 1: First-Time CAPTCHA on New Browser Profiles

**Problem**: When a browser profile is new (or cleared), LinkedIn shows a CAPTCHA ("I'm not a robot") during login. This happens regardless of stealth measures because LinkedIn requires device trust verification.

**Why It Happens**:
- New browser profile = new device fingerprint
- LinkedIn security requires human verification for new devices
- This is standard behavior for ALL users, not just automation

**Solution - Production UX Flow**:

```
First Time Connection (per account):
┌──────────────────────────────────────────────────────────────┐
│ 1. User enters LinkedIn credentials in your app              │
│ 2. Backend opens browser with isolated profile               │
│ 3. LinkedIn may show CAPTCHA/email verification              │
│ 4. User completes verification in browser window (one time)  │
│ 5. Cookies saved to warmed profile                           │
│ 6. Profile is now trusted                                    │
└──────────────────────────────────────────────────────────────┘

All Future Sessions:
┌──────────────────────────────────────────────────────────────┐
│ 1. Load cookies from warmed profile                          │
│ 2. No CAPTCHA, no login needed                               │
│ 3. Direct access to LinkedIn                                 │
│ 4. Run extraction, DMs, etc.                                 │
└──────────────────────────────────────────────────────────────┘
```

**Key Principle**: **Never delete warmed browser profiles**. The account isolation system keeps each account's profile separate - preserve them.

**Code Handling**:
```python
# credential_auth.py now waits up to 5 minutes for checkpoint completion
elif state == LoginState.CHECKPOINT:
    # Wait for user to complete verification in browser
    # Auto-detects when logged in and continues
```

### Issue 2: Proxy Connection Failures

**Problem**: SmartProxy connection timing out.

**Potential Causes**:
1. Invalid API key format
2. Account not activated
3. Network/firewall blocking proxy ports

**Diagnosis**:
```python
from app.services.linkedin.proxy_manager import ProxyManager
import asyncio

async def test():
    pm = ProxyManager()
    if pm.is_configured:
        proxy = pm.get_proxy_for_location('us', sticky_session_id='test')
        result = await pm.check_proxy_health(proxy)
        print(result)

asyncio.run(test())
```

**Solutions**:
1. Verify SmartProxy dashboard shows active subscription
2. Check API key is correct format
3. Test from different network
4. Contact SmartProxy support if credentials are valid

### Issue 3: Session Invalidation After Page Navigation

**Problem**: LinkedIn redirects to login after accessing certain pages.

**Status**: ✅ **RESOLVED in v3.3**

**Solution**: StealthBrowser with proper cookie handling and natural navigation chain (feed → mynetwork → connections).

### Issue 4: Profile Cross-Contamination

**Problem**: Cookies from one LinkedIn account affecting another.

**Status**: ✅ **RESOLVED in v3.4**

**Solution**: AccountManager with email-hashed profile IDs ensures complete isolation.

### Issue 5: Detection of Automation Patterns

**Problem**: LinkedIn detecting bot-like behavior during extraction.

**Status**: ✅ **MITIGATED in v3.4**

**Solutions Implemented**:
- Idle patterns (phone checks, thinking pauses)
- Momentum-based scrolling
- Warmup period for new sessions
- Variable back-scrolling
- Card inspection simulation
- Ghost cursor with Bezier curves

---

## 12. Database Schema

```sql
-- LinkedIn Sessions
CREATE TABLE linkedin_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    user_id UUID REFERENCES users(id),

    -- Encrypted session data
    cookies_encrypted TEXT NOT NULL,

    -- Session metadata
    linkedin_user_id TEXT,
    linkedin_name TEXT,
    user_location TEXT,
    user_timezone TEXT,

    -- Health tracking
    status TEXT DEFAULT 'active',  -- active, paused, expired, disconnected
    health TEXT DEFAULT 'healthy',  -- healthy, warning, restricted

    -- Usage stats
    connections_extracted INTEGER DEFAULT 0,
    profiles_enriched INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,

    -- Rate limiting
    daily_message_count INTEGER DEFAULT 0,
    daily_enrichment_count INTEGER DEFAULT 0,
    last_activity_at TIMESTAMPTZ,

    -- Timestamps
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    paused_until TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted connections (before enrichment)
CREATE TABLE linkedin_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    session_id UUID REFERENCES linkedin_sessions(id),

    -- Basic data from connections list
    linkedin_url TEXT NOT NULL UNIQUE,
    full_name TEXT,
    current_title TEXT,
    current_company TEXT,
    headline TEXT,
    location TEXT,
    profile_image_url TEXT,
    connected_at_text TEXT,  -- "Connected 3 months ago"

    -- Priority scoring
    priority_score INTEGER DEFAULT 0,
    priority_tier TEXT,  -- tier_1, tier_2, tier_3

    -- Enrichment status
    enrichment_status TEXT DEFAULT 'pending',  -- pending, queued, completed, failed
    enriched_at TIMESTAMPTZ,

    -- Link to people table after enrichment
    person_id UUID REFERENCES people(id),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_linkedin_connections_company ON linkedin_connections(company_id);
CREATE INDEX idx_linkedin_connections_priority ON linkedin_connections(priority_tier, priority_score DESC);

-- Scraper account pool
CREATE TABLE scraper_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Credentials (encrypted)
    email_encrypted TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    cookies_encrypted TEXT,

    -- Proxy assignment
    proxy_location TEXT,  -- us-ca, us-ny, gb-london, etc.

    -- Status
    status TEXT DEFAULT 'aging',  -- aging, active, warned, banned

    -- Usage tracking
    profiles_scraped_today INTEGER DEFAULT 0,
    profiles_scraped_total INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Health
    consecutive_failures INTEGER DEFAULT 0,
    last_warning_at TIMESTAMPTZ,
    banned_at TIMESTAMPTZ,

    -- Lifecycle
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,  -- When it turns 30 days old

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- DM automation queue
CREATE TABLE dm_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES linkedin_sessions(id),
    connection_id UUID REFERENCES linkedin_connections(id),
    role_id UUID REFERENCES roles(id),

    -- Message
    linkedin_url TEXT NOT NULL,
    message_template TEXT,
    personalized_message TEXT NOT NULL,

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, approved, sending, sent, failed

    -- User approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,

    -- Sending
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,

    -- Response tracking
    response_received BOOLEAN DEFAULT FALSE,
    response_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_dm_queue_status ON dm_queue(status, scheduled_for);
```

---

## 9. API Reference

### Session Management

```bash
# Connect LinkedIn (direct credentials)
POST /api/v1/linkedin/connect-credentials
{
    "company_id": "uuid",
    "user_id": "uuid",
    "email": "user@email.com",
    "password": "password123",
    "user_location": "San Francisco, CA",
    "user_timezone": "America/Los_Angeles"
}

# Response
{
    "status": "connected" | "2fa_required",
    "session_id": "uuid",
    "linkedin_name": "John Smith",
    "verification_id": "uuid" (if 2FA required)
}

# Submit 2FA code
POST /api/v1/linkedin/submit-2fa
{
    "verification_id": "uuid",
    "code": "123456"
}

# Get session status
GET /api/v1/linkedin/session/{session_id}/status

# Disconnect LinkedIn
DELETE /api/v1/linkedin/session/{session_id}
```

### Connection Extraction

```bash
# Start extraction
POST /api/v1/linkedin/extract-connections
{
    "session_id": "uuid"
}

# Response
{
    "job_id": "uuid",
    "status": "started",
    "estimated_time_minutes": 15
}

# Get extraction status
GET /api/v1/linkedin/extraction/{job_id}/status
```

---

## 10. Cost Analysis

### Monthly Infrastructure Costs

| Component | Provider | Cost |
|-----------|----------|------|
| Residential Proxies (100GB) | Smartproxy | $200 |
| Playwright Workers | Railway | $50 |
| Database | Supabase Pro | $25 |
| **Total** | | **$275/month** |

### Per-User Economics

| Metric | Value |
|--------|-------|
| Infrastructure cost per user (100 users) | $2.75/month |
| Suggested price point | $29-99/month |
| Gross margin | 90-97% |
| Break-even users | ~10 |

---

## 11. Implementation & Testing Plan

### Phase 1: Core Infrastructure (Week 1)

**Tasks:**
- [x] Credential authentication with 2FA
- [x] Session management backend
- [x] Connection extraction with human behavior
- [x] Database schema setup
- [x] Unit tests

**Remaining:**
- [ ] Add playwright-stealth to existing code
- [ ] Implement persistent browser profiles
- [ ] Add warning detection system
- [ ] Set up residential proxy integration

### Phase 2: Testing (Week 2)

**Tasks:**
- [ ] Install playwright-stealth: `poetry add playwright-stealth`
- [ ] Test authentication with real LinkedIn account
- [ ] Test connection extraction (monitor for warnings)
- [ ] Validate human behavior patterns
- [ ] Monitor for 48 hours: any restrictions?

### Phase 3: Production Deploy (Week 3)

**Tasks:**
- [ ] Deploy to Railway/Render
- [ ] Configure residential proxy pool
- [ ] Set up monitoring and alerts
- [ ] Create user documentation
- [ ] Beta test with 5 users

### Testing Checklist

```bash
# 1. Install dependencies
poetry add playwright-stealth

# 2. Run unit tests
pytest agencity/tests/test_phase1_phase2.py -v

# 3. Run manual integration test
python agencity/tests/test_phase1_phase2.py
# (Enter real LinkedIn credentials when prompted)

# 4. Monitor for warnings
# Watch for:
# - Login successful?
# - Connections extracted?
# - Any restriction messages?
# - Session cookies valid after 24h?
```

---

## Summary

This architecture provides a **simple, proven approach** using:

1. ✅ **Playwright + playwright-stealth** - Battle-tested automation
2. ✅ **Multi-account isolation** - Email-hashed browser profiles via AccountManager
3. ✅ **Persistent browser profiles** - Mimics real usage patterns, preserves device trust
4. ✅ **Hardened human behavior** - Idle patterns, warmup mode, momentum scrolling
5. ✅ **Configurable extraction modes** - CAUTIOUS for new accounts, NORMAL for established
6. ✅ **Warning detection** - Immediate pause on restrictions
7. ✅ **Conservative limits** - 50% of known safe thresholds
8. ✅ **Scraper pool isolation** - Zero risk to user accounts

**Status**: 🟡 Testing Phase - Multi-account architecture implemented, residential proxy configuration in progress

**Current Blockers**:
- Residential proxy connection needs verification
- First-time CAPTCHA requires one-time manual completion per account

**Production UX Reality**:
- Users complete CAPTCHA/verification **once** on first connection
- After that, browser profile is trusted and automation runs indefinitely
- This is standard for all LinkedIn tools (Phantombuster, Dripify, etc.)

**Next Steps**:
1. ✅ Implement multi-account isolation (AccountManager)
2. ✅ Implement hardened human behavior (IdlePatternGenerator)
3. 🔄 Configure and test residential proxy
4. 🔄 Warm up test accounts (one-time CAPTCHA completion)
5. ⬜ 48-hour monitoring test
6. ⬜ Deploy to production

**Files Changed (v3.4)**:
- `app/services/linkedin/account_manager.py` - NEW: Multi-account profile management
- `app/services/linkedin/human_behavior.py` - Added IdlePatternGenerator, ExtractionConfig
- `app/services/linkedin/connection_extractor.py` - Integrated hardened behavior
- `app/services/linkedin/credential_auth.py` - Account-based profile isolation, checkpoint handling
- `app/services/linkedin/proxy_manager.py` - SmartProxy username/password support
- `scripts/save_test_auth.py` - Account-specific cache files
- `scripts/manual_login.py` - NEW: Manual checkpoint completion
- `test_extraction_cached.py` - Added --email and --clear flags

**Resources**:
- [playwright-stealth GitHub](https://github.com/AtuboDad/playwright_stealth)
- [PhantomBuster LinkedIn Limits](https://phantombuster.com/blog/guides/linkedin-automation-rate-limits-2021-edition-5pFlkXZFjtku79DltwBF0M)
- [Smartproxy Residential Proxies](https://smartproxy.com/)