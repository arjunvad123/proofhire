# 🚀 AWS Production Deployment Guide - Agencity

Complete guide for deploying Agencity to AWS production environment.

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Production Setup                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Internet Gateway                                            │
│       │                                                      │
│       ▼                                                      │
│  Application Load Balancer (ALB)                            │
│       │                                                      │
│       ▼                                                      │
│  ECS Fargate (Auto-scaling)                                 │
│  ├─ Container 1 (Agencity Backend)                          │
│  ├─ Container 2 (Agencity Backend)                          │
│  └─ Container N (Auto-scaled)                               │
│       │                                                      │
│       ├──────────────┐                                       │
│       ▼              ▼                                       │
│  ElastiCache    Secrets Manager                             │
│  (Redis)        (Environment Variables)                     │
│                                                              │
│  External Services:                                          │
│  • Supabase (Database)                                      │
│  • OpenAI API                                               │
│  • Slack API                                                │
│  • GitHub API                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Deployment Options for AWS

### Option 1: ECS Fargate (Recommended) ⭐
**Best for**: Production workloads with auto-scaling
- **Cost**: ~$30-80/month (with auto-scaling)
- **Setup Time**: 20 minutes
- **Pros**: Serverless containers, auto-scaling, managed infrastructure
- **Cons**: More complex than single EC2

### Option 2: AWS App Runner (Easiest)
**Best for**: Quick deployment, simpler setup
- **Cost**: ~$20-50/month
- **Setup Time**: 10 minutes
- **Pros**: Simplest AWS option, auto-scaling, automatic deployments
- **Cons**: Less control than ECS

### Option 3: Elastic Beanstalk
**Best for**: Traditional PaaS experience
- **Cost**: ~$25-60/month
- **Setup Time**: 15 minutes
- **Pros**: Easy deployment, managed platform
- **Cons**: Less flexible than ECS

### Option 4: Lambda + API Gateway (Serverless)
**Best for**: Pay-per-use, extremely variable traffic
- **Cost**: $0-20/month (depends on usage)
- **Setup Time**: 30 minutes
- **Pros**: Pay only for requests, infinite scale
- **Cons**: Cold starts, complex Slack webhook integration

### Option 5: Single EC2 Instance (Simple)
**Best for**: Testing, low traffic, maximum control
- **Cost**: ~$10-20/month
- **Setup Time**: 25 minutes
- **Pros**: Full control, predictable cost
- **Cons**: No auto-scaling, manual management

---

## 🥇 RECOMMENDED: ECS Fargate Deployment

### Why ECS Fargate?
- ✅ Serverless containers (no EC2 management)
- ✅ Auto-scaling built-in
- ✅ Load balancer included
- ✅ Perfect for production
- ✅ Uses your existing Docker image
- ✅ High availability across AZs
- ✅ Best use of AWS credits

---

## 📦 Prerequisites

### 1. AWS Account Setup
```bash
# Install AWS CLI
brew install awscli  # macOS
# or
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Configure AWS credentials
aws configure
# Enter:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region (e.g., us-east-1)
#   Default output format: json
```

### 2. Install Required Tools
```bash
# Install Docker (if not installed)
brew install --cask docker  # macOS

# Install ECS CLI (optional, helpful)
brew install amazon-ecs-cli

# Verify installations
aws --version
docker --version
```

### 3. Choose AWS Region
Recommended regions (closest to your users):
- `us-east-1` (N. Virginia) - Cheapest, most services
- `us-west-2` (Oregon) - Good for West Coast
- `eu-west-1` (Ireland) - Europe
- `ap-southeast-1` (Singapore) - Asia

---

## 🚀 ECS Fargate Deployment (Step-by-Step)

### Step 1: Create ECR Repository (Container Registry)

```bash
# Navigate to project
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity

# Set variables
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPOSITORY=agencity

# Create ECR repository
aws ecr create-repository \
    --repository-name $ECR_REPOSITORY \
    --region $AWS_REGION

# Output will show repository URI
# Example: 123456789012.dkr.ecr.us-east-1.amazonaws.com/agencity
```

### Step 2: Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image
docker build -t agencity .

# Tag image for ECR
docker tag agencity:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agencity:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agencity:latest

