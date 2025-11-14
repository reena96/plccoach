# PLC Coach Infrastructure Documentation

**Project:** AI Powered PLC at Work Virtual Coach
**Last Updated:** 2025-11-12
**Infrastructure:** AWS
**IaC Tool:** Terraform

---

## Overview

The PLC Coach application is deployed on AWS using a modern, scalable, and secure architecture. All infrastructure is defined as code using Terraform, enabling reproducible deployments and version-controlled infrastructure changes.

## Architecture Diagram

```
Internet
    |
    v
┌─────────────────────────────────────────────────────────────┐
│                      CloudFront CDN                          │
│                    (Frontend Assets)                         │
└─────────────────────────────────────────────────────────────┘
                             |
                             v
┌─────────────────────────────────────────────────────────────┐
│                 Application Load Balancer                    │
│                     (SSL/TLS Termination)                    │
└─────────────────────────────────────────────────────────────┘
                             |
        ┌────────────────────┴────────────────────┐
        v                                         v
┌──────────────┐                          ┌──────────────┐
│  Public      │                          │  Public      │
│  Subnet 1    │                          │  Subnet 2    │
│  (AZ-1)      │                          │  (AZ-2)      │
└──────────────┘                          └──────────────┘
        |                                         |
        v                                         v
┌──────────────┐                          ┌──────────────┐
│ NAT Gateway  │                          │ NAT Gateway  │
└──────────────┘                          └──────────────┘
        |                                         |
        v                                         v
┌──────────────┐                          ┌──────────────┐
│  Private     │                          │  Private     │
│  Subnet 1    │                          │  Subnet 2    │
│  (AZ-1)      │                          │  (AZ-2)      │
└──────────────┘                          └──────────────┘
        |                                         |
        v                                         v
┌──────────────┐                          ┌──────────────┐
│ ECS Fargate  │                          │ ECS Fargate  │
│   Tasks      │                          │   Tasks      │
└──────────────┘                          └──────────────┘
        |                                         |
        └────────────────┬────────────────────────┘
                         v
              ┌────────────────────┐
              │  RDS PostgreSQL 15 │
              │    (Multi-AZ)      │
              └────────────────────┘
```

## Infrastructure Components

### 1. Network Infrastructure

#### VPC Configuration
- **CIDR Block:** 10.0.0.0/16
- **DNS Hostnames:** Enabled
- **DNS Support:** Enabled

#### Subnets
- **Public Subnets:** 2 subnets across 2 Availability Zones
  - Used for: ALB, NAT Gateways
  - CIDR: 10.0.0.0/24, 10.0.1.0/24
- **Private Subnets:** 2 subnets across 2 Availability Zones
  - Used for: ECS Tasks, RDS
  - CIDR: 10.0.10.0/24, 10.0.11.0/24

#### Internet Connectivity
- **Internet Gateway:** Provides internet access to public subnets
- **NAT Gateways:** 2 NAT Gateways (one per AZ) for high availability
  - Private subnets route internet traffic through NAT Gateways

### 2. Compute Infrastructure

#### ECS Fargate Cluster
- **Cluster Name:** plccoach-cluster
- **Container Insights:** Enabled for monitoring
- **Capacity Providers:** FARGATE and FARGATE_SPOT

#### Task Configuration
- **CPU:** 512 units (0.5 vCPU)
- **Memory:** 1024 MB (1 GB)
- **Platform Version:** LATEST

### 3. Database Infrastructure

#### RDS PostgreSQL
- **Engine:** PostgreSQL 15.4
- **Instance Class:** db.t3.medium (production)
- **Storage:** 100 GB (GP3 SSD)
- **Max Storage:** 1000 GB (auto-scaling enabled)
- **Multi-AZ:** Enabled for high availability
- **Encryption:** KMS encryption at rest
- **Backup Retention:** 30 days
- **Backup Window:** 03:00-04:00 UTC
- **Maintenance Window:** Monday 04:00-05:00 UTC

#### Extensions
- **pgvector:** Enabled for vector embeddings
- **pg_stat_statements:** Enabled for query performance monitoring

### 4. Storage Infrastructure

#### S3 Buckets

**Content Bucket** (`plccoach-content-{account-id}`)
- Purpose: Store content and knowledge base files
- Encryption: KMS (SSE-KMS)
- Versioning: Enabled
- Public Access: Blocked

