# Manual Login Integration (Inspired by personal-linkedin-agent)

## Overview

After reviewing [personal-linkedin-agent](https://github.com/pamelafox/personal-linkedin-agent), we identified a **safer login approach**: have users login manually in a visible browser, then save the session.

**Benefits:**
- ✅ LinkedIn sees real user behavior (mouse, keyboard, timing)
- ✅ User handles 2FA naturally (no backend code needed)
- ✅ No password stored or transmitted
- ✅ Lower detection risk
- ✅ Works with any 2FA method (SMS, app, email, security key)

**Tradeoffs:**
- ❌ Requires user interaction (not fully automated)
- ❌ Requires visible browser (can't run on headless server during setup)
- ✅ After initial login, fully automated

## Architecture

### Option A: Automated Login (Current)
```
User → Frontend → Backend → Playwright → LinkedIn
                   ↓
              Credentials
              2FA Code
```

### Option B: Manual Login (New)
```
User → Frontend → Backend launches visible browser
                   ↓
              User logs in manually in browser
                   ↓
              Backend saves session → Fully automated after
```

## Implementation

### 1. Add Manual Login Service

```python
# app/services/linkedin/manual_auth.py

import asyncio
from pathlib import Path
from typing import Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async


class ManualLinkedInAuth:
    """Manual LinkedIn login with visible browser."""

    async def start_manual_login(self, session_id: str) -> Dict[str, Any]:
        """
        Launch browser for user to login manually.

        Args:
            session_id: User session ID

        Returns:
            {
                'status': 'logged_in' | 'already_logged_in' | 'timeout' | 'error',
                'message': str
            }
        """
        profiles_dir = Path('./browser_profiles')
        profiles_dir.mkdir(exist_ok=True)

        user_profile_dir = profiles_dir / session_id
        storage_path = user_profile_dir / 'storage_state.json'

        async with async_playwright() as p:
            # Launch persistent context (visible browser)
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(user_profile_dir),
                headless=False,  # MUST be visible for manual login
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--start-maximized'
                ]
            )

            page = await context.new_page()
            await stealth_async(page)

            try:
                # Check if already logged in
                await page.goto("https://www.linkedin.com/feed", wait_until='networkidle')

                if page.url.startswith("https://www.linkedin.com/feed"):
                    # Already logged in!
                    await context.storage_state(path=str(storage_path))
                    return {
                        'status': 'already_logged_in',
                        'message': 'Session already active'
                    }

                # Not logged in - navigate to login
                print("\n" + "="*60)
                print("🔐 MANUAL LOGIN REQUIRED")
                print("="*60)
                print("Please log in to LinkedIn in the browser window that just opened.")
                print("After you log in, this script will continue automatically.")
                print("Waiting up to 3 minutes for login...")
                print("="*60 + "\n")

                await page.goto("https://www.linkedin.com/login")

                # Wait for user to login (3 minutes max)
                await page.wait_for_url(
                    "https://www.linkedin.com/feed/**",
                    timeout=180000  # 3 minutes
                )

                print("\n✅ Login detected! Saving session...")

                # Save session state
                await context.storage_state(path=str(storage_path))

                # Extract cookies for our system
                cookies = await context.cookies()
                linkedin_cookies = self._extract_linkedin_cookies(cookies)

                return {
                    'status': 'logged_in',
                    'message': 'Session saved successfully',
                    'cookies': linkedin_cookies
                }

            except asyncio.TimeoutError:
                return {
                    'status': 'timeout',
                    'error': 'Login timeout after 3 minutes'
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'error': f'Login failed: {str(e)}'
                }
            finally:
                await context.close()

    def _extract_linkedin_cookies(self, cookies: list) -> Dict[str, Any]:
        """Extract LinkedIn cookies from browser."""
        required = ['li_at', 'JSESSIONID', 'bcookie', 'bscookie']
        result = {}

        for cookie in cookies:
            if cookie['name'] in required or cookie['name'].startswith('li_'):
                result[cookie['name']] = {
                    'value': cookie['value'],
                    'domain': cookie.get('domain'),
                    'path': cookie.get('path'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False),
                    'expirationDate': cookie.get('expires', None)
                }

        return result
```

### 2. Add API Endpoint

```python
# app/api/routes/linkedin.py

@router.post("/connect-manual")
async def connect_linkedin_manual(
    company_id: str,
    user_id: str,
    background_tasks: BackgroundTasks
):
    """
    Start manual LinkedIn login flow.

    Opens a browser window for user to login manually.
    Returns immediately, updates session when login completes.
    """
    session_id = f"{company_id}_{user_id}"

    # Launch manual login in background
    background_tasks.add_task(
        manual_login_and_save,
        session_id,
        company_id,
        user_id
    )

    return {
        'status': 'browser_launched',
        'message': 'Browser window opened. Please log in to LinkedIn.',
        'session_id': session_id
    }

async def manual_login_and_save(session_id: str, company_id: str, user_id: str):
    """Background task to handle manual login."""
    auth = ManualLinkedInAuth()
    result = await auth.start_manual_login(session_id)

    if result['status'] in ['logged_in', 'already_logged_in']:
        # Save to database
        await session_manager.create_session(
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            cookies=result.get('cookies'),
            auth_method='manual'
        )
```

### 3. Update Frontend

```typescript
// Frontend: Offer both options

async function connectLinkedIn() {
  // Show choice modal
  const method = await showAuthMethodChoice()

  if (method === 'automated') {
    // Current flow: email + password
    const result = await fetch('/api/linkedin/connect-credentials', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    })
  } else if (method === 'manual') {
    // New flow: manual login
    const result = await fetch('/api/linkedin/connect-manual', {
      method: 'POST',
      body: JSON.stringify({ company_id, user_id })
    })

    // Show instructions
    showInstructions("A browser window will open. Please log in to LinkedIn.")

    // Poll for completion
    await pollForLoginComplete(session_id)
  }
}
```

## User Experience

### Automated Flow (Current)
```
1. User enters email + password on Agencity
2. Backend handles login + 2FA
3. ✅ Session ready (30 seconds)
```

### Manual Flow (New)
```
1. User clicks "Connect LinkedIn"
2. Browser window opens → LinkedIn login page
3. User logs in (with 2FA if enabled)
4. Browser closes → ✅ Session ready (60 seconds)
```

## When to Use Each Method

### Use Automated (credential_auth.py)
- ✅ User prefers convenience
- ✅ User comfortable sharing password
- ✅ Need programmatic access
- ❌ Higher detection risk

### Use Manual (manual_auth.py)
- ✅ User concerned about security
- ✅ User has complex 2FA (hardware key)
- ✅ Want lowest detection risk
- ❌ Requires user interaction

## Testing

```bash
# Test manual login
python -c "
import asyncio
from app.services.linkedin.manual_auth import ManualLinkedInAuth

async def test():
    auth = ManualLinkedInAuth()
    result = await auth.start_manual_login('test-session-manual')
    print(result)

asyncio.run(test())
"

# Browser will open → Log in → Session saved
# ✅ Session persists in browser_profiles/test-session-manual/
```

## Comparison to personal-linkedin-agent

### What They Do
```python
# Launch browser without persistent context
browser = await p.chromium.launch(headless=False)
context = await browser.new_context(storage_state="playwright/.auth/state.json")

# Check if logged in
await page.goto("https://www.linkedin.com/feed")
if not logged_in:
    # Wait for manual login
    await page.wait_for_url("https://www.linkedin.com/feed/**", timeout=120000)
    # Save storage state only
    await context.storage_state(path="playwright/.auth/state.json")
```

### What We Do Better
```python
# Use persistent context (full browser profile)
context = await p.chromium.launch_persistent_context(
    user_data_dir=f"./browser_profiles/{session_id}",  # Full profile!
    headless=False
)

# Apply stealth
await stealth_async(page)

# Same manual login flow
# But we also extract cookies for our system
cookies = await context.cookies()
```

**Our advantages:**
- ✅ Full browser profile (not just cookies)
- ✅ playwright-stealth applied
- ✅ Cookies also saved to our database
- ✅ Can switch to headless after initial login

## Recommendation

**Offer both options:**

1. **Default: Manual Login** (safer, better UX)
   - Primary button: "Connect LinkedIn"
   - Opens browser → User logs in → Done

2. **Alternative: Automated Login** (faster)
   - Secondary link: "Use email/password instead"
   - Current credential flow

Most users will prefer manual login because:
- ✅ Don't need to share password
- ✅ Familiar (like OAuth flow)
- ✅ Handles any 2FA method
- ✅ Lower detection risk

## Implementation Priority

11- Lower detection risk
- Better user trust
- Works with all 2FA methods
- Simple to implement

⏸️ **Low Priority** - Keep automated login
- Some users prefer convenience
- Good for testing/development
- Already implemented

## Next Steps

1. ✅ Review this doc
2. ⏸️ Decide: Add manual login or not?
3. ⏸️ If yes: Implement `manual_auth.py`
4. ⏸️ Add frontend UI for method selection
5. ⏸️ Test with real LinkedIn account
6. ⏸️ Update TESTING_GUIDE.md

---

**Recommendation:** Add manual login as **primary option**, keep automated as fallback.
