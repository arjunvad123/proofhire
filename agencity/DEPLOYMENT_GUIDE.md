# 🚀 Backend Deployment Guide

Complete guide for deploying Agencity backend to production.

---

## Deployment Options Comparison

| Platform | Cost | Setup Time | Auto-Scaling | Database | Custom Domain | Best For |
|----------|------|-----------|--------------|----------|---------------|----------|
| **Railway** | Pay-as-you-go ($5-50/mo) | 5 min | Yes | Included | Yes | Fastest setup |
| **Render** | Free tier available | 5 min | Yes | Separate | Yes | Best free option |
| **Vercel** | Free/Pro ($20/mo) | 5 min | Yes | Separate | Yes | Serverless |
| **AWS Lambda** | Pay-as-you-go | 15 min | Yes | RDS | Yes | Scale to zero |
| **Heroku** (Legacy) | $7-50/mo | 5 min | Yes | Add-on | Yes | Easiest (shutting down) |
| **DigitalOcean** | $5-12/mo | 10 min | Manual | Separate | Yes | Control & simplicity |
| **Docker on VPS** | $5-20/mo | 20 min | Manual | Separate | Yes | Maximum control |

---

## 🥇 RECOMMENDED: Railway (Fastest & Easiest)

Railway is the recommended choice for this project because:
- ✅ Simplest setup (5 minutes)
- ✅ One-click deployment from GitHub
- ✅ Auto-scaling built-in
- ✅ Free tier available ($5 credits)
- ✅ Perfect for startups
- ✅ Easy environment variables

### Option 1A: Railway (Using GitHub)

**Prerequisites:**
- GitHub account with your repo
- Railway account (free at railway.app)

**Step 1: Push code to GitHub** (if not already done)
```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Initialize git if needed
git init
git add .
git commit -m "Initial Agencity backend with Slack integration"
git remote add origin https://github.com/YOUR_USERNAME/agencity.git
git push -u origin main
```

**Step 2: Connect Railway to GitHub**
```bash
1. Go to https://railway.app
2. Sign up/Login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your agencity repository
5. Click "Deploy"
```

**Step 3: Configure Environment Variables**
```
1. In Railway dashboard, click your project
2. Click "Variables" tab
3. Add all variables from your .env file:
   - OPENAI_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
   - SLACK_BOT_TOKEN
   - SLACK_SIGNING_SECRET
   - DATABASE_URL
   - etc.
4. Click "Save"
```

**Step 4: Get Your Production URL**
```
1. Click "Deployments" tab
2. Click the successful deployment
3. Copy the URL from "Domains" section
4. This is your production URL!
```

**Step 5: Update Slack App**
```
1. Go to https://api.slack.com/apps
2. Select "Hermes"
3. Go to "Event Subscriptions"
4. Update Request URL to:
   https://your-railway-url.railway.app/api/slack/events
5. Wait for ✅ "Verified"
6. Save Changes
```

**Cost:** ~$5-10/month (or use free tier initially)
**Setup Time:** 5 minutes
**Result:** Automatic deployment on every git push ✅

---

## 🥈 ALTERNATIVE: Render (Best Free Option)

Render has a free tier and is very similar to Railway.

### Option 1B: Render Setup

**Step 1: Push to GitHub** (same as Railway)

**Step 2: Connect Render**
```
1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Select "Deploy an existing repository"
4. Connect GitHub (grant permissions)
5. Select agencity repository
```

**Step 3: Configure Service**
```
Build Command:
  pip install -r requirements.txt

Start Command:
  uvicorn app.main:app --host 0.0.0.0 --port $PORT

Instance Type:
  Free (or Starter Pro for better performance)
```

**Step 4: Add Environment Variables**
```
1. Click "Environment" tab
2. Add all variables from .env file
3. Save
```

**Step 5: Deploy**
```
1. Click "Create Web Service"
2. Wait for deployment (~3-5 min)
3. Copy the URL from dashboard
```

**Step 6: Update Slack**
```
Same as Railway - update Event Subscriptions URL
```

**Cost:** Free tier available (with limitations), $7+/month for production
**Setup Time:** 5 minutes
**Result:** Automatic deployment ✅

---

## 🔧 AWS EC2 Deployment (Traditional)

Traditional EC2 deployment with full control. Best if you have AWS credits.

