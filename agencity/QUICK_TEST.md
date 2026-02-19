# Quick Test Guide - LinkedIn Automation

Test your LinkedIn automation end-to-end in 5 minutes.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Run quickstart (if not already done)
./scripts/quickstart.sh

# Or manually:
pip install playwright playwright-stealth
playwright install chromium
```

### Step 2: Set Test Credentials

```bash
# Use environment variables (recommended)
export LINKEDIN_TEST_EMAIL="your-test@email.com"
export LINKEDIN_TEST_PASSWORD="your-test-password"

# Or the script will prompt you interactively
```

### Step 3: Run Test

```bash
python test_automated_flow.py
```

**That's it!** The test will:
1. Login to LinkedIn (with 2FA if needed)
2. Extract 10 connections
3. Save session for reuse
4. Verify everything works

---

## ⚠️ IMPORTANT: Use Test Account

**DO NOT use your personal LinkedIn account!**

Create a test account:
1. Use temp email: https://temp-mail.org
2. Create LinkedIn account
3. Add a few connections (optional)
4. Enable 2FA (recommended)
5. Wait 48 hours before heavy testing (optional)

---

## 🎬 What You'll See

### During Test

You will see a **Chrome browser window open** and:

1. Navigate to LinkedIn login page
2. Fill in your credentials (you'll see it type)
3. Handle 2FA if enabled
4. Navigate to connections page
5. Scroll gradually (human-like, 1-3s pauses)
6. Extract connection data
7. Close automatically

**This is normal!** The browser MUST be visible (headless=False) to avoid detection.

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
Enter 6-digit code: 123456

✅ Login successful!
   Cookies extracted: 8 cookies
   li_at: AQEDAR1234567890...

======================================================================
Phase 2: Connection Extraction (Limited to 10)
----------------------------------------------------------------------

📊 Starting extraction...
   (Browser window will open - this is normal!)

   [1] Extracting...
   [2] Extracting...
   ...
   [10] Extracting...

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
   ✅ Cookies file found

======================================================================
✅ ALL TESTS COMPLETED!
======================================================================
```

---

## ✅ Success Indicators

After the test, verify:

- [x] Browser window was VISIBLE during test
- [x] Login succeeded without CAPTCHA
- [x] 2FA handled correctly (if enabled)
- [x] At least a few connections extracted
- [x] No warnings or unusual activity messages
- [x] Session saved (check `./browser_profiles/` directory)
- [x] Connection data looks correct (names, titles, companies)

---

## ❌ Troubleshooting

### Issue: "Module not found"

```bash
pip install playwright playwright-stealth
playwright install chromium
```

### Issue: "CAPTCHA appears"

Your IP may be flagged. Solutions:
1. Wait 24 hours and try again
2. Use different network/IP
3. Use residential proxy
4. Try manual login method (see MANUAL_LOGIN_INTEGRATION.md)

### Issue: "Session expired"

Test account may be flagged:
1. Wait 48 hours
2. Create new test account
3. Use manual login method

### Issue: "No connections extracted"

This is okay if:
- Test account has no connections (add some first)
- Account is brand new (wait 24-48h)

### Issue: "Login failed"

Check:
1. Credentials are correct
2. Account is not locked
3. 2FA code is valid (6 digits)
4. Network connection is stable

---

## 🔍 Verify Stealth

After test succeeds, verify detection protection:

### Check Browser Fingerprint

```bash
# Open Chrome manually
google-chrome --user-data-dir=./browser_profiles/test-automated-XXXXXX

# Navigate to:
https://bot.sannysoft.com

# Should show: "Not a bot" ✅
```

### Check Headless Mode

```bash
# Verify all files use headless=False
grep "headless=" app/services/linkedin/*.py

# Should show:
# credential_auth.py:63:    headless=False,
# connection_extractor.py:381:    headless=False,
```

### Check Stealth Plugin

```bash
# Verify playwright-stealth is applied
grep "apply_stealth_async" app/services/linkedin/*.py

# Should show both files using it
```

---

## 📊 After Testing

### If Test Passes ✅

1. **Test session re-use**:
   ```bash
   # Run extraction again with same session
   # Should NOT require re-login
   ```

2. **Test with more connections**:
   ```python
   # Edit test_automated_flow.py
   # Change: connections[:10] to connections[:50]
   ```

3. **Monitor for 24 hours**:
   - Check for warnings
   - Verify session stays active
   - Watch for any restrictions

4. **Ready for integration**:
   - Add to API routes
   - Connect to frontend
   - Deploy to production

### If Test Fails ❌

1. **Check logs**:
   ```bash
   cat logs/linkedin_automation.log
   ```

2. **Review error message**:
   - Authentication errors → Check credentials
   - CAPTCHA → IP flagged, use proxy
   - Session expired → Account flagged, use manual login

3. **Try manual login**:
   - Safer method
   - See MANUAL_LOGIN_INTEGRATION.md
   - Requires manual_auth.py implementation

---

## 📚 Additional Resources

- **END_TO_END_TESTING.md** - Comprehensive testing guide
- **MANUAL_LOGIN_INTEGRATION.md** - Safer manual login method
- **TESTING_GUIDE.md** - Full testing process (5 phases)
- **HEADLESS_MODE_FIX.md** - Critical stealth fix details
- **IMPLEMENTATION_COMPLETE.md** - What's been implemented

---

## 🎯 Next Steps

1. **Run the test** → `python test_automated_flow.py`
2. **Verify success** → Check output and browser profiles
3. **Test session reuse** → Run extraction again
4. **Integrate to API** → Add endpoints
5. **Deploy** → Production ready!

---

## 💡 Pro Tips

1. **Test with fresh account** - Don't use flagged accounts
2. **Wait 48h** - New accounts need aging
3. **Use residential IP** - VPNs may trigger detection
4. **Monitor closely** - First 7 days are critical
5. **Start small** - Extract 10-50 connections first
6. **Add proxies later** - If detection rate > 5%

---

## Need Help?

1. Check logs: `cat logs/linkedin_automation.log`
2. Review error in test output
3. Read troubleshooting section above
4. Check stealth principles are applied
5. Try manual login as alternative

---

**Ready to test?**

```bash
python test_automated_flow.py
```

Good luck! 🚀
