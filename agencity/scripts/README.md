# Agencity Deployment Scripts

Automated deployment and testing scripts for Agencity on AWS EC2.

---

## 📋 Scripts Overview

### Deployment Scripts

#### 1. `full-deployment.sh` ⭐ RECOMMENDED
**Complete end-to-end deployment**

Automates the entire deployment process:
- Creates EC2 instance
- Configures server
- Uploads code
- Sets up services
- Runs tests

**Usage:**
```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
bash scripts/full-deployment.sh
```

**Prerequisites:**
- AWS CLI configured (`aws configure`)
- `.env` file with all environment variables
- SSH key will be created automatically

**Time:** ~10 minutes

---

#### 2. `deploy-to-ec2.sh`
**Create and configure EC2 instance**

Creates EC2 instance with proper security groups and saves deployment info.

**Usage:**
```bash
bash scripts/deploy-to-ec2.sh
```

**What it does:**
- Creates/uses SSH key pair
- Finds latest Ubuntu 22.04 AMI
- Creates security group (ports 22, 80, 443, 8001)
- Launches EC2 instance
- Saves deployment info to `deployment-info.txt`

---

#### 3. `setup-server.sh`
**Configure server dependencies**

Installs all required software on the EC2 instance.

**Usage:**
```bash
# From EC2 instance:
bash setup-server.sh

# Or from local machine:
scp -i ~/.ssh/agencity-key.pem scripts/setup-server.sh ubuntu@YOUR_IP:~/
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'bash setup-server.sh'
```

**What it installs:**
- Python 3.11+
- Redis
- Nginx
- Certbot
- Git

---

### Testing Scripts

#### 4. `test-deployment.sh` ⭐
**Comprehensive endpoint testing**

Tests all HTTP endpoints to verify deployment.

**Usage:**
```bash
bash scripts/test-deployment.sh
```