**Time:** 25-30 minutes
**Cost:** ~$10-20/month
**Best for:** Production workloads on AWS with credits

### Option 2: AWS EC2 Instance

**Step 1: Create EC2 Instance**

Using AWS Console:
```
1. Go to https://console.aws.amazon.com/ec2
2. Click "Launch Instance"
3. Configure:
   - Name: agencity-production
   - AMI: Ubuntu Server 22.04 LTS
   - Instance type: t3.small (2 vCPU, 2GB RAM) or t3.micro (Free tier)
   - Key pair: Create new → Save as ~/.ssh/agencity-key.pem
   - Network settings:
     * Create security group: agencity-sg
     * Allow: SSH (22), HTTP (80), HTTPS (443), Custom TCP (8001)
   - Storage: 20 GB gp3
4. Launch instance
5. Get public IP from EC2 dashboard
```

Or using AWS CLI:
```bash
# Set your region
export AWS_REGION=us-east-1

# Launch instance
aws ec2 run-instances \
    --image-id ami-0c7217cdde317cfec \
    --instance-type t3.small \
    --key-name agencity-key \
    --region $AWS_REGION

# Get public IP
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=agencity-production" \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text
```

**Configure SSH key permissions:**
```bash
chmod 400 ~/.ssh/agencity-key.pem

# Test connection
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

**Step 2: Install Dependencies**
```bash
# SSH into EC2 instance
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Git
sudo apt install -y git

# Install Redis (for caching)
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify Redis
redis-cli ping  # Should return "PONG"

# Install Nginx (reverse proxy)
sudo apt install -y nginx

# Install Certbot (SSL)
sudo apt install -y certbot python3-certbot-nginx

# Verify installations
python3 --version
nginx -v
```

**Step 3: Clone & Setup Application**
```bash
# Create application directory
sudo mkdir -p /opt/agencity
sudo chown ubuntu:ubuntu /opt/agencity
cd /opt/agencity

# Clone repository (if using Git)
git clone https://github.com/YOUR_USERNAME/agencity.git .

# OR upload files from local machine:
# On your LOCAL machine:
# cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
# scp -i ~/.ssh/agencity-key.pem -r * ubuntu@YOUR_EC2_IP:/opt/agencity/

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .

# Verify installation
python -c "from app.main import app; print('✓ App loaded successfully')"
```

**Step 4: Configure Environment**
```bash
# Create .env file on server
nano /opt/agencity/.env

# Paste all your environment variables:
# APP_ENV=production
# DEBUG=false
# REDIS_URL=redis://localhost:6379/0
# OPENAI_API_KEY=sk-proj-...
# SUPABASE_URL=https://...
# SUPABASE_KEY=...
# SLACK_BOT_TOKEN=xoxb-...
# SLACK_SIGNING_SECRET=...
# GITHUB_TOKEN=ghp_...
# (see Environment Variables section below for full list)

# Save (Ctrl+X, Y, Enter)

# OR copy from local machine:
# scp -i ~/.ssh/agencity-key.pem .env ubuntu@YOUR_EC2_IP:/opt/agencity/

# Set secure permissions
chmod 600 /opt/agencity/.env
```

**Step 5: Setup Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/agencity.service

# Add this content:
[Unit]
Description=Agencity AI Hiring Agent
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/agencity
Environment="PATH=/opt/agencity/venv/bin"
EnvironmentFile=/opt/agencity/.env
ExecStart=/opt/agencity/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=3
StandardOutput=append:/var/log/agencity/access.log
StandardError=append:/var/log/agencity/error.log

[Install]
WantedBy=multi-user.target

# Save (Ctrl+X, Y, Enter)

# Create log directory
sudo mkdir -p /var/log/agencity
sudo chown ubuntu:ubuntu /var/log/agencity
```

**Step 6: Start Service**
```bash
# Reload systemd, enable and start service
sudo systemctl daemon-reload
sudo systemctl enable agencity
sudo systemctl start agencity

# Check status (should show "active (running)")
sudo systemctl status agencity

# View logs
sudo journalctl -u agencity -f
# Press Ctrl+C to stop viewing logs
```

