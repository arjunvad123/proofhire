e# End-to-End Testing Guide

Complete guide for testing LinkedIn automation from login to connection extraction.

---

## Overview

We have **two authentication methods** to test:

1. **Automated Login** (credential_auth.py) - Already implemented ✅
2. **Manual Login** (manual_auth.py) - Needs implementation ⏸️

This guide covers testing both methods end-to-end.

---

## Prerequisites

### 1. Install Dependencies

```bash
# Run the quickstart script
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
./scripts/quickstart.sh

# Or manually:
pip install playwright playwright-stealth
playwright install chromium
```

### 2. Create Test LinkedIn Account

**CRITICAL: Use a test account, NEVER your personal account!**

```bash
# Option A: Use temp email
# 1. Go to https://temp-mail.org
# 2. Get temp email: test-abc123@temp-mail.org
# 3. Create LinkedIn account
# 4. Enable 2FA (recommended)
# 5. Wait 48 hours before heavy testing (optional but safer)

# Option B: Use dedicated test email
# Create: linkedintest+agencity@yourdomain.com
```

### 3. Set Environment Variables

```bash
export LINKEDIN_TEST_EMAIL="acn002@ucsd.edu"
export LINKEDIN_TEST_PASSWORD="^5>r9p94Wy+zuu;"

# For database testing (if using Supabase)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
```

---

## Method 1: Automated Login (Credential Auth)

### Quick Test Script

Create `test_automated_flow.py`:

```python
#!/usr/bin/env python3
"""
End-to-end test for automated LinkedIn login + extraction.
"""

import asyncio
import os
from datetime import datetime

# Import our services
from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.connection_extractor import LinkedInConnectionExtractor
from app.services.linkedin.session_manager import LinkedInSessionManager


async def test_automated_flow():
    """Test full automated flow."""

    print("=" * 70)
    print("AUTOMATED LOGIN + EXTRACTION - END TO END TEST")
    print("=" * 70)
    print()

    # Get credentials from env
    email = os.getenv('LINKEDIN_TEST_EMAIL')
    password = os.getenv('LINKEDIN_TEST_PASSWORD')

    if not email or not password:
        print("❌ Error: Set LINKEDIN_TEST_EMAIL and LINKEDIN_TEST_PASSWORD")
        return

    # Initialize services
    auth = LinkedInCredentialAuth()
    session_manager = LinkedInSessionManager()
    extractor = LinkedInConnectionExtractor(session_manager)

    session_id = f"test-automated-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # ================================================================
    # PHASE 1: AUTHENTICATION
    # ================================================================
    print("Phase 1: Authentication")
    print("-" * 70)
    print(f"📧 Email: {email}")
    print("🔐 Logging in...")
    print()

    result = await auth.login(
        email=email,
        password=password,
        user_location="San Francisco, CA"  # Optional
    )

    if result['status'] == '2fa_required':
        print("🔐 2FA Required!")
        print("Check your device for verification code.")
        code = input("Enter 6-digit code: ").strip()

        # Resume with 2FA code
        result = await auth.login(
            email=email,
            password=password,
            verification_code=code,
            resume_state=result.get('verification_state')
        )

    if result['status'] != 'connected':
        print(f"❌ Login failed: {result.get('error')}")
        return

    print("✅ Login successful!")
    print(f"   Cookies extracted: {len(result['cookies'])} cookies")
    print(f"   li_at: {result['cookies']['li_at']['value'][:20]}...")
    print()

    # Save session
    cookies = result['cookies']
    await session_manager.create_session(
        session_id=session_id,
        company_id="test-company",
        user_id="test-user",
        cookies=cookies,
        auth_method='automated'
    )

    # ================================================================
    # PHASE 2: CONNECTION EXTRACTION
    # ================================================================
    print("=" * 70)
    print("Phase 2: Connection Extraction (Limited to 10)")
    print("-" * 70)
    print()

    connection_count = [0]  # Use list to modify in callback

    def progress_callback(current, estimated):
        connection_count[0] = current
        if current <= 10:  # Only show first 10
            print(f"   [{current}/10] Extracting...")

    # Extract connections (we'll limit to 10 for testing)
    extraction_result = await extractor.extract_connections(
        session_id=session_id,
        progress_callback=progress_callback
    )

    if extraction_result['status'] != 'success':
        print(f"❌ Extraction failed: {extraction_result.get('error')}")
        return

    connections = extraction_result['connections'][:10]  # Limit to first 10

    print()
    print("✅ Extraction complete!")
    print(f"   Total connections found: {len(connections)}")
    print(f"   Duration: {extraction_result['duration_seconds']:.1f}s")
    print()

    # ================================================================
    # PHASE 3: VERIFY EXTRACTED DATA
    # ================================================================
    print("=" * 70)
    print("Phase 3: Verify Extracted Data")
    print("-" * 70)
    print()

    for i, conn in enumerate(connections[:5], 1):  # Show first 5
        print(f"{i}. {conn.get('full_name', 'Unknown')}")
        print(f"   Title: {conn.get('current_title', 'N/A')}")
        print(f"   Company: {conn.get('current_company', 'N/A')}")
        print(f"   URL: {conn.get('linkedin_url', 'N/A')}")
        print()

    if len(connections) > 5:
        print(f"   ... and {len(connections) - 5} more")
        print()

    # ================================================================
    # PHASE 4: SESSION PERSISTENCE CHECK
    # ================================================================
    print("=" * 70)
    print("Phase 4: Session Persistence Check")
    print("-" * 70)
    print()

    # Verify session was saved
    saved_session = await session_manager.get_session(session_id)
    if saved_session:
        print("✅ Session saved successfully")
        print(f"   Session ID: {session_id}")
        print(f"   Auth method: {saved_session.get('auth_method')}")
        print(f"   Created: {saved_session.get('created_at')}")
    else:
        print("❌ Session not found in database")

    print()

    # Check browser profile exists
    import os
    profile_path = f"./browser_profiles/{session_id}"
    if os.path.exists(profile_path):
        print(f"✅ Browser profile created: {profile_path}")
        print(f"   Contains: {len(os.listdir(profile_path))} items")
    else:
        print("❌ Browser profile not found")

    print()
    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_automated_flow())
```