**Tests:**
- Root endpoint (/)
- Health check (/health)
- API endpoints (/api/*)
- Response times
- Concurrent requests
- Server availability

**Output:**
- ✓ PASSED / ✗ FAILED for each test
- Summary with total passed/failed
- Troubleshooting tips if failures

---

#### 5. `test-services.py`
**Integration testing for services**

Tests all external service integrations.

**Usage:**
```bash
# Install test dependencies first
pip install python-dotenv

# Run tests
python3 scripts/test-services.py
```

**Tests:**
- Environment variables
- OpenAI API connection
- Redis cache operations
- Supabase database
- Slack token validity
- GitHub token validity
- Application imports

---

## 🚀 Quick Start Guide

### Option A: Full Automated Deployment

```bash
# 1. Configure AWS credentials
aws configure

# 2. Create .env file with your environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Run full deployment
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
bash scripts/full-deployment.sh
```

That's it! The script will:
1. Create EC2 instance
2. Configure server
3. Upload code
4. Install dependencies
5. Start services
6. Run tests
7. Give you the production URL

**Total time:** ~10 minutes

---

### Option B: Step-by-Step Deployment

```bash
# 1. Deploy EC2 instance
bash scripts/deploy-to-ec2.sh

# 2. Get deployment info
source deployment-info.txt

# 3. Setup server
scp -i ~/.ssh/${KEY_NAME}.pem scripts/setup-server.sh ubuntu@${PUBLIC_IP}:~/
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'bash setup-server.sh'

# 4. Upload code
scp -i ~/.ssh/${KEY_NAME}.pem -r app/ pyproject.toml .env ubuntu@${PUBLIC_IP}:/opt/agencity/

# 5. Configure and start services (SSH into server)
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}

# On server:
cd /opt/agencity
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Create systemd service (see DEPLOYMENT_GUIDE.md)

# 6. Test deployment (from local machine)
bash scripts/test-deployment.sh
```

---

## 🧪 Running Tests

### Test Deployment Endpoints

```bash
bash scripts/test-deployment.sh
```

This will test:
- All HTTP endpoints
- Response times
- Server availability
- Concurrent request handling

### Test Service Integrations

```bash
python3 scripts/test-services.py
```

This will test:
- OpenAI API
- Redis cache
- Supabase database
- Slack integration
- GitHub API
- Environment configuration

### Quick Health Check

```bash
# Get your server IP
source deployment-info.txt

# Test health endpoint
curl http://${PUBLIC_IP}/health

# Expected response:
# {"status":"healthy","environment":"production",...}
```

---

## 📊 Deployment Info File

After running `deploy-to-ec2.sh`, you'll have a `deployment-info.txt` file:

```bash
AWS_REGION=us-east-1
INSTANCE_ID=i-0abc123def456789
PUBLIC_IP=54.123.45.67
KEY_NAME=agencity-key
SECURITY_GROUP=sg-0123456789abcdef
DEPLOYED_AT=Mon Feb 12 10:30:00 PST 2024
```

**Usage:**
```bash
# Load variables
source deployment-info.txt

# SSH into server
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}

# View logs
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'sudo journalctl -u agencity -f'
```

---

## 🔧 Useful Commands

### SSH into Server
```bash
source deployment-info.txt
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}
```

### View Application Logs
```bash
# Real-time logs
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo journalctl -u agencity -f'

# Last 100 lines
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo journalctl -u agencity -n 100'

# Application log files
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'tail -f /var/log/agencity/access.log'
```

### Restart Services
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo systemctl restart agencity'
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo systemctl restart nginx'
```

### Update Application Code
```bash
# Upload new code
source deployment-info.txt
scp -i ~/.ssh/${KEY_NAME}.pem -r app/ ubuntu@${PUBLIC_IP}:/opt/agencity/

# Restart service
ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'sudo systemctl restart agencity'
```

### Check Service Status
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP <<'EOF'
sudo systemctl status agencity
sudo systemctl status nginx
sudo systemctl status redis-server
EOF
```

---

## 🐛 Troubleshooting

### Deployment fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check for existing resources
aws ec2 describe-instances --filters "Name=tag:Name,Values=agencity-production"
aws ec2 describe-security-groups --filters "Name=group-name,Values=agencity-sg"
```

### Tests fail

```bash
# Check if service is running
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo systemctl status agencity'

# Check logs for errors
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo journalctl -u agencity -n 50'

# Test service directly
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'curl localhost:8001/health'
```

### Cannot connect to server

```bash
# Check instance is running
source deployment-info.txt
aws ec2 describe-instances --instance-ids ${INSTANCE_ID}

# Check security group
aws ec2 describe-security-groups --group-ids ${SECURITY_GROUP}

# Verify SSH key permissions
chmod 400 ~/.ssh/${KEY_NAME}.pem
```

---

## 🧹 Cleanup

### Stop Services (but keep instance)
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo systemctl stop agencity'
```

### Terminate EC2 Instance
```bash
source deployment-info.txt

# Terminate instance
aws ec2 terminate-instances --instance-ids ${INSTANCE_ID}

# Delete security group (after instance is terminated)
aws ec2 delete-security-group --group-id ${SECURITY_GROUP}

# Delete key pair
aws ec2 delete-key-pair --key-name ${KEY_NAME}
rm ~/.ssh/${KEY_NAME}.pem
```

---

## 📝 Environment Variables Required

Create a `.env` file with these variables:

```bash
# App
APP_ENV=production
DEBUG=false

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-proj-your-key
DEFAULT_MODEL=gpt-4o

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret

# GitHub
GITHUB_TOKEN=ghp_your-token

# Other APIs
PDL_API_KEY=your-key
CLADO_API_KEY=your-key

# Security
SECRET_KEY=your-random-secret-key
```

---

## 🎯 Next Steps After Deployment

1. **Update Slack Event URL**
   - Go to https://api.slack.com/apps
   - Select your app
   - Update Event Subscriptions URL to: `http://YOUR_IP/api/slack/events`

2. **Setup HTTPS** (if using domain)
   ```bash
   ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Monitor Logs**
   ```bash
   bash scripts/monitor-logs.sh  # (create this if needed)
   ```

4. **Setup Backups** (optional)
   - Configure automated snapshots in AWS Console
   - Or use AWS Backup service

---

## 📚 Additional Resources

- [Full Deployment Guide](../DEPLOYMENT_GUIDE.md)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Troubleshooting Guide](../DEPLOYMENT_GUIDE.md#troubleshooting)

---

**Need Help?**

Check the logs:
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_IP 'sudo journalctl -u agencity -f'
```

---

## 🔗 LinkedIn Automation Testing

### Quick Start

```bash
# 1. Run setup
./quickstart.sh

# 2. Set credentials
export LINKEDIN_TEST_EMAIL="your-test@email.com"
export LINKEDIN_TEST_PASSWORD="your-password"

# 3. Run test
python test_linkedin_flow.py
```

### LinkedIn Test Scripts

#### `quickstart.sh`
**One-command setup for LinkedIn automation**

**What it does:**
- Installs playwright + playwright-stealth
- Installs Chromium browser
- Creates browser_profiles/ and logs/ directories
- Shows next steps

**Usage:**
```bash
./quickstart.sh
```

#### `test_linkedin_flow.py`
**Quick test of LinkedIn automation**

**Tests:**
1. Authentication with credentials + 2FA
2. playwright-stealth (anti-detection)
3. Connection extraction (10 connections)
4. Warning detection system
5. Persistent browser profiles

**Usage:**
```bash
# With environment variables
export LINKEDIN_TEST_EMAIL="test@email.com"
export LINKEDIN_TEST_PASSWORD="password"
python test_linkedin_flow.py

# Or interactive (prompts for credentials)
python test_linkedin_flow.py
```

**Expected Output:**
```
======================================================================
PHASE 1: AUTHENTICATION TEST
======================================================================

🚀 Logging in as test@email.com...

🔐 2FA Required
Enter 6-digit verification code: 123456

✅ Login successful!
   Cookies extracted: 8 cookies
   li_at: AQEDAR...

======================================================================
PHASE 2: CONNECTION EXTRACTION TEST (LIMIT: 10)
======================================================================

📊 Starting extraction...
   [1/10] Found: Sarah Chen
           Senior ML Engineer at Stripe
...

✅ All tests completed!
```

### LinkedIn Testing Workflow

```bash
# Step 1: Setup
./quickstart.sh

# Step 2: Create test account
# - Go to LinkedIn and create account
# - Use temp email: https://temp-mail.org
# - Enable 2FA
# - Wait 48 hours (recommended)

# Step 3: Run quick test
export LINKEDIN_TEST_EMAIL="test@email.com"
export LINKEDIN_TEST_PASSWORD="password"
python test_linkedin_flow.py

# Step 4: Verify results
ls -la ../browser_profiles/
# Should see: test-session-123/

# Step 5: Check for warnings
cat ../logs/linkedin_automation.log
# Should be empty or show no errors
```

### Docker Testing

```bash
# Build image
docker build -t agencity-linkedin -f ../Dockerfile.test ..

# Run test
docker run --rm \
  -e LINKEDIN_TEST_EMAIL="test@email.com" \
  -e LINKEDIN_TEST_PASSWORD="password" \
  -v $(pwd)/../logs:/app/logs \
  -v $(pwd)/../browser_profiles:/app/browser_profiles \
  agencity-linkedin python scripts/test_linkedin_flow.py
```

### Success Indicators

✅ **Good Test:**
```
✅ Login successful
✅ 10 connections extracted
✅ No warnings detected
✅ Profile directory created
✅ Duration: 10-20 seconds
```

❌ **Bad Test:**
```
❌ CAPTCHA appeared
❌ "Unusual activity" warning
❌ Session expired immediately
❌ No connections extracted
```

### Troubleshooting

**Issue: "Module not found: playwright_stealth"**
```bash
pip install playwright-stealth
```

**Issue: "Chromium not installed"**
```bash
playwright install chromium
```

**Issue: CAPTCHA appears**
1. Verify stealth: Visit bot.sannysoft.com
2. Use different IP/proxy
3. Wait 48h with test account

**Issue: "Session expired"**
- Re-run test to get fresh cookies
- Check browser_profiles/ has Cookies file

### Full Documentation

For comprehensive testing:
- Read: `../TESTING_GUIDE.md`
- Architecture: `../docs/architecture/LINKEDIN_AUTOMATION.md`
- Implementation: `../IMPLEMENTATION_COMPLETE.md`

---

**Remember:** Always use test accounts, never personal LinkedIn accounts!
