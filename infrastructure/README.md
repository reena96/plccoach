# PLC Coach Infrastructure Setup

This directory contains Terraform infrastructure-as-code for the PLC Coach application.

## Quick Start

### Prerequisites

- AWS CLI installed and configured
- Terraform >= 1.0 installed
- AWS account with appropriate permissions

### Setup Steps

1. **Configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your settings
   ```

2. **Initialize Terraform:**
   ```bash
   terraform init
   ```

3. **Review planned changes:**
   ```bash
   terraform plan
   ```

4. **Deploy infrastructure:**
   ```bash
   terraform apply
   ```

5. **Save outputs:**
   ```bash
   terraform output > ../infrastructure-outputs.txt
   ```

## What Gets Created

- **Networking:** VPC, Subnets, NAT Gateways, Internet Gateway
- **Compute:** ECS Fargate cluster, ECR repository
- **Database:** RDS PostgreSQL 15 (Multi-AZ)
- **Storage:** S3 buckets for content, exports, backups, and frontend
- **CDN:** CloudFront distribution for frontend
- **Load Balancing:** Application Load Balancer with SSL/TLS
- **Security:** KMS keys, Security Groups, IAM roles, Secrets Manager
- **Monitoring:** CloudWatch logs, metrics, alarms, and dashboard

## Deployment Time

⏱️ **Initial deployment takes 15-20 minutes** (primarily RDS instance creation)

## Cost Estimate

💰 **~$325/month for production** (see docs/infrastructure.md for breakdown)

## Important Outputs

After deployment, get critical values:

```bash
# ALB URL for API
terraform output alb_dns_name

# ECR repository for Docker images
terraform output ecr_repository_url

# Database endpoint
terraform output rds_endpoint

# CloudFront URL for frontend
terraform output cloudfront_domain_name
```

## Terraform State Management

### Local State (Default)

State is stored locally in `terraform.tfstate`. **Keep this file secure and backed up.**

### Remote State (Recommended for Teams)

Uncomment the backend configuration in `main.tf` and create an S3 bucket:

```bash
# Create S3 bucket for state
aws s3 mb s3://plccoach-terraform-state

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name plccoach-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Re-initialize Terraform with backend
terraform init -migrate-state
```

## Destroying Infrastructure

⚠️ **WARNING: This will delete all resources and data!**

```bash
terraform destroy
```

## Updating Infrastructure

1. Modify Terraform files
2. Review changes: `terraform plan`
3. Apply changes: `terraform apply`

## Troubleshooting

### Error: "Error creating DB Instance: DBInstanceAlreadyExists"

The RDS instance already exists. Either:
- Import it: `terraform import aws_db_instance.main plccoach-db`
- Destroy and recreate (⚠️ data loss)

### Error: "Error creating S3 bucket: BucketAlreadyOwnedByYou"

The S3 bucket already exists. Import it:
```bash
terraform import aws_s3_bucket.content plccoach-content-<account-id>
```

### Error: "UnauthorizedOperation"

Your AWS credentials don't have sufficient permissions. Required permissions:
- VPC, EC2, RDS, S3, ECS, ECR, IAM, KMS, CloudWatch, Secrets Manager, CloudFront

## Additional Documentation

See [docs/infrastructure.md](../docs/infrastructure.md) for:
- Detailed architecture diagrams
- Security best practices
- Operational procedures
- Cost optimization tips
- Troubleshooting guide
