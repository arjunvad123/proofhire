# LinkedIn Automation Testing Guide

## Overview

This guide walks through testing the LinkedIn automation system with real accounts to validate:
1. ✅ Authentication works (with 2FA)
2. ✅ playwright-stealth prevents detection
3. ✅ Persistent browser profiles work correctly
4. ✅ Connection extraction completes successfully
5. ✅ Warning detection catches restrictions
6. ✅ Human behavior patterns are realistic

## Pre-Testing Checklist

### 1. Create Test LinkedIn Account

**IMPORTANT**: Use a **dedicated test account**, NOT your personal LinkedIn.

```
1. Create new LinkedIn account
   - Use temporary email (e.g., temp-mail.org)
   - Use VPN matching your server's location
   - Complete basic profile (photo, headline, 2-3 connections)
   - Wait 48 hours before testing (new accounts are monitored closely)

2. Enable 2FA on the account
   - Go to Settings → Sign in & Security
   - Enable Two-factor authentication
   - Use authenticator app (Google Authenticator)
```

### 2. Install Dependencies

```bash
cd agencity

# Install Python dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium

# Verify playwright-stealth is installed
python -c "import playwright_stealth; print('✅ playwright-stealth installed')"
```

### 3. Prepare Test Environment

```bash
# Create directory for browser profiles
mkdir -p browser_profiles

# Create directory for test logs
mkdir -p logs

# Set environment variables
export LINKEDIN_TEST_EMAIL="your-test-account@email.com"
export LINKEDIN_TEST_PASSWORD="your-test-password"
export TESTING_MODE=true
```

## Testing Phases

### Phase 1: Authentication Test (5 minutes)

Test credential authentication with 2FA handling.

```bash
# Run authentication test
python tests/test_credential_auth.py
```

**Expected Output:**
```
🚀 Testing LinkedIn Authentication
   Email: test@email.com

   🔐 2FA Required
   Enter 6-digit code: 123456

   ✅ Login successful!
   Cookies extracted: 8 cookies
   li_at: AQEDAR...

   Session valid: True
   Can access feed: True
```

**What to Monitor:**
- [ ] Login completes without CAPTCHA
- [ ] 2FA code accepted
- [ ] li_at cookie extracted
- [ ] Session persists for 24+ hours

**If CAPTCHA appears:** This means stealth is not working. Check:
- playwright-stealth is installed correctly
- Using latest Chromium version
- Not running in obvious cloud IP ranges

### Phase 2: Connection Extraction Test (15 minutes)

Test connection extraction with human behavior.

```bash
# Run extraction test (limit to 50 connections)
python tests/test_phase1_phase2.py

# Or run full extraction
python -c "
from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
import asyncio

async def test():
    # Login
    auth = LinkedInCredentialAuth()
    result = await auth.login(
        email='$LINKEDIN_TEST_EMAIL',
        password='$LINKEDIN_TEST_PASSWORD'
    )

    # Extract (full)
    session_id = 'test-session'
    extractor = LinkedInConnectionExtractor(session_manager)
    result = await extractor.extract_connections(session_id)

    print(f'✅ Extracted {result[\"total\"]} connections')
    print(f'   Duration: {result[\"duration_seconds\"]}s')

asyncio.run(test())
"
```

**Expected Output:**
```
📊 Extracting connections...

   [1/73] Scroll 1... (delay: 1.8s)
   [2/73] Scroll 2... (delay: 2.3s)
   [3/73] Scroll 3... (delay: 1.2s)
   [10/73] 📖 Back-scroll (re-reading)

   Progress: 150/500 connections

✅ Extraction complete!
   Total: 487 connections
   Duration: 14.2 minutes
   No warnings detected
```

**What to Monitor:**
- [ ] Scroll delays are 1-3 seconds (varies)
- [ ] Occasional back-scroll (10% of time)
- [ ] No "unusual activity" warnings
- [ ] Session completes without interruption
- [ ] All connection data extracted correctly

