#!/bin/bash
set -e

# AWS EC2 Deployment Script for Agencity
# This script helps deploy Agencity to AWS EC2

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Agencity EC2 Deployment Script ===${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install: brew install awscli${NC}"
    exit 1
fi
echo "✓ AWS CLI installed"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS credentials not configured. Run: aws configure${NC}"
    exit 1
fi
echo "✓ AWS credentials configured"

# Get AWS account info
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ AWS Account: $AWS_ACCOUNT_ID"

# Configuration
read -p "Enter AWS region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}
export AWS_REGION

read -p "Enter instance type (t3.micro for free tier, t3.small for production): " INSTANCE_TYPE
INSTANCE_TYPE=${INSTANCE_TYPE:-t3.small}

read -p "Enter key pair name (default: agencity-key): " KEY_NAME
KEY_NAME=${KEY_NAME:-agencity-key}

echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Region: $AWS_REGION"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Key Pair: $KEY_NAME"
echo ""

# Check if key pair exists
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo "✓ Key pair '$KEY_NAME' exists"
else
    echo -e "${YELLOW}Creating key pair '$KEY_NAME'...${NC}"

    # Create key pair
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text \
        --region "$AWS_REGION" > ~/.ssh/${KEY_NAME}.pem

    chmod 400 ~/.ssh/${KEY_NAME}.pem
    echo "✓ Key pair created and saved to ~/.ssh/${KEY_NAME}.pem"
fi

# Get latest Ubuntu 22.04 AMI
echo -e "${YELLOW}Finding latest Ubuntu 22.04 AMI...${NC}"
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text \
    --region "$AWS_REGION")

if [ -z "$AMI_ID" ]; then
    echo -e "${RED}Failed to find Ubuntu AMI${NC}"
    exit 1
fi
echo "✓ Using AMI: $AMI_ID"

# Create security group
echo -e "${YELLOW}Creating security group...${NC}"

# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region "$AWS_REGION")

if [ "$VPC_ID" = "None" ] || [ -z "$VPC_ID" ]; then
    echo -e "${RED}No default VPC found. Please create one in AWS Console.${NC}"
    exit 1
fi
echo "✓ Using VPC: $VPC_ID"

# Check if security group exists
SG_NAME="agencity-sg"
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region "$AWS_REGION" 2>/dev/null)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    echo "Creating new security group..."

    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "Security group for Agencity backend" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' \
        --output text \
        --region "$AWS_REGION")

    # Add inbound rules
    # SSH
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION" > /dev/null

    # HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION" > /dev/null

    # HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION" > /dev/null

    # Port 8001 (for testing)
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port 8001 \
        --cidr 0.0.0.0/0 \
        --region "$AWS_REGION" > /dev/null

    echo "✓ Security group created: $SG_ID"
else
    echo "✓ Using existing security group: $SG_ID"
fi

# Launch EC2 instance
echo -e "${YELLOW}Launching EC2 instance...${NC}"

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=agencity-production}]" \
    --query 'Instances[0].InstanceId' \
    --output text \
    --region "$AWS_REGION")

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}Failed to launch instance${NC}"
    exit 1
fi

echo "✓ Instance launched: $INSTANCE_ID"
echo -e "${YELLOW}Waiting for instance to be running...${NC}"

aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$AWS_REGION"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text \
    --region "$AWS_REGION")

echo "✓ Instance is running!"
echo ""
echo -e "${GREEN}=== Deployment Information ===${NC}"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Key: ~/.ssh/${KEY_NAME}.pem"
echo ""
echo -e "${YELLOW}SSH Command:${NC}"
echo "ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo -e "${YELLOW}Waiting 60 seconds for instance to fully initialize...${NC}"
sleep 60

# Save deployment info
cat > deployment-info.txt <<EOF
AWS_REGION=$AWS_REGION
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
KEY_NAME=$KEY_NAME
SECURITY_GROUP=$SG_ID
DEPLOYED_AT=$(date)
EOF

echo "✓ Deployment info saved to deployment-info.txt"
echo ""
echo -e "${GREEN}EC2 instance is ready!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. SSH into the instance:"
echo "   ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "2. Run the server setup script:"
echo "   scp -i ~/.ssh/${KEY_NAME}.pem scripts/setup-server.sh ubuntu@${PUBLIC_IP}:~/"
echo "   ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP} 'bash setup-server.sh'"
echo ""
echo "3. Or follow the manual steps in DEPLOYMENT_GUIDE.md"
