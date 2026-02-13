#!/bin/bash
set -e

# Agencity Server Setup Script
# Run this on the EC2 instance after deployment

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Agencity Server Setup ===${NC}"
echo ""

# Update system
echo -e "${YELLOW}[1/8] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo -e "${YELLOW}[2/8] Installing Python 3.11 and dependencies...${NC}"
sudo apt install -y python3 python3-pip python3-venv git

# Install Redis
echo -e "${YELLOW}[3/8] Installing Redis...${NC}"
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis
if redis-cli ping | grep -q "PONG"; then
    echo "✓ Redis is running"
else
    echo -e "${RED}Redis failed to start${NC}"
    exit 1
fi

# Install Nginx
echo -e "${YELLOW}[4/8] Installing Nginx...${NC}"
sudo apt install -y nginx

# Install Certbot (for SSL)
echo -e "${YELLOW}[5/8] Installing Certbot...${NC}"
sudo apt install -y certbot python3-certbot-nginx

# Create application directory
echo -e "${YELLOW}[6/8] Creating application directory...${NC}"
sudo mkdir -p /opt/agencity
sudo chown ubuntu:ubuntu /opt/agencity

echo -e "${YELLOW}[7/8] Server dependencies installed${NC}"
echo ""
echo -e "${GREEN}Server setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Upload application code:"
echo "   From your local machine, run:"
echo "   cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity"
echo "   scp -i ~/.ssh/agencity-key.pem -r * ubuntu@\$(cat deployment-info.txt | grep PUBLIC_IP | cut -d= -f2):/opt/agencity/"
echo ""
echo "2. Setup Python environment:"
echo "   cd /opt/agencity"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install --upgrade pip"
echo "   pip install -e ."
echo ""
echo "3. Create .env file with your environment variables"
echo ""
echo "4. Run deployment script (from local machine):"
echo "   bash scripts/configure-server.sh"
