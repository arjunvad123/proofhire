#!/bin/bash
set -e

# Full Agencity Deployment Script
# Deploys and configures Agencity on AWS EC2 from start to finish

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Agencity Full Deployment to AWS EC2             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_DIR"

# Step 1: Deploy EC2 instance
echo -e "${BLUE}[1/6] Deploying EC2 Instance${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ ! -f "scripts/deploy-to-ec2.sh" ]; then
    echo -e "${RED}Error: deploy-to-ec2.sh not found${NC}"
    exit 1
fi

chmod +x scripts/deploy-to-ec2.sh
bash scripts/deploy-to-ec2.sh

if [ ! -f "deployment-info.txt" ]; then
    echo -e "${RED}Error: deployment-info.txt not created${NC}"
    exit 1
fi

# Load deployment info
source deployment-info.txt

echo ""
echo -e "${GREEN}✓ EC2 instance deployed${NC}"
echo ""

# Step 2: Setup server
echo -e "${BLUE}[2/6] Setting Up Server${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Copying setup script to server..."
scp -i ~/.ssh/${KEY_NAME}.pem \
    -o StrictHostKeyChecking=no \
    scripts/setup-server.sh \
    ubuntu@${PUBLIC_IP}:~/

echo "Running setup script on server..."
ssh -i ~/.ssh/${KEY_NAME}.pem \
    -o StrictHostKeyChecking=no \
    ubuntu@${PUBLIC_IP} \
    'bash ~/setup-server.sh'

echo ""
echo -e "${GREEN}✓ Server configured${NC}"
echo ""

# Step 3: Upload application code
echo -e "${BLUE}[3/6] Uploading Application Code${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Uploading application files..."
scp -i ~/.ssh/${KEY_NAME}.pem \
    -o StrictHostKeyChecking=no \
    -r app/ pyproject.toml Dockerfile \
    ubuntu@${PUBLIC_IP}:/opt/agencity/

echo ""
echo -e "${GREEN}✓ Code uploaded${NC}"
echo ""

# Step 4: Check for .env file
echo -e "${BLUE}[4/6] Environment Configuration${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ -f ".env" ]; then
    echo "Found .env file, uploading..."
    scp -i ~/.ssh/${KEY_NAME}.pem \
        -o StrictHostKeyChecking=no \
        .env \
        ubuntu@${PUBLIC_IP}:/opt/agencity/

    ssh -i ~/.ssh/${KEY_NAME}.pem \
        -o StrictHostKeyChecking=no \
        ubuntu@${PUBLIC_IP} \
        'chmod 600 /opt/agencity/.env'

    echo -e "${GREEN}✓ Environment variables configured${NC}"
else
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo "Please create .env file and upload manually:"
    echo "  scp -i ~/.ssh/${KEY_NAME}.pem .env ubuntu@${PUBLIC_IP}:/opt/agencity/"
    echo ""
    read -p "Press Enter when .env is uploaded..."
fi

echo ""

# Step 5: Install Python dependencies and setup services
echo -e "${BLUE}[5/6] Installing Dependencies and Configuring Services${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

ssh -i ~/.ssh/${KEY_NAME}.pem \
    -o StrictHostKeyChecking=no \
    ubuntu@${PUBLIC_IP} <<'ENDSSH'

set -e

cd /opt/agencity

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/agencity.service > /dev/null <<'EOF'
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
EOF

# Create log directory
sudo mkdir -p /var/log/agencity
sudo chown ubuntu:ubuntu /var/log/agencity

# Start service
echo "Starting Agencity service..."
sudo systemctl daemon-reload
sudo systemctl enable agencity
sudo systemctl start agencity

# Wait for service to start
sleep 5

# Check service status
sudo systemctl status agencity --no-pager || true

# Configure Nginx
echo "Configuring Nginx..."
sudo rm -f /etc/nginx/sites-enabled/default

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

sudo tee /etc/nginx/sites-available/agencity > /dev/null <<EOF
server {
    listen 80;
    server_name $PUBLIC_IP;

    # Increase timeouts
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
    send_timeout 300;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /api/slack/ {
        proxy_pass http://127.0.0.1:8001/api/slack/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/agencity /etc/nginx/sites-enabled/ || true
sudo nginx -t
sudo systemctl restart nginx

echo "✓ All services configured and started"

ENDSSH

echo ""
echo -e "${GREEN}✓ Services configured and running${NC}"
echo ""

# Step 6: Run tests
echo -e "${BLUE}[6/6] Running Deployment Tests${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Wait for services to stabilize
echo "Waiting 10 seconds for services to stabilize..."
sleep 10

# Run tests
chmod +x scripts/test-deployment.sh
bash scripts/test-deployment.sh

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ DEPLOYMENT COMPLETE AND VERIFIED!                 ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Deployment Summary:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${YELLOW}Server URL:${NC} http://${PUBLIC_IP}"
    echo -e "${YELLOW}Instance ID:${NC} ${INSTANCE_ID}"
    echo -e "${YELLOW}Region:${NC} ${AWS_REGION}"
    echo ""
    echo -e "${YELLOW}SSH Access:${NC}"
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
    echo ""
    echo -e "${YELLOW}View Logs:${NC}"
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'sudo journalctl -u agencity -f'"
    echo ""
    echo -e "${YELLOW}Slack Event URL (update in Slack app settings):${NC}"
    echo "  http://${PUBLIC_IP}/api/slack/events"
    echo ""
    echo -e "${YELLOW}Health Check:${NC}"
    echo "  curl http://${PUBLIC_IP}/health"
    echo ""
else
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ DEPLOYMENT COMPLETED WITH ERRORS                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Check logs for issues:${NC}"
    echo "  ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'sudo journalctl -u agencity -n 100'"
    echo ""
fi