**If warnings appear:**
```
❌ LinkedIn warning detected: "unusual activity"
   Type: unusual_activity
   Session paused for 48 hours
```

This means:
- Behavior patterns need adjustment (too fast, too uniform)
- Account is flagged (use different test account)
- IP address is suspicious (use residential proxy)

### Phase 3: Warning Detection Test (5 minutes)

Test that warning detection catches restrictions.

```bash
python tests/test_warning_detection.py
```

**Expected Output:**
```
🔍 Testing Warning Detection

1. Testing restriction banner detection...
   ✅ Detected: restriction

2. Testing CAPTCHA detection...
   ✅ Detected: captcha

3. Testing unusual activity detection...
   ✅ Detected: unusual_activity

4. Testing clean page (no warnings)...
   ✅ No warnings detected

All warning detection tests passed!
```

### Phase 4: 24-Hour Monitoring Test

Run extraction 3 times over 24 hours to test session persistence.

```bash
# Run 1 (immediate)
python scripts/test_extraction.py

# Wait 8 hours

# Run 2 (8 hours later)
python scripts/test_extraction.py

# Wait 16 hours

# Run 3 (24 hours after initial)
python scripts/test_extraction.py
```

**What to Monitor:**
- [ ] Cookies still valid after 8 hours
- [ ] Cookies still valid after 24 hours
- [ ] No re-authentication needed
- [ ] No warnings across all 3 runs

### Phase 5: Persistent Profile Test

Verify browser profile persists correctly.

```bash
# Run extraction
python scripts/test_extraction.py

# Check profile directory
ls -la browser_profiles/test-session/

# Should see:
# - Default/Cookies (SQLite database)
# - Default/Preferences (JSON)
# - Default/Cache/
```

**Expected Profile Structure:**
```
browser_profiles/
└── test-session/
    ├── Default/
    │   ├── Cookies          # SQLite DB with li_at
    │   ├── Preferences      # Browser preferences
    │   ├── Cache/           # Cached resources
    │   └── Local Storage/   # LinkedIn data
    └── SingletonLock
```

**What to Monitor:**
- [ ] Profile directory created
- [ ] Cookies file exists and contains li_at
- [ ] Profile size grows over time (cache building)
- [ ] Same profile used across runs

## Docker Testing

### Build and Run Tests in Docker

```bash
# Build Docker image
docker build -t agencity-linkedin-test -f Dockerfile.test .

# Run tests
docker run --rm \
  -e LINKEDIN_TEST_EMAIL="test@email.com" \
  -e LINKEDIN_TEST_PASSWORD="password" \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/browser_profiles:/app/browser_profiles \
  agencity-linkedin-test

# Or run interactively
docker run --rm -it \
  -e LINKEDIN_TEST_EMAIL="test@email.com" \
  -e LINKEDIN_TEST_PASSWORD="password" \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/browser_profiles:/app/browser_profiles \
  agencity-linkedin-test bash
```

### Docker-Specific Testing

```bash
# Inside Docker container

# 1. Test Playwright installation
playwright install --with-deps chromium

# 2. Test stealth
python -c "
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    Stealth().apply_stealth_sync(page)
    page.goto('https://bot.sannysoft.com')
    page.screenshot(path='bot-test.png')
    print('✅ Stealth test complete - check bot-test.png')
"

# 3. Run full test suite
pytest tests/ -v --tb=short
```

## Monitoring & Metrics

### Key Metrics to Track

```python
# Add to your test script
import time
import json

metrics = {
    'test_date': datetime.now().isoformat(),
    'auth_time_seconds': 0,
    'extraction_time_seconds': 0,
    'connections_extracted': 0,
    'warnings_detected': 0,
    'captcha_encountered': False,
    'session_valid_24h': False,
}

# Save metrics
with open(f'logs/test_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```

### Success Criteria

**Phase 1 - Authentication:**
- ✅ Login success rate: 100%
- ✅ 2FA handling: Works
- ✅ CAPTCHA rate: 0%
- ✅ Session persistence: 24+ hours

