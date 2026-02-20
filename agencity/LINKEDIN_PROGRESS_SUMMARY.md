# LinkedIn Automation - Progress Summary

## ✅ Completed

### 1. Authentication System
- **Status**: Fully working
- **File**: `app/services/linkedin/credential_auth.py`
- **Features**:
  - Email/password login
  - 2FA support
  - Cookie extraction
  - Playwright-stealth integration
  - Fixed timeout issues (changed networkidle → load)
  - **Adaptive state-machine login flow** (handles all LinkedIn login variations)
  - **Persistent browser profiles** (eliminates repeated sign-in emails)

**Login States Handled**:
- Welcome Back (remembered account selector)
- Password-only form (email pre-filled)
- Standard email/password form
- 2FA challenges and security checkpoints

**Test**: `python test_auth_only.py`

### 2. Session Storage
- **Status**: Fully working
- **Files**:
  - `app/services/linkedin/session_manager.py`
  - `supabase/migrations/006_linkedin_automation.sql`
- **Features**:
  - Encrypted cookie storage (Fernet)
  - Database persistence in Supabase
  - 30-day session expiry
  - Health tracking (active/paused/expired)
  - No re-login needed (cookies reused)

**Database Tables Created**:
- `linkedin_sessions` - Stores encrypted session cookies
- `connection_extraction_jobs` - Tracks extraction progress
- `linkedin_connections` - Stores extracted connection data

**Test**: Session persists across runs, no sign-in emails after first login

### 3. Connection Extraction (DOM Selectors)
- **Status**: ✅ Fully working
- **Files**: `app/services/linkedin/connection_extractor.py`
- **Selectors** (stable attributes, not obfuscated classes):
  - `data-view-name="connections-list"` - Main container
  - `data-view-name="connections-profile"` - Profile links
  - `componentkey="auto-component-*"` - Card containers

**Extraction Logic**:
- Name: Nested `<p><a>` links or `aria-label` on figures
- Headline: `<p>` elements (filtering UI text)
- Connected date: "Connected on..." text parsing
- Profile URL: `href` attributes

**Testing**:
- `test_extraction_offline.py` - Offline extraction against saved HTML
- `test_extraction_new.py` - Live extraction test
- `quick_dom_inspect.py` - DOM inspection utility

### 4. Browser Profiles
- **Status**: Working
- **Location**: `./browser_profiles/{session_id}/`
- **Features**:
  - Persistent browser profiles per session
  - Cookies, cache, and state preserved
  - Mimics real browser usage
  - Reduces detection risk

### 5. Cookie Caching System
- **Status**: ✅ Working
- **Files**:
  - `scripts/save_test_auth.py` - One-time auth + cookie save
  - `conftest.py` - Pytest fixtures for cached cookies
  - `.linkedin_test_cache.json` - Cached cookies (gitignored)
- **Features**:
  - Session-scoped pytest fixtures (`linkedin_cookies`, `linkedin_cookie_list`)
  - Tests load from cache, skip login entirely
  - Cache persists across test runs

### 6. Adaptive Re-Authentication
- **Status**: ✅ Working
- **File**: `test_extraction_cached.py`
- **Features**:
  - Detects stale cookies during extraction
  - Automatically handles re-authentication using state machine
  - Updates cookie cache with fresh cookies
  - Continues extraction without restart

### 7. Testing Scripts
Created comprehensive test suite:
- `test_auth_only.py` - Test authentication + session storage (loads cache when present)
- `test_cookie_reuse.py` - Verify cookies work without re-login
- `test_extraction_cached.py` - Extraction with cached cookies + adaptive re-auth
- `test_extraction_offline.py` - Offline extraction against saved HTML
- `test_extraction_new.py` - Live extraction test
- `quick_dom_inspect.py` - DOM inspection utility
- `debug_connections_page.py` - Debug page navigation
- `screenshot_connections.py` - Capture page state
- `find_connection_selectors.py` - Discover selectors
- `scripts/save_test_auth.py` - Save cookies for testing

---

## ✅ RESOLVED: Session Invalidation

### Solution: Stealth Browser + Ghost Cursor
Implemented comprehensive anti-detection system that **successfully resolves session invalidation**:

1. ✅ Login succeeds with human-like behavior
2. ✅ Cookies extracted and properly formatted
3. ✅ Feed page loads without issues
4. ✅ My Network page loads successfully
5. ✅ **Connections page loads without redirect!**

### What Was Implemented

