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

## 🔧 ALTERNATIVE: Manual VPS Deployment (DigitalOcean)

For maximum control and lower long-term cost.

### Option 2: DigitalOcean Droplet

**Step 1: Create Droplet**
```
1. Go to https://digitalocean.com
2. Click "Create" → "Droplets"
3. Choose:
   - Image: Ubuntu 22.04
   - Size: Basic ($5-6/month)
   - Region: Closest to your users
4. Create Droplet
5. SSH into droplet (instructions emailed)
```

**Step 2: Install Dependencies**
```bash
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Python & pip
apt install -y python3 python3-pip python3-venv

# Install Git
apt install -y git

# Install Nginx (reverse proxy)
apt install -y nginx

# Install Certbot (SSL)
apt install -y certbot python3-certbot-nginx
```

**Step 3: Clone & Setup Application**
```bash
cd /home
git clone https://github.com/YOUR_USERNAME/agencity.git
cd agencity

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Step 4: Configure Environment**
```bash
# Copy .env to server
scp .env root@YOUR_DROPLET_IP:/home/agencity/

# Set permissions
chmod 600 /home/agencity/.env
```

**Step 5: Setup Systemd Service**
```bash
# Create service file
sudo nano /etc/systemd/system/agencity.service

# Add this content:
[Unit]
Description=Agencity Backend
After=network.target

[Service]
User=root
WorkingDirectory=/home/agencity
ExecStart=/home/agencity/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target

# Save (Ctrl+X, Y, Enter)
```

**Step 6: Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable agencity
sudo systemctl start agencity
sudo systemctl status agencity  # Verify it's running
```

**Step 7: Configure Nginx**
```bash
# Create config
sudo nano /etc/nginx/sites-available/agencity

# Add this content:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/agencity /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 8: Setup SSL**
```bash
sudo certbot --nginx -d your-domain.com
# Follow prompts to setup HTTPS
```

**Cost:** $5-6/month
**Setup Time:** 15-20 minutes
**Result:** Full control, persistent ✅

---

## 📋 QUICK COMPARISON TABLE

### For Different Scenarios:

**Want Fastest Setup?**
→ **Railway or Render** (5 min, GitHub integration)

**Want Free Option?**
→ **Render Free Tier** (limited, but works)

**Want Best Value?**
→ **DigitalOcean Droplet** ($5/mo, full control)

**Want Serverless/Autoscale?**
→ **AWS Lambda** or **Vercel** (complex setup)

**Want Maximum Control?**
→ **Docker on VPS** (DigitalOcean, Linode, AWS EC2)

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

### DigitalOcean
```bash
ssh root@your-ip
sudo journalctl -u agencity -f
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

**DigitalOcean:**
```bash
ssh root@your-ip
sudo systemctl restart agencity
# Or revert git: git checkout previous-commit
```

---

## Cost Estimates (Monthly)

| Platform | Tier | Cost | Includes |
|----------|------|------|----------|
| Railway | Starter | $5-15 | 50GB bandwidth, auto-scaling |
| Render | Free | $0* | Limited CPU/Memory/Bandwidth |
| Render | Starter | $7 | Unlimited bandwidth |
| DigitalOcean | Basic | $5-6 | Full VPS control |
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

### Choose DigitalOcean if:
- ✅ Want maximum control
- ✅ Want to save money long-term
- ✅ Don't mind manual management
- ✅ Need specific configurations

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