# Verify push
aws ecr describe-images --repository-name agencity --region $AWS_REGION
```

### Step 3: Create Secrets in AWS Secrets Manager

```bash
# Create secrets for sensitive environment variables
# This is more secure than hardcoding in task definition

# Create a JSON file with all secrets
cat > secrets.json <<EOF
{
  "OPENAI_API_KEY": "sk-proj-your-key",
  "SUPABASE_KEY": "your-supabase-key",
  "SLACK_BOT_TOKEN": "xoxb-your-token",
  "SLACK_SIGNING_SECRET": "your-signing-secret",
  "GITHUB_TOKEN": "ghp_your-token",
  "PDL_API_KEY": "your-pdl-key",
  "CLADO_API_KEY": "lk_your-key",
  "SECRET_KEY": "your-secret-key"
}
EOF

# Create secret in AWS Secrets Manager
aws secretsmanager create-secret \
    --name agencity/production \
    --description "Agencity production environment variables" \
    --secret-string file://secrets.json \
    --region $AWS_REGION

# Clean up local secrets file
rm secrets.json

# Get secret ARN for later use
aws secretsmanager describe-secret \
    --secret-id agencity/production \
    --region $AWS_REGION \
    --query ARN --output text
```

### Step 4: Create ElastiCache Redis (Optional but Recommended)

```bash
# Create security group for Redis
aws ec2 create-security-group \
    --group-name agencity-redis-sg \
    --description "Security group for Agencity Redis" \
    --region $AWS_REGION

# Get the security group ID
REDIS_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=agencity-redis-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region $AWS_REGION)

# Allow inbound Redis traffic (port 6379) from ECS tasks
# We'll update this after creating ECS security group

# Create Redis cluster (smallest instance for cost)
aws elasticache create-cache-cluster \
    --cache-cluster-id agencity-redis \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1 \
    --security-group-ids $REDIS_SG_ID \
    --region $AWS_REGION

# Wait for Redis to be available (takes ~5 minutes)
aws elasticache wait cache-cluster-available \
    --cache-cluster-id agencity-redis \
    --region $AWS_REGION

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id agencity-redis \
    --show-cache-node-info \
    --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" \
    --output text \
    --region $AWS_REGION)

echo "Redis endpoint: $REDIS_ENDPOINT:6379"
```

### Step 5: Create ECS Cluster

```bash
# Create ECS cluster (Fargate serverless)
aws ecs create-cluster \
    --cluster-name agencity-production \
    --region $AWS_REGION

# Verify cluster created
aws ecs describe-clusters \
    --clusters agencity-production \
    --region $AWS_REGION
```

### Step 6: Create IAM Role for ECS Tasks

```bash
# Create trust policy for ECS tasks
cat > ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name agencityTaskExecutionRole \
    --assume-role-policy-document file://ecs-task-trust-policy.json

# Attach AWS managed policy for ECS task execution
aws iam attach-role-policy \
    --role-name agencityTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create policy for Secrets Manager access
cat > secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production-*"
    }
  ]
}
EOF

# Create and attach secrets policy
aws iam put-role-policy \
    --role-name agencityTaskExecutionRole \
    --policy-name SecretsManagerAccess \
    --policy-document file://secrets-policy.json

# Clean up policy files
rm ecs-task-trust-policy.json secrets-policy.json

# Get role ARN for task definition
TASK_ROLE_ARN=$(aws iam get-role \
    --role-name agencityTaskExecutionRole \
    --query Role.Arn --output text)