#### 1. StealthBrowser Module (`stealth_browser.py`)
- **playwright-stealth** integration at context level
- **Persistent browser profiles** (maintains session state across runs)
- **Extra evasion scripts**:
  - WebGL fingerprint randomization
  - Canvas fingerprint spoofing
  - Audio context masking
  - chrome.runtime injection
  - Navigator plugins simulation
  - Permissions API mocking
- **Residential proxy support** with location-based routing
- **Dual launch modes**: Standard (ephemeral) and persistent (session-based)

#### 2. GhostCursor Module (`human_behavior.py`)
- **pyppeteer-ghost-cursor** integration
- **Bezier curve mouse movements** (no straight lines between elements)
- **Natural typing rhythm**:
  - Variable speed (50-80 WPM)
  - Character-by-character with random delays
  - Occasional typos and corrections
  - Pauses between words
- **Mouse-wheel scrolling** (discrete notches, not instant jumps)
- **Random delays** between all actions
- **Realistic click patterns** (slight overshoot, small adjustments)

#### 3. Enhanced Cookie Handling
- Proper domain/path configuration (`.www.linkedin.com` vs `.linkedin.com`)
- Correct secure/httpOnly flags
- Session cookie expiration handling
- Cookie list format conversion for Playwright context

### Test Results (All Passing ✅)

**Phase 0: Ghost Cursor Visual Test**
- ✅ Natural mouse movement with visible Bezier trails
- ✅ Human-like typing with variable speed
- ✅ Mouse-wheel scrolling (not programmatic scroll)
- ✅ Natural clicks with overshoot
- Screenshot: `ghost_cursor_test_20260219_004341.png`

**Phase 1: Stealth Evasion Test**
- ✅ `navigator.webdriver` = False
- ✅ `window.chrome` exists
- ✅ `navigator.plugins.length` = 3
- ✅ `hardwareConcurrency` = 8
- Screenshot: `stealth_test_20260219_010402.png`

**Phase 2: Navigation Chain Test**
- ✅ Feed page loads (`https://www.linkedin.com/feed/`)
- ✅ My Network page loads (`https://www.linkedin.com/mynetwork/`)
- ✅ **Connections page loads successfully!** (No login redirect)
- URL: `https://www.linkedin.com/mynetwork/invite-connect/connections/`

**Phase 3: Connection Page Access**
- ✅ Page displays "1 connection"
- ✅ Connection card visible with name, headline, profile image
- ✅ No authentication challenges or redirects
- Screenshot: `extraction_test.png`

---

## 🔍 What We Learned

### LinkedIn's New HTML Structure
- **Dynamic class names**: Changes between deploys
- **Component-based**: React with obfuscated classes
- **Lazy loading**: Content loads on scroll
- **Multiple authentication checks**: Each page validates differently

### Screenshot Analysis
From `linkedin_connections_20260218_234031.png`:
- Page loads correctly when logged in
- Shows "1 connection"
- Card displays: name, headline, profile picture, "Message" button
- Layout is clean and modern

### Chrome Extension Approach (From Your Example)
The Chrome extension approach you shared works better because:
- **Runs in-page**: No external automation detection
- **Shadow DOM**: Isolates extension UI from LinkedIn
- **No CDP**: Doesn't use Chrome DevTools Protocol
- **User-driven**: Actual user clicks trigger actions

---

## ✅ RESOLVED: DOM Selectors

### Solution
Updated `connection_extractor.py` to use stable DOM attributes instead of obfuscated CSS classes:

**Working Selectors:**
- `data-view-name="connections-list"` - Main container
- `data-view-name="connections-profile"` - Profile links
- `componentkey="auto-component-*"` - Card containers

**Extraction Successfully Parses:**
- Name from nested `<p><a>` links or `aria-label` on figures
- Headline from `<p>` elements (filtering UI text)
- Connected date from "Connected on..." text
- Profile URL from `href` attributes

**Verified Working:**
- Offline extraction against saved HTML: ✅
- Live extraction test: ✅

---

## ✅ COMPLETED: Pagination & Production Integration

### 1. Pagination/Infinite Scroll (✅ Done)
- **File**: `app/services/linkedin/connection_extractor.py`
- **Features**:
  - Detects total connection count from page header
  - Waits for new content after each scroll
  - Handles LinkedIn's lazy loading (~50 per scroll)
  - Natural scrolling with ghost cursor
  - Progress callback with accurate totals
  - End-of-list detection (3 scrolls with no new content)