**Step 7: Configure Nginx**
```bash
# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Create Agencity config
sudo nano /etc/nginx/sites-available/agencity

# Add this content (replace YOUR_EC2_PUBLIC_IP with your IP):
server {
    listen 80;
    server_name YOUR_EC2_PUBLIC_IP;  # Or your domain: yourdomain.com

    # Increase timeouts for long-running requests
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Slack webhook endpoint
    location /api/slack/ {
        proxy_pass http://127.0.0.1:8001/api/slack/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Save (Ctrl+X, Y, Enter)

# Enable site
sudo ln -s /etc/nginx/sites-available/agencity /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

**Step 8: Test Deployment**
```bash
# From your LOCAL machine:

# Test health endpoint
curl http://YOUR_EC2_PUBLIC_IP/health

# Expected response:
# {"status":"healthy","environment":"production"...}

# Test root endpoint
curl http://YOUR_EC2_PUBLIC_IP/

# Expected response:
# {"name":"Agencity","status":"ok","version":"0.1.0"...}
```

**Step 9: Update Slack Event Subscription**
```
1. Go to https://api.slack.com/apps
2. Select "Hermes" app
3. Go to "Event Subscriptions"
4. Update Request URL to: http://YOUR_EC2_PUBLIC_IP/api/slack/events
5. Wait for ✅ "Verified"
6. Save Changes
```

**Step 10: Setup HTTPS/SSL (Production)**

If you have a domain name:
```bash
# SSH into server
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Update Nginx config with your domain
sudo nano /etc/nginx/sites-available/agencity
# Change: server_name YOUR_EC2_PUBLIC_IP;
# To: server_name yourdomain.com;

# Reload Nginx
sudo systemctl reload nginx

# Get SSL certificate (free with Let's Encrypt)
sudo certbot --nginx -d yourdomain.com

# Follow prompts - certificate auto-renews every 90 days
# Test auto-renewal:
sudo certbot renew --dry-run
```

**Cost:** $10-20/month (t3.micro ~$7.50, t3.small ~$15)
**Setup Time:** 25-30 minutes
**Result:** Full control, production-ready ✅

---

## 📋 QUICK COMPARISON TABLE

### For Different Scenarios:

**Want Fastest Setup?**
→ **Railway or Render** (5 min, GitHub integration)

**Want Free Option?**
→ **Render Free Tier** (limited, but works)

**Want Best Value?**
→ **AWS EC2** ($10-20/mo, full control, use credits)

**Want Serverless/Autoscale?**
→ **AWS Lambda** or **Vercel** (complex setup)

**Want Maximum Control?**
→ **AWS EC2** (traditional deployment, full access)

---

## Step-by-Step: Railway (Recommended)

I'll guide you through Railway step by step.

### Prerequisites Check:
```bash
# 1. Have GitHub account? (yes/no)
# 2. Repo pushed to GitHub? (yes/no)
# 3. Have all .env variables ready? (yes/no)
```

### If all yes, proceed:

**Step 1: Create GitHub Repo (if needed)**
```bash
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Check if git repo exists
git status

# If not, initialize:
git init
git add .
git commit -m "Agencity backend ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/agencity.git
git push -u origin main
```

**Step 2: Go to Railway.app**
```
https://railway.app → Sign up with GitHub → Authorize
```

**Step 3: Create New Project**
```
Click "New Project" → "Deploy from GitHub repo"
→ Select agencity repo → Click "Deploy"
```

**Step 4: Add Environment Variables**
```
In Railway dashboard:
1. Project Settings → Variables
2. Paste all from .env file:

OPENAI_API_KEY=sk-proj-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=45e...
DATABASE_URL=postgresql+asyncpg://...

3. Save
```

**Step 5: Get URL**
```
Deployments → Click latest → Copy "Railway URL"

Example: https://agencity-production.up.railway.app
```

**Step 6: Update Slack App**
```
1. api.slack.com/apps
2. Hermes → Event Subscriptions
3. Request URL: https://YOUR-RAILWAY-URL/api/slack/events
4. Save
```

**Done! 🎉**

---

## Testing Deployment

Once deployed, test your backend:

```bash
# Test health endpoint
curl https://your-production-url/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "llm_configured": true,
  "github_configured": true
}

# Test Slack webhook endpoint
curl https://your-production-url/api/slack/install