echo "Task Execution Role ARN: $TASK_ROLE_ARN"
```

### Step 7: Create ECS Task Definition

```bash
# Create task definition JSON
cat > task-definition.json <<EOF
{
  "family": "agencity",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$TASK_ROLE_ARN",
  "containerDefinitions": [
    {
      "name": "agencity",
      "image": "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agencity:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        },
        {
          "name": "DEBUG",
          "value": "false"
        },
        {
          "name": "SUPABASE_URL",
          "value": "https://your-project.supabase.co"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://$REDIS_ENDPOINT:6379/0"
        },
        {
          "name": "DEFAULT_MODEL",
          "value": "gpt-4o"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:OPENAI_API_KEY::"
        },
        {
          "name": "SUPABASE_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:SUPABASE_KEY::"
        },
        {
          "name": "SLACK_BOT_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:SLACK_BOT_TOKEN::"
        },
        {
          "name": "SLACK_SIGNING_SECRET",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:SLACK_SIGNING_SECRET::"
        },
        {
          "name": "GITHUB_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:GITHUB_TOKEN::"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:$AWS_REGION:$AWS_ACCOUNT_ID:secret:agencity/production:SECRET_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agencity",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
EOF

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region $AWS_REGION

# Verify task definition
aws ecs describe-task-definition \
    --task-definition agencity \
    --region $AWS_REGION
```

### Step 8: Create Application Load Balancer

```bash
# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=isDefault,Values=true" \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region $AWS_REGION)

# Get subnets in default VPC
SUBNET_IDS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" \
    --query "Subnets[*].SubnetId" \
    --output text \
    --region $AWS_REGION)

# Convert to array
SUBNET_ARRAY=($SUBNET_IDS)

# Create security group for ALB
aws ec2 create-security-group \
    --group-name agencity-alb-sg \
    --description "Security group for Agencity ALB" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION

ALB_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=agencity-alb-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region $AWS_REGION)

# Allow HTTP and HTTPS traffic to ALB
aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

aws ec2 authorize-security-group-ingress \
    --group-id $ALB_SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region $AWS_REGION

# Create Application Load Balancer
aws elbv2 create-load-balancer \
    --name agencity-alb \
    --subnets ${SUBNET_ARRAY[@]} \
    --security-groups $ALB_SG_ID \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --region $AWS_REGION

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
    --names agencity-alb \
    --query "LoadBalancers[0].LoadBalancerArn" \
    --output text \
    --region $AWS_REGION)

# Get ALB DNS name (this is your public URL)
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names agencity-alb \
    --query "LoadBalancers[0].DNSName" \
    --output text \
    --region $AWS_REGION)

echo "ALB URL: http://$ALB_DNS"

# Create target group
aws elbv2 create-target-group \
    --name agencity-tg \
    --protocol HTTP \
    --port 8001 \
    --vpc-id $VPC_ID \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region $AWS_REGION

# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
    --names agencity-tg \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text \
    --region $AWS_REGION)

# Create listener (HTTP for now, add HTTPS later)
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $AWS_REGION
```

### Step 9: Create Security Group for ECS Tasks

```bash
# Create security group for ECS tasks
aws ec2 create-security-group \
    --group-name agencity-ecs-sg \
    --description "Security group for Agencity ECS tasks" \
    --vpc-id $VPC_ID \
    --region $AWS_REGION

ECS_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=agencity-ecs-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region $AWS_REGION)

# Allow traffic from ALB to ECS tasks on port 8001
aws ec2 authorize-security-group-ingress \
    --group-id $ECS_SG_ID \
    --protocol tcp \
    --port 8001 \
    --source-group $ALB_SG_ID \
    --region $AWS_REGION

# Allow ECS tasks to access Redis
aws ec2 authorize-security-group-ingress \
    --group-id $REDIS_SG_ID \
    --protocol tcp \
    --port 6379 \
    --source-group $ECS_SG_ID \
    --region $AWS_REGION
```

### Step 10: Create ECS Service

```bash
# Create ECS service with auto-scaling
aws ecs create-service \
    --cluster agencity-production \
    --service-name agencity-service \
    --task-definition agencity \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_ARRAY[0]},${SUBNET_ARRAY[1]}],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=$TG_ARN,containerName=agencity,containerPort=8001" \
    --health-check-grace-period-seconds 60 \
    --region $AWS_REGION

# Wait for service to stabilize
aws ecs wait services-stable \
    --cluster agencity-production \
    --services agencity-service \
    --region $AWS_REGION

echo "Service deployed successfully!"
echo "Access your application at: http://$ALB_DNS"
```

### Step 11: Configure Auto-Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/agencity-production/agencity-service \
    --min-capacity 2 \
    --max-capacity 10 \
    --region $AWS_REGION

# Create scaling policy based on CPU utilization
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --scalable-dimension ecs:service:DesiredCount \
    --resource-id service/agencity-production/agencity-service \
    --policy-name agencity-cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "ScaleInCooldown": 300,
        "ScaleOutCooldown": 60
    }' \
    --region $AWS_REGION

echo "Auto-scaling configured: 2-10 tasks based on CPU > 70%"
```