### 2. Production Integration (✅ Done)
- **Files**:
  - `app/services/linkedin/extraction_task.py` - Background task runner
  - `app/api/routes/linkedin.py` - API endpoints wired up
- **Features**:
  - Background task runs extraction async via FastAPI BackgroundTasks
  - Stores connections in `linkedin_connections` table (upsert on company_id + linkedin_url)
  - Updates job status in `connection_extraction_jobs` table
  - Progress tracking via `connections_found` column
  - New endpoint: `GET /connections/{company_id}` to list extracted connections

### API Endpoints
- `POST /api/v1/linkedin/extract-connections` - Start extraction job
- `GET /api/v1/linkedin/extraction/{job_id}/status` - Check job progress
- `GET /api/v1/linkedin/connections/{company_id}` - List connections (paginated)

---

## 🎯 Next Steps

1. **Error Handling**
   - Handle network failures gracefully
   - Retry logic for transient errors
   - Alert system for persistent failures

2. **Rate Limiting**
   - Enforce max connections per hour/day
   - Respect LinkedIn's implicit limits
   - Auto-pause on warning detection

### Option 2: Chrome Extension Approach
Build a Chrome extension instead of Playwright automation:

**Pros**:
- Lower detection risk
- User's own session (no login needed)
- No cookie management
- Faster and more reliable

**Cons**:
- Requires user to install extension
- Limited to Chrome browser
- User must be logged in
- Can't run server-side

**Implementation**:
- Content script injected into LinkedIn
- Shadow DOM for UI isolation
- PostMessage for background communication
- IndexedDB for local storage

### Option 3: Hybrid Approach
Combine both methods:

1. **Chrome Extension** for data extraction (low-risk)
2. **Backend API** for data processing and storage
3. **Playwright** for enrichment (only when needed)

User installs extension → Extension extracts connections → Sends to backend → Backend enriches profiles

---

## 📊 Current Test Results

### Authentication: ✅ Working
```
✅ Login successful!
   Cookies extracted: 8 cookies
   li_at: AQEDAVa1WOgAMxNJAAA...
```

### Session Storage: ✅ Working
```
✅ Session saved!
   Session ID: c4c7ebca-a493-42be-a3c0-d2213073627a
   Expires: 2026-03-21T06:28:28Z

✅ Session retrieved!
   Status: active
   Health: healthy

✅ Cookies retrieved and decrypted!
```

### Cookie Reuse: ✅ Working
```
✅ Cookies injected into browser context
✅ Feed page loads successfully
✅ My Network page loads successfully
✅ Connections page loads successfully
   No login redirects detected!
```

### Connection Extraction: ✅ Working
```
Status: success
✅ Page loads: https://www.linkedin.com/mynetwork/invite-connect/connections/
✅ Shows "1 connection"
✅ Connection card visible
✅ DOM selectors updated for new structure
✅ Offline extraction verified
✅ Live extraction working
```

### Adaptive Re-Auth: ✅ Working
```
✅ Detects stale cookies automatically
✅ Handles Welcome Back, password-only, email/password forms
✅ Updates cookie cache with fresh cookies
✅ Continues extraction without restart
```

---

## 🛠️ Technical Details

### Cookies Structure
```python
{
    'li_at': {
        'value': 'AQEDA...',
        'domain': '.linkedin.com',
        'secure': True,
        'httpOnly': True
    },
    'JSESSIONID': {...},
    'bcookie': {...},
    # ... 5 more cookies
}
```

### Connection Data Structure
```python
{
    'full_name': 'Aidan Nguyen-Tran',
    'linkedin_url': 'https://www.linkedin.com/in/aidan-nguyen-tran-277a3a258/',
    'current_title': 'Building',
    'current_company': 'Agencity',
    'headline': 'Building @ Agencity | Prev. Cluely | Data Science @ UCSD',
    'profile_image_url': 'https://media.licdn.com/...',
    'extracted_at': '2026-02-19T06:28:00Z'
}
```