**Exports Bucket** (`plccoach-exports-{account-id}`)
- Purpose: User-generated exports and downloads
- Encryption: KMS (SSE-KMS)
- Versioning: Enabled
- Lifecycle: Expire after 30 days
- Public Access: Blocked

**Backups Bucket** (`plccoach-backups-{account-id}`)
- Purpose: Database backups and snapshots
- Encryption: KMS (SSE-KMS)
- Versioning: Enabled
- Lifecycle: Transition to Glacier after 90 days, expire after 365 days
- Public Access: Blocked

**Frontend Bucket** (`plccoach-frontend-{account-id}`)
- Purpose: Static frontend assets served via CloudFront
- Encryption: AES256 (SSE-S3)
- Versioning: Enabled
- Access: CloudFront Origin Access Identity only

### 5. Content Delivery

#### CloudFront Distribution
- **Origin:** S3 Frontend Bucket
- **Price Class:** PriceClass_100 (US, Canada, Europe)
- **IPv6:** Enabled
- **HTTPS:** Required (redirect HTTP to HTTPS)
- **Caching:**
  - Default: 1 hour (3600 seconds)
  - Static assets: 1 year (31536000 seconds)
- **Compression:** Enabled
- **Custom Error Pages:** SPA routing support (404 → index.html)

### 6. Load Balancing

#### Application Load Balancer
- **Type:** Application Load Balancer
- **Scheme:** Internet-facing
- **HTTP/2:** Enabled
- **Cross-Zone Load Balancing:** Enabled
- **Deletion Protection:** Enabled

#### Listeners
- **HTTPS (443):** Primary listener with SSL/TLS termination
- **HTTP (80):** Redirects to HTTPS (301)

#### Target Groups
- **Primary:** For active deployment
- **Alternate:** For blue-green deployments
- **Health Check:** `/health` endpoint
  - Healthy threshold: 2
  - Unhealthy threshold: 3
  - Interval: 30 seconds
  - Timeout: 5 seconds

### 7. Security

#### Security Groups

**ALB Security Group**
- Inbound: HTTPS (443) and HTTP (80) from 0.0.0.0/0
- Outbound: All traffic

**ECS Tasks Security Group**
- Inbound: Port 8000 from ALB Security Group
- Outbound: All traffic

**RDS Security Group**
- Inbound: PostgreSQL (5432) from ECS Tasks Security Group
- Outbound: All traffic

#### KMS Encryption
- **RDS KMS Key:** For database encryption at rest
- **S3 KMS Key:** For S3 bucket encryption
- **Secrets KMS Key:** For Secrets Manager encryption
- **Key Rotation:** Enabled (automatic annual rotation)

#### IAM Roles

**ECS Task Execution Role**
- Permissions: Pull ECR images, write CloudWatch logs, read Secrets Manager

**ECS Task Role**
- Permissions: Access S3 buckets (content, exports), interact with AWS services

### 8. Monitoring & Logging

#### CloudWatch Log Groups
- **API Logs:** `/ecs/plccoach/api`
- **Application Logs:** `/application/plccoach`
- **Retention:** 90 days

#### CloudWatch Alarms
1. **High Error Rate:** >10 5XX errors in 5 minutes
2. **High Response Time:** p95 >10 seconds
3. **RDS High CPU:** >80% for 5 minutes
4. **RDS Low Storage:** <10 GB free space
5. **ECS High CPU:** >80% for 5 minutes
6. **ECS High Memory:** >80% for 5 minutes

#### Notifications
- **SNS Topic:** `plccoach-alarms`
- Alerts sent for all alarm triggers

#### CloudWatch Dashboard
- Request count and error rates
- API response times (p50, p95, p99)
- Database metrics (CPU, connections, storage)
- ECS metrics (CPU, memory utilization)

### 9. Container Registry

#### ECR Repository
- **Repository:** plccoach/api
- **Image Scanning:** Enabled on push
- **Encryption:** KMS
- **Lifecycle Policy:**
  - Keep last 10 tagged images
  - Expire untagged images after 7 days

### 10. Secrets Management

#### AWS Secrets Manager
- **Database Credentials:** Auto-generated 32-character password
- **Format:** JSON with username, password, host, port, dbname
- **Encryption:** KMS encryption
- **Rotation:** Manual (can be automated)

---

## Deployment Guide

### Prerequisites