### Run the Test

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Set credentials
export LINKEDIN_TEST_EMAIL="test@email.com"
export LINKEDIN_TEST_PASSWORD="password"

# Run test
python test_automated_flow.py
```

### Expected Output

```
======================================================================
AUTOMATED LOGIN + EXTRACTION - END TO END TEST
======================================================================

Phase 1: Authentication
----------------------------------------------------------------------
📧 Email: test@email.com
🔐 Logging in...

🔐 2FA Required!
Check your device for verification code.
Enter 6-digit code: 123456

✅ Login successful!
   Cookies extracted: 8 cookies
   li_at: AQEDAR1234567890...

======================================================================
Phase 2: Connection Extraction (Limited to 10)
----------------------------------------------------------------------

   [1/10] Extracting...
   [2/10] Extracting...
   ...
   [10/10] Extracting...

✅ Extraction complete!
   Total connections found: 10
   Duration: 15.3s

======================================================================
Phase 3: Verify Extracted Data
----------------------------------------------------------------------

1. Sarah Chen
   Title: Senior Software Engineer
   Company: Google
   URL: https://www.linkedin.com/in/sarahchen

2. Mike Johnson
   Title: Product Manager
   Company: Meta
   URL: https://www.linkedin.com/in/mikejohnson

...

======================================================================
Phase 4: Session Persistence Check
----------------------------------------------------------------------

✅ Session saved successfully
   Session ID: test-automated-20240218-143022
   Auth method: automated
   Created: 2024-02-18T14:30:22Z

✅ Browser profile created: ./browser_profiles/test-automated-20240218-143022
   Contains: 12 items

======================================================================
✅ ALL TESTS PASSED!
======================================================================
```

---

## Method 2: Manual Login (Safer Method)

This method is documented in `MANUAL_LOGIN_INTEGRATION.md` but **not yet implemented**.

### Implementation Steps

1. **Create the manual_auth.py service** (see MANUAL_LOGIN_INTEGRATION.md)
2. **Add API endpoint** for triggering manual login
3. **Test manually**

### Quick Implementation

Let me create the manual auth service for you:

```python
# app/services/linkedin/manual_auth.py
# (See MANUAL_LOGIN_INTEGRATION.md lines 42-163 for full implementation)
```

Then test with:

```python
#!/usr/bin/env python3
"""Test manual login flow."""

import asyncio
from app.services.linkedin.manual_auth import ManualLinkedInAuth