### Database Schema
```sql
CREATE TABLE linkedin_sessions (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    cookies_encrypted TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    health TEXT DEFAULT 'healthy',
    connections_extracted INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 📝 Recommendations

### For Production Use

1. **Use Real Accounts**
   - Not test accounts
   - With existing connections
   - Established activity history
   - Good standing with LinkedIn

2. **Rate Limiting**
   - Max 50 connections/hour
   - Max 200 connections/day
   - Random delays between actions
   - Pause during off-hours

3. **Monitoring**
   - Track warning rates
   - Log all redirects
   - Monitor session health
   - Alert on detection

4. **Fallback Strategy**
   - Manual intervention option
   - Email user if session fails
   - Grace period before retry
   - Alternative extraction methods

### Security Best Practices

1. **Cookie Encryption**: ✅ Implemented (Fernet)
2. **Secure Storage**: ✅ Using Supabase
3. **Session Expiry**: ✅ 30 days
4. **RLS Policies**: ✅ Enabled
5. **Proxy Usage**: ✅ Implemented (SmartProxy + BrightData, sticky sessions, geo-targeting)

---

## 💰 Unit Economics — Cost Per Operation

### Proxy Provider Pricing

| Provider | Pay-as-you-go | Starter | Growth | Enterprise |
|---|---|---|---|---|
| **SmartProxy** | ~$12/GB | $30/mo (2 GB = $15/GB) | $80/mo (8 GB = $10/GB) | ~$5–7/GB |
| **BrightData** | ~$15/GB | $500/mo (~$10.50/GB) | Custom (~$8/GB) | ~$5/GB |

> **Recommendation**: SmartProxy Growth plan ($10/GB) for early stage. Switch to enterprise at 50+ active users.

---

### Operation 1: Authentication (One-Time Per User)

| Step | Pages Loaded | Est. Bandwidth |
|---|---|---|
| LinkedIn login page | 1 | ~1.5 MB |
| Feed redirect + verification | 1–2 | ~2 MB |
| Cookie extraction | 0 | 0 |
| **Total** | **2–3 pages** | **~3.5 MB** |

**Frequency**: Once per user (persistent profile), or once per 30 days (session expiry).

| Metric | Value |
|---|---|
| Bandwidth per auth | ~0.0035 GB |
| **Proxy cost @ $10/GB** | **$0.035** |
| **Proxy cost @ $7/GB** | **$0.025** |

---

### Operation 2: Connection Extraction (Per User Onboarding)

LinkedIn loads ~50 connections per scroll. The extraction follows a natural navigation chain (feed → mynetwork → connections) then scrolls to load all.

| Connection Count | Pages | Scrolls | Nav Bandwidth | Scroll Bandwidth | **Total** |
|---|---|---|---|---|---|
| 100 | 3 | ~2 | ~6 MB | ~0.7 MB | **~7 MB** |
| 500 | 3 | ~10 | ~6 MB | ~3.5 MB | **~10 MB** |
| 1,000 | 3 | ~20 | ~6 MB | ~7 MB | **~13 MB** |
| 3,000 | 3 | ~60 | ~6 MB | ~21 MB | **~27 MB** |
| 5,000 | 3 | ~100 | ~6 MB | ~35 MB | **~41 MB** |

| Avg User (500 conn.) | @ $10/GB | @ $7/GB |
|---|---|---|
| Bandwidth: ~0.01 GB | **$0.10** | **$0.07** |

| Power User (3,000 conn.) | @ $10/GB | @ $7/GB |
|---|---|---|
| Bandwidth: ~0.027 GB | **$0.27** | **$0.19** |

| Max User (5,000 conn.) | @ $10/GB | @ $7/GB |
|---|---|---|
| Bandwidth: ~0.041 GB | **$0.41** | **$0.29** |

---

### Operation 3: PDL Enrichment (Per Candidate)

No proxy needed — pure API call.

| Metric | Value |
|---|---|
| Cost per enrichment | **$0.10** |
| Enrichments per role | Top 5 candidates |
| Cache duration | 30 days |
| **Cost per role (cold)** | **$0.50** |
| **Cost per role (cached)** | **$0.00** |

---

### Operation 4: AI / LLM Costs (Per Role Curation)

| Service | Per-Role Cost | Notes |
|---|---|---|
| Claude (reasoning) | ~$0.006 | Top 5 candidates |
| GPT-4o (scoring) | ~$0.01 | Fit scoring |
| Perplexity (research) | ~$0.025 | Disabled in cache gen |
| **Total per role** | **~$0.04** | |

---

### 🧮 Full Cost Per User (Onboarding)

**Scenario: Average user, 500 connections, 1 role**

| Cost Item | Amount |
|---|---|
| Authentication (proxy) | $0.035 |
| Connection extraction (proxy) | $0.10 |
| PDL enrichment (top 5) | $0.50 |
| AI/LLM curation | $0.04 |
| **Total onboarding cost** | **$0.68** |

**Scenario: Power user, 3,000 connections, 3 roles**

| Cost Item | Amount |
|---|---|
| Authentication (proxy) | $0.035 |
| Connection extraction (proxy) | $0.27 |
| PDL enrichment (15 unique, ~10 cached) | $0.50 |
| AI/LLM curation (×3) | $0.12 |
| **Total onboarding cost** | **$0.93** |

---

### 📊 Monthly Recurring Costs (Per Active User)

After onboarding, recurring costs are minimal:

| Item | Monthly Cost | Trigger |
|---|---|---|
| Session refresh (re-auth) | $0.035 | Every 30 days |
| Incremental extraction | ~$0.02 | New connections since last run |
| New role curation | ~$0.54 | Per new role |
| **Idle user (no new roles)** | **~$0.06/mo** | |
| **Active user (2 roles/mo)** | **~$1.14/mo** | |

---

### 📈 Scaling Projections (Monthly)

| Active Users | Proxy GB/mo | Proxy Cost | PDL Cost | AI Cost | **Total/mo** |
|---|---|---|---|---|---|
| 10 | ~0.15 GB | $1.50 | $5.00 | $0.40 | **$6.90** |
| 50 | ~0.75 GB | $7.50 | $25.00 | $2.00 | **$34.50** |
| 100 | ~1.5 GB | $15.00 | $50.00 | $4.00 | **$69.00** |
| 500 | ~7.5 GB | $52.50* | $250.00 | $20.00 | **$322.50** |
| 1,000 | ~15 GB | $90.00* | $500.00 | $40.00 | **$630.00** |

*Enterprise pricing at $7/GB kicks in above ~25 GB/mo.

---

### 🎯 Key Takeaways

1. **Proxy cost is negligible** — < $0.30/user for onboarding. The PDL enrichment ($0.10/call) is the dominant variable cost.
2. **Sticky sessions save money** — Same IP reuse means no wasted auth retries. One auth = one login email = one proxy session.
3. **30-day PDL cache is critical** — Without it, enrichment costs would be 3–5× higher for multi-role companies.
4. **Break-even**: At $50/mo SaaS pricing, break-even is ~1 user per month. At scale (100 users), COGS is ~$0.69/user/mo = **98.6% gross margin**.

---

## 🎬 Quick Start

### Run Authentication Test
```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