1. **AWS Account:** Active AWS account with appropriate permissions
2. **AWS CLI:** Installed and configured ([Installation Guide](https://aws.amazon.com/cli/))
3. **Terraform:** Version 1.0+ installed ([Installation Guide](https://www.terraform.io/downloads))
4. **GitHub Repository:** For CI/CD integration
5. **Domain (Optional):** For custom domain and SSL certificate

### Initial Setup

#### 1. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your default output format (json)
```

#### 2. Clone Repository

```bash
git clone <repository-url>
cd plccoach
```

#### 3. Configure Terraform Variables

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your settings:
```hcl
aws_region  = "us-east-1"
environment = "production"
project_name = "plccoach"
# ... other settings
```

#### 4. Initialize Terraform

```bash
terraform init
```

#### 5. Review Infrastructure Plan

```bash
terraform plan
```

Review the output to ensure all resources will be created as expected.

#### 6. Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. **This will take 15-20 minutes** due to RDS creation.

#### 7. Save Terraform Outputs

```bash
terraform output > ../outputs.txt
```

Keep this file secure as it contains sensitive information.

### Post-Deployment Configuration

#### 1. Configure GitHub Secrets

Add these secrets to your GitHub repository:

```
AWS_ROLE_TO_ASSUME: <arn-from-terraform-outputs>
API_URL: <alb-dns-name-from-outputs>
```

#### 2. Subscribe to SNS Alarms

```bash
aws sns subscribe \
  --topic-arn $(terraform output -raw sns_alarms_topic_arn) \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Confirm the subscription via email.

#### 3. (Optional) Configure Custom Domain

If using a custom domain:

1. Create ACM certificate in AWS Console
2. Add DNS validation records
3. Update `domain_name` in `terraform.tfvars`
4. Run `terraform apply` again
5. Update DNS with ALB and CloudFront records

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### API Deployment (`.github/workflows/deploy-api.yml`)

**Triggers:**
- Push to `main` branch (changes in `api-service/`)
- Manual workflow dispatch

**Steps:**
1. Run tests (pytest, coverage)
2. Run linting (flake8)
3. Build Docker image
4. Push to ECR
5. Update ECS task definition
6. Deploy to ECS with blue-green strategy
7. Run smoke tests
8. Notify deployment status

#### Frontend Deployment (`.github/workflows/deploy-frontend.yml`)

**Triggers:**
- Push to `main` branch (changes in `frontend/`)
- Manual workflow dispatch

**Steps:**
1. Run tests (Jest)
2. Run linting (ESLint)
3. Build React application (Vite)
4. Sync to S3
5. Invalidate CloudFront cache
6. Verify deployment
7. Notify deployment status

### Deployment Strategy

**Blue-Green Deployment:**
1. New version deployed to alternate target group
2. Health checks verify new version
3. Traffic gradually shifted to new version
4. Old version remains available for rollback
5. After stability, old version decommissioned

---

## Operational Procedures

### Accessing the Database

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw rds_endpoint)

# Get database password from Secrets Manager
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id plccoach-db-password \
  --query SecretString \
  --output text | jq -r '.password')

# Connect via psql (requires SSH tunnel to private subnet or VPN)
psql -h $DB_ENDPOINT -U plccoach_admin -d plccoach
```

### Viewing Logs

```bash
# API logs
aws logs tail /ecs/plccoach/api --follow

# Application logs
aws logs tail /application/plccoach --follow
```

### Scaling ECS Service

```bash
aws ecs update-service \
  --cluster plccoach-cluster \
  --service plccoach-api-service \
  --desired-count 3
```

### Manual Deployment

```bash
# API service
cd .github/workflows
gh workflow run deploy-api.yml

# Frontend
gh workflow run deploy-frontend.yml
```

### Rollback Procedure

#### ECS Service Rollback
```bash
# List recent task definitions
aws ecs list-task-definitions --family-prefix plccoach

# Update service to previous task definition
aws ecs update-service \
  --cluster plccoach-cluster \
  --service plccoach-api-service \
  --task-definition plccoach-api-service:PREVIOUS_REVISION
```

#### Frontend Rollback
```bash
# Re-run previous successful GitHub Actions workflow
gh run rerun <run-id>
```

### Database Backup & Restore

#### Manual Backup
```bash
aws rds create-db-snapshot \
  --db-instance-identifier plccoach-db \
  --db-snapshot-identifier plccoach-manual-$(date +%Y%m%d-%H%M%S)
```

#### Restore from Snapshot
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier plccoach-db-restored \
  --db-snapshot-identifier <snapshot-id>
```

---

## Security Best Practices

1. **Network Isolation:**
   - Application and database in private subnets
   - No direct internet access to sensitive resources

2. **Encryption:**
   - Data at rest: KMS encryption for RDS and S3
   - Data in transit: SSL/TLS for all connections

3. **Least Privilege:**
   - IAM roles with minimum required permissions
   - Security groups with specific port/source restrictions

4. **Secrets Management:**
   - No secrets in code or environment variables
   - All secrets in AWS Secrets Manager with KMS encryption

5. **Monitoring:**
   - CloudWatch alarms for security events
   - VPC Flow Logs (can be enabled)
   - Access logging for S3 and ALB

---

## Cost Optimization

### Production Environment (Estimated Monthly Costs)

| Service | Configuration | Est. Monthly Cost |
|---------|--------------|-------------------|
| ECS Fargate | 2 tasks (0.5 vCPU, 1 GB RAM, 24/7) | ~$30 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ, 100 GB | ~$150 |
| S3 | 100 GB storage, moderate requests | ~$10 |
| NAT Gateways | 2 NAT Gateways | ~$70 |
| ALB | Standard ALB | ~$25 |
| CloudFront | 100 GB transfer | ~$10 |
| Data Transfer | Inter-AZ and outbound | ~$20 |
| CloudWatch | Logs and metrics | ~$10 |
| **Total** | | **~$325/month** |

### Cost Savings Tips

**Development/Staging:**
- Use single NAT Gateway
- RDS: db.t3.small, Single-AZ
- Reduced ECS task count
- Lower log retention (30 days)
- **Estimated savings: 60-70%**

**Production Optimizations:**
- Use Reserved Instances for RDS (save 40-60%)
- Use Savings Plans for ECS Fargate (save 20%)
- S3 Intelligent-Tiering for infrequently accessed data
- CloudFront cost optimization by region selection

---

## Troubleshooting

### Common Issues

#### 1. ECS Tasks Failing to Start

**Symptoms:** Tasks immediately stop after starting

**Diagnosis:**
```bash
aws ecs describe-tasks \
  --cluster plccoach-cluster \
  --tasks <task-arn>
```

**Common Causes:**
- Missing environment variables
- Incorrect security group configuration
- Secrets Manager access denied
- Container image issues

**Resolution:**
- Check CloudWatch logs
- Verify IAM permissions
- Test container locally

#### 2. Database Connection Failures

**Symptoms:** API logs show database connection errors

**Diagnosis:**
- Check security group rules
- Verify database is running
- Test connectivity from ECS task

**Resolution:**
```bash
# Verify RDS status
aws rds describe-db-instances --db-instance-identifier plccoach-db

# Check security group rules
aws ec2 describe-security-groups --group-ids <sg-id>
```

#### 3. High Response Times

**Symptoms:** CloudWatch alarms for high response time

**Diagnosis:**
- Check RDS CPU and connections
- Review slow query logs
- Monitor ECS CPU/memory

**Resolution:**
- Scale ECS tasks
- Optimize database queries
- Add database indexes
- Increase RDS instance size

---

## Maintenance Windows

### Recommended Maintenance Schedule

- **Database Maintenance:** Monday 04:00-05:00 UTC
- **Database Backups:** Daily 03:00-04:00 UTC
- **Security Patches:** Apply during maintenance window
- **Infrastructure Updates:** Review and apply monthly

### Update Procedure

1. Review Terraform changes in staging
2. Schedule maintenance window
3. Notify users of planned downtime (if any)
4. Apply changes with `terraform apply`
5. Monitor CloudWatch metrics
6. Verify application functionality
7. Document changes

---

## Disaster Recovery

### RTO and RPO

- **Recovery Time Objective (RTO):** 1 hour
- **Recovery Point Objective (RPO):** 5 minutes (continuous backups)

### Backup Strategy

- **Automated RDS Snapshots:** Daily (30-day retention)
- **Manual Snapshots:** Before major changes
- **Point-in-Time Recovery:** Enabled (5-minute granularity)
- **S3 Versioning:** Enabled on all buckets

### Recovery Procedures

**Complete Region Failure:**
1. Create new infrastructure in alternate region
2. Restore database from snapshot
3. Update Route53 DNS records
4. Deploy application containers
5. Verify functionality

**Data Corruption:**
1. Identify corruption time
2. Stop application
3. Restore from point-in-time backup
4. Apply missing transactions if possible
5. Resume application

---

## Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/intro.html)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## Support Contacts

- **AWS Support:** Via AWS Console
- **Infrastructure Issues:** DevOps team
- **Application Issues:** Development team