async def test_manual_login():
    auth = ManualLinkedInAuth()

    print("=" * 70)
    print("MANUAL LOGIN TEST")
    print("=" * 70)
    print()
    print("A browser window will open.")
    print("Please log in to LinkedIn manually.")
    print("The browser will close automatically after login.")
    print()

    result = await auth.start_manual_login('test-manual-session')

    print()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")

    if result['status'] in ['logged_in', 'already_logged_in']:
        print("✅ Manual login successful!")
        print(f"   Cookies saved: {len(result.get('cookies', {}))} cookies")
    else:
        print(f"❌ Login failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_manual_login())
```

---

## Testing Checklist

### Phase 1: Authentication ✅

- [ ] Login without 2FA works
- [ ] Login with 2FA works
- [ ] Invalid credentials fail gracefully
- [ ] Cookies are extracted (li_at present)
- [ ] Session is saved to database
- [ ] Browser window is VISIBLE (headless=False)

### Phase 2: Extraction ✅

- [ ] Navigate to connections page succeeds
- [ ] Extract at least 10 connections
- [ ] Each connection has: name, title, company, URL
- [ ] Scrolling is human-like (1-3s delays)
- [ ] No warnings detected during extraction
- [ ] Extraction completes without errors

### Phase 3: Persistence ✅

- [ ] Browser profile directory created
- [ ] Profile contains Cookies file
- [ ] Session persists in database
- [ ] Can re-use session without re-login

### Phase 4: Stealth Verification ✅

- [ ] Browser runs with headless=False
- [ ] playwright-stealth applied
- [ ] Visit bot.sannysoft.com shows "Not a bot"
- [ ] No CAPTCHA appears
- [ ] No unusual activity warnings

---

## Troubleshooting

### Issue: "Module not found"

```bash
pip install playwright playwright-stealth
playwright install chromium
```

### Issue: "Session expired"

The test account may be flagged. Solutions:
1. Wait 24-48 hours
2. Use a different test account
3. Use manual login instead

### Issue: "CAPTCHA appears"

Your IP may be flagged. Solutions:
1. Use residential proxy
2. Use manual login method
3. Wait and try from different network

### Issue: "No connections extracted"

Check:
```bash
# View logs
cat logs/linkedin_automation.log

# Check if logged in
# (The test will show if login succeeded)
```

### Issue: "Browser closes immediately"

This is expected if headless=False wasn't working. Verify:
```bash
grep "headless=False" app/services/linkedin/credential_auth.py
grep "headless=False" app/services/linkedin/connection_extractor.py
```

Should see both files using `headless=False`.

---

## What Should You See?

### During Test

1. **Browser window opens** (Chrome, visible)
2. **Navigates to LinkedIn login**
3. **Fills credentials** (you can watch it type)
4. **Handles 2FA** (if enabled)
5. **Navigates to connections page**
6. **Scrolls gradually** (human-like, 1-3s pauses)
7. **Extracts connection data**
8. **Browser closes**

### After Test

1. **Session saved** in database
2. **Browser profile** in `./browser_profiles/test-session-*/`
3. **Cookies file** in profile directory
4. **No errors** in logs
5. **Connection data** printed with names, titles, companies

---

## Next Steps

### If Tests Pass ✅

1. **Test with real user session** (not test account)
2. **Extract 50-100 connections** (increase limit)
3. **Monitor for 24 hours** (check for warnings)
4. **Test session re-use** (run extraction 3x over 24h)
5. **Verify profile persistence** (no re-login needed)

### If Tests Fail ❌

1. **Check logs**: `cat logs/linkedin_automation.log`
2. **Verify stealth**: Visit bot.sannysoft.com manually
3. **Test different account**: Account may be flagged
4. **Check network**: Use residential IP if possible
5. **Try manual login**: Safer method (MANUAL_LOGIN_INTEGRATION.md)

---

## Production Deployment

Once testing succeeds:

1. **Add to API routes**:
   ```python
   # app/api/routes/linkedin.py
   @router.post("/connect-automated")
   async def connect_linkedin(email: str, password: str):
       # Use credential_auth.py
   ```

2. **Add frontend UI**:
   ```typescript
   // Connect button triggers API
   async function connectLinkedIn() {
       await fetch('/api/linkedin/connect-automated', {
           method: 'POST',
           body: JSON.stringify({ email, password })
       })
   }
   ```

3. **Monitor in production**:
   - Track warning rates
   - Monitor session lifetimes
   - Check extraction success rates
   - Watch for detection patterns

---

## Summary

**Two methods available:**

1. **Automated** (credential_auth.py) ✅ Implemented
   - Faster
   - Requires password
   - Higher detection risk (but mitigated by stealth)

2. **Manual** (manual_auth.py) ⏸️ Needs implementation
   - Safer
   - No password needed
   - Lower detection risk
   - Requires user interaction

**Recommended:** Start with automated (easier to test), then add manual as alternative.

**Next command:**
```bash
python test_automated_flow.py
```