---

## 🔒 Adding HTTPS/SSL (Production Required)

### Option A: Using AWS Certificate Manager (ACM) - Free SSL

```bash
# Prerequisites: You need a domain name registered

# Step 1: Request certificate in ACM
aws acm request-certificate \
    --domain-name yourdomain.com \
    --subject-alternative-names www.yourdomain.com \
    --validation-method DNS \
    --region $AWS_REGION

# Step 2: Get certificate ARN
CERT_ARN=$(aws acm list-certificates \
    --query "CertificateSummaryList[?DomainName=='yourdomain.com'].CertificateArn" \
    --output text \
    --region $AWS_REGION)

# Step 3: Validate certificate (add DNS records shown in ACM console)
# Go to ACM console to see required DNS records

# Step 4: Create HTTPS listener
aws elbv2 create-listener \
    --load-balancer-arn $ALB_ARN \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=$CERT_ARN \
    --default-actions Type=forward,TargetGroupArn=$TG_ARN \
    --region $AWS_REGION

# Step 5: Redirect HTTP to HTTPS (modify existing listener)
HTTP_LISTENER_ARN=$(aws elbv2 describe-listeners \
    --load-balancer-arn $ALB_ARN \
    --query "Listeners[?Port==\`80\`].ListenerArn" \
    --output text \
    --region $AWS_REGION)

aws elbv2 modify-listener \
    --listener-arn $HTTP_LISTENER_ARN \
    --default-actions '[{
        "Type": "redirect",
        "RedirectConfig": {
            "Protocol": "HTTPS",
            "Port": "443",
            "StatusCode": "HTTP_301"
        }
    }]' \
    --region $AWS_REGION

# Step 6: Update Route53 DNS to point to ALB
# Create A record pointing yourdomain.com to ALB_DNS
```

---

## 📊 Monitoring & Logging

### View Logs in CloudWatch

```bash
# View recent logs
aws logs tail /ecs/agencity --follow --region $AWS_REGION

# View specific time range
aws logs filter-log-events \
    --log-group-name /ecs/agencity \
    --start-time $(date -u -d '1 hour ago' +%s)000 \
    --region $AWS_REGION
```

### Monitor ECS Service

```bash
# Check service status
aws ecs describe-services \
    --cluster agencity-production \
    --services agencity-service \
    --region $AWS_REGION

# List running tasks
aws ecs list-tasks \
    --cluster agencity-production \
    --service-name agencity-service \
    --region $AWS_REGION
```

---

## 🔄 Updating Your Application

### Quick Update Process

```bash
# 1. Build new image with changes
docker build -t agencity .

# 2. Tag new version
docker tag agencity:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agencity:latest

# 3. Push to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/agencity:latest

# 4. Force new deployment (ECS will pull latest image)
aws ecs update-service \
    --cluster agencity-production \
    --service agencity-service \
    --force-new-deployment \
    --region $AWS_REGION

# ECS will perform rolling update (zero downtime)
```

---

## 💰 Cost Breakdown (Monthly Estimates)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| **ECS Fargate** | 2 tasks (0.5 vCPU, 1GB RAM) | ~$30 |
| **Application Load Balancer** | Standard | ~$16 |
| **ElastiCache Redis** | cache.t3.micro | ~$12 |
| **NAT Gateway** | 1 AZ (if needed) | ~$32 |
| **Data Transfer** | 50GB/month | ~$5 |
| **CloudWatch Logs** | 5GB/month | ~$2.50 |
| **Secrets Manager** | 1 secret | ~$0.40 |
| **ECR Storage** | <1GB | <$1 |
| **Total** | | **~$65-100/month** |

**Cost Optimization Tips:**
- Remove NAT Gateway if not needed (use public subnets)
- Use Redis on-demand pricing
- Enable ECS auto-scaling to scale to 0 during off-hours
- Use CloudWatch Logs retention policies

---

## 🚀 Alternative: AWS App Runner (Simpler Option)

