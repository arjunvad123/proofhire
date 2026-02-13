# AWS Credentials Setup Guide

How to create and configure AWS credentials for deployment.

---

## Step 1: Sign into AWS Console

1. Go to https://console.aws.amazon.com
2. Sign in with your AWS account
   - If you don't have an account, click "Create a new AWS account"
   - You'll need a credit card (but we're using credits)

---

## Step 2: Create IAM User (Recommended)

**Why IAM User?** It's more secure than using root credentials.

### Via AWS Console:

1. **Go to IAM Service**
   - In the AWS Console search bar, type "IAM"
   - Click on "IAM" (Identity and Access Management)

2. **Create New User**
   - Click "Users" in the left sidebar
   - Click "Create user" button
   - Enter username: `agencity-deployer`
   - Click "Next"

3. **Set Permissions**
   - Select "Attach policies directly"
   - Search for and select these policies:
     - ✅ `AmazonEC2FullAccess` (to create/manage EC2 instances)
     - ✅ `IAMReadOnlyAccess` (to check account info)
   - Click "Next"

4. **Review and Create**
   - Review the settings
   - Click "Create user"

5. **Create Access Key**
   - Click on the user you just created (`agencity-deployer`)
   - Go to "Security credentials" tab
   - Scroll down to "Access keys"
   - Click "Create access key"
   - Select "Command Line Interface (CLI)"
   - Check the confirmation box
   - Click "Next"
   - (Optional) Add description: "Agencity deployment"
   - Click "Create access key"

6. **SAVE YOUR CREDENTIALS** ⚠️
   - You'll see:
     - **Access key ID**: Starts with `AKIA...`
     - **Secret access key**: Long random string
   - Click "Download .csv file" (recommended)
   - **IMPORTANT**: You can only see the secret key once!
   - Copy both values somewhere safe

---

## Step 3: Configure AWS CLI

Now configure the CLI with your credentials:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: AKIA................  (paste your access key)
AWS Secret Access Key [None]: ................  (paste your secret key)
Default region name [None]: us-east-1           (or your preferred region)
Default output format [None]: json              (just type 'json')
```

### Available Regions:

Choose the region closest to your users:

**US Regions:**
- `us-east-1` - N. Virginia (most services, cheapest)
- `us-east-2` - Ohio
- `us-west-1` - N. California
- `us-west-2` - Oregon

**Europe:**
- `eu-west-1` - Ireland
- `eu-west-2` - London
- `eu-central-1` - Frankfurt

**Asia:**
- `ap-southeast-1` - Singapore
- `ap-northeast-1` - Tokyo
- `ap-south-1` - Mumbai

**Recommended**: `us-east-1` (cheapest, most services)

---

## Step 4: Verify Configuration

Test that your credentials work:

```bash
# Check your AWS identity
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/agencity-deployer"
# }

# List EC2 regions (confirms permissions)
aws ec2 describe-regions --output table
```

If these commands work, you're ready to deploy! ✅

---

## Alternative: Using Root Credentials (Not Recommended)

If you want to use root credentials (simpler but less secure):

1. Go to AWS Console: https://console.aws.amazon.com
2. Click your account name (top right)
3. Click "Security credentials"
4. Scroll to "Access keys"
5. Click "Create access key"
6. Select "Command Line Interface (CLI)"
7. Download credentials
8. Run `aws configure` with those credentials

**⚠️ Security Note**: Root credentials have full access to everything. IAM users are more secure.

---

## Troubleshooting

### "Unable to locate credentials"
```bash
# Check if credentials file exists
cat ~/.aws/credentials

# If empty or doesn't exist, run:
aws configure
```

### "Access Denied" errors
```bash
# Check your current identity
aws sts get-caller-identity

# Make sure the user has EC2FullAccess policy attached
```

### Credentials file location
- **macOS/Linux**: `~/.aws/credentials`
- **Windows**: `C:\Users\USERNAME\.aws\credentials`

You can manually edit this file:
```ini
[default]
aws_access_key_id = AKIA................
aws_secret_access_key = ................
region = us-east-1
```

---

## Security Best Practices

1. ✅ **Never commit credentials to git**
   - `.aws/credentials` should never be in your repo
   - Add to `.gitignore` if needed

2. ✅ **Use IAM users, not root**
   - Root has unlimited access
   - IAM users can have limited permissions

3. ✅ **Rotate credentials regularly**
   - Delete old access keys
   - Create new ones every 90 days

4. ✅ **Enable MFA** (Multi-Factor Authentication)
   - In IAM console
   - Adds extra security layer

5. ✅ **Never share credentials**
   - Each person should have their own IAM user
   - Easier to track and revoke access

---

## AWS Free Tier

If you're on AWS Free Tier, you get:
- ✅ 750 hours/month of t2.micro or t3.micro (first 12 months)
- ✅ 30 GB storage
- ✅ 15 GB data transfer

**Note**: We'll use `t3.micro` for free tier or `t3.small` for production.

---

## Next Steps

Once credentials are configured:

```bash
# Test credentials
aws sts get-caller-identity

# Run deployment
cd /Users/aidannguyen/Downloads/proofhire/proofhire/agencity
bash scripts/full-deployment.sh
```

---

## Quick Reference

**Create IAM User:**
https://console.aws.amazon.com/iam/home#/users

**Create Access Key:**
IAM → Users → [Your User] → Security Credentials → Create Access Key

**Configure CLI:**
```bash
aws configure
```

**Test Configuration:**
```bash
aws sts get-caller-identity
```

---

**Ready to deploy?** Once you have credentials configured, run:
```bash
bash scripts/full-deployment.sh
```