export LINKEDIN_TEST_EMAIL="your@email.com"
export LINKEDIN_TEST_PASSWORD="your-password"

python test_auth_only.py
```

### Check Saved Sessions
```sql
SELECT id, status, health, connections_extracted, created_at
FROM linkedin_sessions
ORDER BY created_at DESC
LIMIT 5;
```

### Test Cookie Reuse
```bash
# Get session ID from previous test
python test_cookie_reuse.py <session-id>
```

---

## 📚 Documentation Files

- `END_TO_END_TESTING.md` - Complete testing guide
- `IMPLEMENTATION_COMPLETE.md` - Implementation summary
- `TESTING_GUIDE.md` - Testing procedures
- `GHOST_CURSOR_INTEGRATION.md` - Mouse movement simulation
- `MANUAL_LOGIN_INTEGRATION.md` - Manual auth option
- `docs/architecture/LINKEDIN_AUTOMATION.md` - Architecture details

---

## 🔗 Related Commits

1. `0ee93af` - fix: LinkedIn authentication and session storage
2. `b233643` - feat: update LinkedIn connection extraction with new selectors
3. `ef9aa58` - feat: implement stealth browser with ghost cursor for LinkedIn automation
4. `348c311` - feat: integrate ghost cursor + stealth browser for LinkedIn automation
5. `fc22f8a` - docs: update LinkedIn automation docs with stealth implementation
6. `b0f28d5` - fix: update LinkedIn connection extraction for new DOM structure
7. `52e55ee` - feat: persistent browser profiles + cookie cache to eliminate LinkedIn login emails
8. `268d4a4` - feat: adaptive state-machine login flow for LinkedIn
9. `2701863` - feat: add adaptive re-auth to extraction test

---

**Last Updated**: February 19, 2026

**Status**: ✅ Authentication working | ✅ Session persistence working | ✅ Navigation working | ✅ DOM selectors working | ✅ Adaptive re-auth working | ✅ Proxy support working

**Latest Commit**: `400c0a4` - feat: implement residential proxy support with sticky sessions + geo-targeting