If ECS is too complex, App Runner is much simpler:

```bash
# Create App Runner service directly from ECR
aws apprunner create-service \
    --service-name agencity \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "'$AWS_ACCOUNT_ID'.dkr.ecr.'$AWS_REGION'.amazonaws.com/agencity:latest",
            "ImageConfiguration": {
                "Port": "8001",
                "RuntimeEnvironmentVariables": {
                    "APP_ENV": "production",
                    "DEBUG": "false"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": true
    }' \
    --instance-configuration '{
        "Cpu": "1 vCPU",
        "Memory": "2 GB"
    }' \
    --region $AWS_REGION

# Get App Runner URL
aws apprunner describe-service \
    --service-arn <service-arn-from-create> \
    --query "Service.ServiceUrl" \
    --output text \
    --region $AWS_REGION
```

**App Runner Pros:**
- ✅ Much simpler setup
- ✅ Auto-scaling included
- ✅ HTTPS by default
- ✅ Automatic deployments

**App Runner Cost:** ~$25-40/month

---

## 🔧 Update Slack Event Subscription

After deployment:

```bash
# 1. Get your production URL
echo "Production URL: https://$ALB_DNS"

# 2. Go to https://api.slack.com/apps
# 3. Select "Hermes" app
# 4. Go to "Event Subscriptions"
# 5. Update Request URL to:
#    https://your-alb-dns/api/slack/events
#    or
#    https://yourdomain.com/api/slack/events (if using custom domain)
# 6. Wait for ✅ Verified
# 7. Save Changes
```

---

## ✅ Post-Deployment Checklist

- [ ] ECS service running (2+ tasks)
- [ ] Load balancer healthy
- [ ] Health endpoint returns 200: `curl https://$ALB_DNS/health`
- [ ] Redis connection working
- [ ] Secrets Manager configured
- [ ] CloudWatch logs flowing
- [ ] Auto-scaling configured
- [ ] Slack webhook URL updated
- [ ] HTTPS/SSL configured (production)
- [ ] Custom domain configured (optional)
- [ ] Monitoring alarms set up
- [ ] Backup strategy defined

---

## 🐛 Troubleshooting

### Tasks failing to start
```bash
# Check task logs
aws ecs describe-tasks \
    --cluster agencity-production \
    --tasks <task-id> \
    --region $AWS_REGION

# View CloudWatch logs
aws logs tail /ecs/agencity --follow --region $AWS_REGION
```

### Load balancer health checks failing
```bash
# Test health endpoint directly
curl http://$ALB_DNS/health

# Check target group health
aws elbv2 describe-target-health \
    --target-group-arn $TG_ARN \
    --region $AWS_REGION
```

### Cannot connect to Redis
```bash
# Verify security group allows traffic
# ECS tasks must be in same VPC as Redis
# Check Redis endpoint is correct in task definition
```

---

## 📚 Useful Commands Reference

```bash
# View all ECS services
aws ecs list-services --cluster agencity-production --region $AWS_REGION

# Scale service manually
aws ecs update-service \
    --cluster agencity-production \
    --service agencity-service \
    --desired-count 4 \
    --region $AWS_REGION

# Stop all tasks (for maintenance)
aws ecs update-service \
    --cluster agencity-production \
    --service agencity-service \
    --desired-count 0 \
    --region $AWS_REGION

# Update environment variables
# Edit task-definition.json, then:
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs update-service \
    --cluster agencity-production \
    --service agencity-service \
    --task-definition agencity \
    --force-new-deployment

# Delete everything (cleanup)
aws ecs delete-service --cluster agencity-production --service agencity-service --force
aws ecs delete-cluster --cluster agencity-production
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
aws elasticache delete-cache-cluster --cache-cluster-id agencity-redis
```

---

## 🎯 Next Steps

1. **Choose deployment method** (ECS Fargate recommended)
2. **Set up AWS CLI** with credentials
3. **Follow step-by-step guide** above
4. **Test deployment** with health checks
5. **Update Slack webhook** URL
6. **Configure monitoring** and alarms
7. **Set up custom domain** (optional)
8. **Enable HTTPS** for production

---

**Need help?** Check the troubleshooting section or AWS documentation.