**Phase 2 - Extraction:**
- ✅ Extraction success rate: 100%
- ✅ Average scroll delay: 1-3 seconds
- ✅ Back-scroll frequency: ~10%
- ✅ Warning rate: 0%
- ✅ Data completeness: >95%

**Phase 3 - Warning Detection:**
- ✅ Detection accuracy: 100%
- ✅ False positive rate: 0%
- ✅ Auto-pause working: Yes
- ✅ User notification: Sent

**Phase 4 - 24h Monitoring:**
- ✅ Runs completed: 3/3
- ✅ Warnings: 0
- ✅ Session stability: Stable
- ✅ Cookie validity: Valid

## Troubleshooting

### Issue: CAPTCHA appears during login

**Cause:** Stealth not working or IP flagged

**Solution:**
```bash
# 1. Verify stealth is applied
python -c "
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    Stealth().apply_stealth_sync(page)
    page.goto('https://bot.sannysoft.com')
    # Check screenshot - should show 'Not a bot'
"

# 2. Use residential proxy
# Add to credential_auth.py:
proxy = {
    'server': 'http://proxy.smartproxy.com:7000',
    'username': 'your-username',
    'password': 'your-password'
}

# 3. Use different IP/VPN
```

### Issue: "Unusual activity" warning

**Cause:** Behavior too mechanical or account flagged

**Solution:**
```python
# Adjust behavior parameters
# In human_behavior.py:

MIN_SCROLL_DELAY = 2.0  # Increase from 1.0
MAX_SCROLL_DELAY = 5.0  # Increase from 3.0

# Add more variance
def get_delay_between_messages(self) -> float:
    # Add occasional very long pause
    if random.random() < 0.1:  # 10% chance
        return random.uniform(300, 600)  # 5-10 minutes
    return random.triangular(30, 300, 90)
```

### Issue: Session expires quickly

**Cause:** Cookies not persisting or profile not saving

**Solution:**
```bash
# Check profile directory
ls -la browser_profiles/test-session/Default/Cookies

# Verify cookies are being saved
python -c "
import sqlite3
conn = sqlite3.connect('browser_profiles/test-session/Default/Cookies')
cursor = conn.cursor()
cursor.execute('SELECT name FROM cookies WHERE host_key LIKE \"%linkedin%\"')
print(cursor.fetchall())
"

# Should see: [('li_at',), ('JSESSIONID',), ...]
```

### Issue: Docker tests fail but local works

**Cause:** Docker environment differences

**Solution:**
```dockerfile
# In Dockerfile.test, ensure:

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgbm1 \
    libasound2

# Install Playwright with deps
RUN playwright install --with-deps chromium

# Use headless mode with proper args
args=[
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox'
]
```

## Production Deployment Checklist

Before deploying to production:

- [ ] All test phases pass with 0 warnings
- [ ] 24-hour monitoring test successful
- [ ] Docker tests pass
- [ ] Residential proxy integrated
- [ ] User notification system working
- [ ] Rate limits configured conservatively
- [ ] Monitoring/alerting set up
- [ ] Backup test accounts created (in case primary flagged)
- [ ] Legal disclaimer in user onboarding
- [ ] User can disconnect anytime

## Next Steps

Once all tests pass:

1. **Set up residential proxies**: Smartproxy or Bright Data
2. **Configure monitoring**: Track warning rates, session health
3. **Beta test with 5 users**: Real users, real profiles
4. **Monitor for 7 days**: Watch for any delayed restrictions
5. **Iterate on behavior patterns**: Adjust based on real data
6. **Launch to production**: With conservative limits

## Support

If you encounter issues during testing:

1. Check logs: `cat logs/linkedin_automation.log`
2. Review metrics: `cat logs/test_metrics_*.json`
3. Take screenshots during failures
4. Document exact steps to reproduce
5. Test with fresh account if current one flagged

---

**Remember:** Always use test accounts, never production. LinkedIn's detection systems improve constantly - what works today may be flagged tomorrow. Conservative limits and monitoring are essential.