# Expected response:
{
  "status": "not_configured",
  "message": "Slack OAuth not configured",
  ...
}
```

---

## Monitoring & Logs

### Railway
```
Dashboard → Logs tab → View real-time logs
```

### Render
```
Dashboard → Logs tab → View application logs
```

### AWS EC2
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_EC2_IP
sudo journalctl -u agencity -f

# View application logs
tail -f /var/log/agencity/access.log
tail -f /var/log/agencity/error.log
```

---

## Environment Variables You Need

All of these from your `.env` file:

```bash
# LLM
OPENAI_API_KEY=sk-proj-...
DEFAULT_MODEL=gpt-4o

# GitHub
GITHUB_TOKEN=ghp_...

# APIs
PDL_API_KEY=...
PERPLEXITY_API_KEY=...
GOOGLE_CSE_API_KEY=...

# Supabase
SUPABASE_URL=https://npqjuljzpjvcqmrgpyqj.supabase.co
SUPABASE_KEY=eyJ...

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=45e...
SLACK_CLIENT_ID=  (optional)
SLACK_CLIENT_SECRET=  (optional)
SLACK_REDIRECT_URI=  (optional)

# Database
DATABASE_URL=postgresql+asyncpg://...

# Other
PINECONE_API_KEY=...
APP_ENV=production
DEBUG=false
```

---

## Post-Deployment Checklist

- ☑ Backend deployed and running
- ☑ Health endpoint returns 200
- ☑ Environment variables set
- ☑ Slack Event URL updated
- ☑ Slack bot token verified
- ☑ Database connection working
- ☑ Search API responding
- ☑ Logs being monitored
- ☑ Auto-scaling configured (if applicable)
- ☑ SSL/HTTPS enabled

---

## Troubleshooting Deployment

### Issue: Build fails
```
Check logs for:
- Missing dependencies (pip install -r requirements.txt)
- Python version mismatch
- Environment variables not set
```

### Issue: Application crashes
```
Check:
- All environment variables present
- Database connection string correct
- API keys valid
- Port not in use
```

### Issue: Slack webhook fails
```
Check:
- Production URL in Slack Event Subscriptions
- Signature verification enabled
- All Slack credentials correct
```

---

## Rollback Plan

If something goes wrong:

**Railway:**
```
Dashboard → Deployments → Click previous → Click "Redeploy"
```

**Render:**
```
Dashboard → Deployments → Click previous → Deploy again
```

**AWS EC2:**
```bash
ssh -i ~/.ssh/agencity-key.pem ubuntu@YOUR_EC2_IP
sudo systemctl restart agencity
# Or revert git: cd /opt/agencity && git checkout previous-commit && sudo systemctl restart agencity
```

---

## Cost Estimates (Monthly)

| Platform | Tier | Cost | Includes |
|----------|------|------|----------|
| Railway | Starter | $5-15 | 50GB bandwidth, auto-scaling |
| Render | Free | $0* | Limited CPU/Memory/Bandwidth |
| Render | Starter | $7 | Unlimited bandwidth |
| AWS EC2 | t3.micro | $7-10 | 2 vCPU, 1GB RAM, Free tier eligible |
| AWS EC2 | t3.small | $15-20 | 2 vCPU, 2GB RAM |
| AWS Lambda | Pay-as-use | $0-20 | Serverless, auto-scale |
| Vercel | Free | $0* | Limited serverless executions |

*Free tiers have limitations

---

## Which Should You Choose?

### Choose Railway if:
- ✅ Want fastest setup
- ✅ Don't mind paying $5-15/month
- ✅ Want automatic deployments from GitHub
- ✅ Want best integration with tools

### Choose Render if:
- ✅ Want to test for free
- ✅ Want professional features
- ✅ Don't mind slightly slower setup
- ✅ Plan to upgrade to paid eventually

### Choose AWS EC2 if:
- ✅ Have AWS credits to use
- ✅ Want maximum control
- ✅ Traditional deployment approach
- ✅ Don't mind manual management
- ✅ Need specific configurations
- ✅ Want to integrate with other AWS services

---

## Next Steps

1. **Choose a platform** (Railway recommended)
2. **Prepare GitHub repo** (push code if not done)
3. **Follow the deployment guide** for your chosen platform
4. **Add environment variables**
5. **Update Slack Event URL**
6. **Test the deployment**
7. **Monitor the logs**

---

*Ready to deploy? Let me know which platform you choose!*
