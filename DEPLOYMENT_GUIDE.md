# PLC Coach - Deployment Guide

**Quick Start Guide for Deploying Infrastructure**

This guide shows you exactly what commands to run to deploy the PLC Coach infrastructure.

---

## What You'll Need (5 minutes to set up)

1. **AWS Account** - Get one at [aws.amazon.com](https://aws.amazon.com)
2. **AWS CLI** - Install from [here](https://aws.amazon.com/cli/)
3. **Terraform** - Install from [terraform.io](https://www.terraform.io/downloads)

---

## Step-by-Step Deployment

### Step 1: Install Prerequisites

#### macOS:
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install AWS CLI and Terraform
brew install awscli terraform
```

#### Windows:
```powershell
# Install using Chocolatey
choco install awscli terraform
```

#### Linux (Ubuntu/Debian):
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Step 2: Configure AWS Credentials

```bash
aws configure
```

You'll need to enter:
- **AWS Access Key ID**: Get from [AWS IAM Console](https://console.aws.amazon.com/iam/)
- **AWS Secret Access Key**: From the same place
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

**How to get AWS credentials:**
1. Go to AWS Console → IAM → Users
2. Click your username → Security credentials
3. Create access key → CLI → Create access key
4. Copy the Access Key ID and Secret Access Key

### Step 3: Configure Your Settings

```bash
cd plccoach/infrastructure
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` (optional - defaults work fine):
```hcl
aws_region  = "us-east-1"
environment = "production"
project_name = "plccoach"

# For development/testing, use smaller resources:
# db_instance_class = "db.t3.small"
# enable_multi_az = false
```

### Step 4: Deploy Infrastructure (Automated)

**Option A: Use the automated script (Recommended)**

```bash
cd plccoach
./scripts/deploy-infrastructure.sh
```

This script will:
- ✅ Check all prerequisites
- ✅ Initialize Terraform
- ✅ Show you what will be created
- ✅ Deploy everything (takes 15-20 minutes)
- ✅ Save all important values for you

**Option B: Manual deployment**

```bash
cd plccoach/infrastructure

# Initialize
terraform init

# Preview what will be created
terraform plan

# Deploy (type 'yes' when prompted)
terraform apply

# Save outputs
terraform output > ../infrastructure-outputs.txt
```

### Step 5: Subscribe to Alerts

After deployment completes, run this command (replace with your email):

```bash
aws sns subscribe \
  --topic-arn $(cd infrastructure && terraform output -raw sns_alarms_topic_arn) \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Check your email and click the confirmation link.

### Step 6: Set Up GitHub Actions (for CI/CD)

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:

```
Name: AWS_ROLE_TO_ASSUME
Value: <get from infrastructure-outputs.txt>

Name: API_URL
Value: <get alb_dns_name from infrastructure-outputs.txt>
```

**That's it! Your infrastructure is deployed.**

---

## What Was Created

Your infrastructure now includes:

- ☁️ **VPC** with public and private subnets across 2 availability zones
- 🖥️ **ECS Fargate cluster** for running containers
- 🗄️ **PostgreSQL database** (Multi-AZ, encrypted)
- 📦 **S3 buckets** for content, exports, backups, and frontend
- 🚀 **CloudFront CDN** for fast frontend delivery
- ⚖️ **Application Load Balancer** with SSL/TLS
- 🔒 **Security groups, KMS encryption, IAM roles**
- 📊 **CloudWatch monitoring and alarms**

---

## Accessing Your Application

After deployment, you'll have these URLs:

```bash
# Get your URLs
cd infrastructure

# API URL (backend)
terraform output alb_dns_name
# Example: plccoach-alb-123456789.us-east-1.elb.amazonaws.com

# Frontend URL (will work after you deploy frontend code)
terraform output cloudfront_domain_name
# Example: d1234567890.cloudfront.net
```

---

## Next Steps

### 1. Deploy Backend Code

Your backend code will go in `api-service/` directory. Once you push to the `main` branch, GitHub Actions will:
- Build a Docker image
- Push to ECR (Elastic Container Registry)
- Deploy to ECS Fargate

### 2. Deploy Frontend Code

Your frontend code will go in `frontend/` directory. Once you push to the `main` branch, GitHub Actions will:
- Build the React app
- Upload to S3
- Invalidate CloudFront cache

### 3. (Optional) Set Up Custom Domain

If you want `https://plccoach.example.com` instead of AWS URLs:

1. **Request SSL certificate in AWS Certificate Manager:**
   ```bash
   aws acm request-certificate \
     --domain-name plccoach.example.com \
     --validation-method DNS
   ```

2. **Add DNS validation records** (AWS Console will show these)

3. **Update terraform.tfvars:**
   ```hcl
   domain_name = "plccoach.example.com"
   ```

4. **Apply changes:**
   ```bash
   cd infrastructure
   terraform apply
   ```

5. **Update your DNS** to point to:
   - ALB DNS name (for API)
   - CloudFront distribution (for frontend)

---

## Cost Breakdown

### Production Environment (~$325/month):

| What | Configuration | Monthly Cost |
|------|---------------|--------------|
| Servers (ECS) | 2 tasks running 24/7 | $30 |
| Database (RDS) | PostgreSQL, Multi-AZ | $150 |
| Storage (S3) | 100 GB | $10 |
| Internet (NAT) | 2 NAT Gateways | $70 |
| Load Balancer | Standard ALB | $25 |
| CDN (CloudFront) | 100 GB transfer | $10 |
| Data Transfer | Between services | $20 |
| Monitoring | CloudWatch | $10 |
| **Total** | | **$325** |

### Development Environment (~$100/month):

To reduce costs for dev/staging:

```hcl
# In terraform.tfvars:
db_instance_class = "db.t3.small"  # Instead of t3.medium
enable_multi_az = false            # Single AZ is fine for dev
ecs_task_cpu = 256                 # Half the CPU
```

This saves ~$200/month but is not suitable for production.

---

## Managing Your Infrastructure

### View Resource Status

```bash
cd infrastructure
terraform show
```

### Update Infrastructure

1. Edit `.tf` files
2. Preview changes: `terraform plan`
3. Apply changes: `terraform apply`

### View Logs

```bash
# API logs
aws logs tail /ecs/plccoach/api --follow

# See recent logs from last hour
aws logs tail /ecs/plccoach/api --since 1h
```

### Scale Your Application

```bash
# Increase to 3 containers
aws ecs update-service \
  --cluster plccoach-cluster \
  --service plccoach-api-service \
  --desired-count 3
```

### Backup Database Manually

```bash
aws rds create-db-snapshot \
  --db-instance-identifier plccoach-db \
  --db-snapshot-identifier plccoach-backup-$(date +%Y%m%d)
```

---

## Troubleshooting

### ❌ "Error: error configuring Terraform AWS Provider"

**Problem:** AWS credentials not set up correctly.

**Solution:**
```bash
aws configure
# Re-enter your credentials
```

### ❌ "Error creating DB Instance: DBInstanceAlreadyExists"

**Problem:** The database already exists from a previous deployment.

**Solution:**
```bash
cd infrastructure
terraform import aws_db_instance.main plccoach-db
terraform apply
```

### ❌ Deployment is taking forever

**Normal:** RDS database creation takes 15-20 minutes. This is normal.

**If stuck longer:** Check AWS Console → RDS to see if there are errors.

### ❌ "Error: UnauthorizedOperation"

**Problem:** Your AWS user doesn't have enough permissions.

**Solution:** Your AWS user needs these permissions:
- VPC, EC2, RDS, S3, ECS, ECR, IAM
- KMS, CloudWatch, Secrets Manager, CloudFront

Ask your AWS administrator to grant these permissions.

---

## Destroying Infrastructure (⚠️ Deletes Everything!)

If you need to tear down everything:

```bash
cd infrastructure
terraform destroy
# Type 'yes' when prompted
```

**WARNING:** This will:
- Delete all resources
- Delete all data in the database
- Delete all files in S3 buckets
- This cannot be undone!

---

## Getting Help

### Check Status
```bash
cd infrastructure
terraform show
```

### View Outputs Again
```bash
cd infrastructure
terraform output
```

### AWS Console
- [ECS Console](https://console.aws.amazon.com/ecs/) - View running containers
- [RDS Console](https://console.aws.amazon.com/rds/) - View database status
- [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/) - View logs and metrics

### Documentation
- Full documentation: `docs/infrastructure.md`
- Terraform files: `infrastructure/` directory
- GitHub workflows: `.github/workflows/` directory

---

## Summary: What You Need to Do

**One-time setup (30 minutes):**
1. ✅ Install AWS CLI and Terraform
2. ✅ Configure AWS credentials
3. ✅ Run `./scripts/deploy-infrastructure.sh`
4. ✅ Subscribe to email alerts
5. ✅ Add GitHub secrets

**Done!** Your infrastructure is now running and ready for your application code.

The GitHub Actions workflows will automatically deploy your code when you push to the `main` branch.
