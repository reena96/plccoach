# PLC Coach - Deployment Runbook

**Last Updated**: 2025-11-14
**Environment**: Production
**AWS Account**: 971422717446
**Region**: us-east-1

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Prerequisites](#prerequisites)
3. [Deployment Procedures](#deployment-procedures)
4. [Rollback Procedures](#rollback-procedures)
5. [Troubleshooting](#troubleshooting)
6. [Environment Variables](#environment-variables)
7. [Monitoring](#monitoring)

---

## Quick Reference

### Production URLs

- **Backend API**: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com`
- **Frontend**: `https://d3394we8ve9ne3.cloudfront.net`
- **Health Check**: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/health`
- **Database Ready**: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/ready`

### AWS Resources

- **ECS Cluster**: `plccoach-cluster`
- **ECS Service**: `plccoach-api-service`
- **ECR Repository**: `971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api`
- **RDS Endpoint**: `plccoach-db.crws0amqe1e3.us-east-1.rds.amazonaws.com:5432`
- **S3 Frontend Bucket**: `plccoach-frontend-971422717446`
- **CloudFront Distribution ID**: `E7TVM4BHHDN7X`

### Quick Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster plccoach-cluster --services plccoach-api-service --region us-east-1

# View recent logs
aws logs tail /ecs/plccoach/api --follow --region us-east-1

# Run smoke tests
./scripts/smoke-tests.sh

# Check CloudWatch alarms
aws cloudwatch describe-alarms --state-value ALARM --region us-east-1
```

---

## Prerequisites

### Required Tools

- AWS CLI v2 (`aws --version`)
- Docker (`docker --version`)
- Terraform (`terraform --version`)
- Node.js 18+ (`node --version`)
- jq (`jq --version`)

### Required Credentials

- AWS credentials with permissions for:
  - ECS (deploy services)
  - ECR (push images)
  - Secrets Manager (read secrets)
  - S3 (upload frontend)
  - CloudFront (invalidate cache)

### Required Secrets (in AWS Secrets Manager)

- `plccoach-db-password` - Database credentials
- `plccoach/production/google-oauth` - Google OAuth credentials
- `plccoach/production/clever-sso` - Clever SSO credentials
- `plccoach/production/session` - Session encryption key

---

## Deployment Procedures

### Option 1: Manual Deployment (Recommended for First Time)

#### Step 1: Setup Secrets

```bash
# Run the secrets setup script
./scripts/setup-secrets.sh

# This will prompt you for:
# - Google OAuth credentials
# - Clever SSO credentials
# - Session secret (or auto-generate)
```

#### Step 2: Build and Push Docker Image

```bash
cd api-service

# Build the image
docker build -t 971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  971422717446.dkr.ecr.us-east-1.amazonaws.com

# Push the image
docker push 971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api:latest

cd ..
```

#### Step 3: Deploy ECS Service

```bash
# Run the deployment script
./scripts/deploy-ecs-service.sh

# This will:
# - Create ECS task definition
# - Create/update ECS service
# - Wait for service to stabilize
# - Display service status
```

Expected output:
```
🎉 Deployment Complete!
📊 Service Status:
---------------------------------------------------------------------------
|                          DescribeServices                               |
+--------+----------+---------+---------+--------+
| Desired| Name     | Pending | Running | Status |
+--------+----------+---------+---------+--------+
|  2     | plccoach |  0      |  2      | ACTIVE |
+--------+----------+---------+---------+--------+
```

#### Step 4: Run Smoke Tests

```bash
# Validate deployment
./scripts/smoke-tests.sh
```

Expected output:
```
Testing: Health endpoint... ✅ PASSED (HTTP 200)
Testing: Ready endpoint... ✅ PASSED (HTTP 200)
Testing: Google OAuth... ✅ PASSED (HTTP 302)
Testing: Clever SSO... ✅ PASSED (HTTP 302)
Testing: Frontend... ✅ PASSED (HTTP 200)
```

#### Step 5: Deploy Frontend

```bash
# Build and deploy frontend
./scripts/deploy-frontend.sh

# This will:
# - Install npm dependencies
# - Build frontend with production API URL
# - Upload to S3
# - Invalidate CloudFront cache
```

#### Step 6: Configure OAuth Redirect URLs

**Google OAuth**:
1. Go to https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Add: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/google/callback`
4. Save

**Clever SSO**:
1. Go to https://apps.clever.com/
2. Select your application
3. Add: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/clever/callback`
4. Save

#### Step 7: Subscribe to Alerts

```bash
# Subscribe email to receive CloudWatch alarms
./scripts/setup-sns-alerts.sh your-email@example.com

# Check your email and confirm the subscription
```

#### Step 8: Final Validation

```bash
# Access the application
open https://d3394we8ve9ne3.cloudfront.net

# Test login flows
# - Click "Sign in with Google"
# - Click "Sign in with Clever"
# - Verify you can log in successfully
```

---

### Option 2: Automated Deployment via GitHub Actions

#### Prerequisites

1. GitHub secrets configured (see `./scripts/setup-github-secrets.sh`)
2. Secrets Manager configured with OAuth credentials
3. Code merged to `main` branch

#### Deployment Process

GitHub Actions automatically runs on push to `main`:

1. **Test**: Runs all pytest tests
2. **Build**: Builds Docker image, pushes to ECR
3. **Migrate**: Runs Alembic database migrations
4. **Deploy**: Updates ECS service with new image
5. **Smoke Tests**: Validates deployment health
6. **Frontend**: Deploys frontend to S3/CloudFront

#### Monitoring GitHub Actions

View workflow runs:
```bash
# Using GitHub CLI
gh run list --repo reena96/plccoach

# Watch latest run
gh run watch
```

Or visit: https://github.com/reena96/plccoach/actions

---

## Rollback Procedures

### Scenario 1: Bad Deployment (Service Running but Broken)

#### Quick Rollback via ECS

```bash
# 1. List task definitions
aws ecs list-task-definitions --family-prefix plccoach-api-task --region us-east-1

# 2. Update service to previous task definition
aws ecs update-service \
  --cluster plccoach-cluster \
  --service plccoach-api-service \
  --task-definition plccoach-api-task:PREVIOUS_REVISION \
  --region us-east-1

# 3. Wait for rollback to complete
aws ecs wait services-stable \
  --cluster plccoach-cluster \
  --services plccoach-api-service \
  --region us-east-1

# 4. Verify health
curl http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/health
```

### Scenario 2: Database Migration Failed

#### Rollback Database

```bash
cd api-service

# Check current migration version
alembic current

# Rollback one migration
alembic downgrade -1

# Or rollback to specific version
alembic downgrade <revision_id>
```

#### Re-deploy Previous Code

```bash
# Revert git commit
git revert HEAD
git push origin main

# GitHub Actions will automatically deploy the reverted code
```

### Scenario 3: Frontend Issues

#### Rollback Frontend

```bash
# 1. Get previous S3 version
aws s3api list-object-versions \
  --bucket plccoach-frontend-971422717446 \
  --prefix index.html \
  --region us-east-1

# 2. Restore previous version
aws s3api copy-object \
  --bucket plccoach-frontend-971422717446 \
  --copy-source plccoach-frontend-971422717446/index.html?versionId=PREVIOUS_VERSION_ID \
  --key index.html \
  --region us-east-1

# 3. Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id E7TVM4BHHDN7X \
  --paths "/*"
```

---

## Troubleshooting

### ECS Service Not Starting

**Symptoms**: Tasks start then immediately stop

**Diagnosis**:
```bash
# Check service events
aws ecs describe-services \
  --cluster plccoach-cluster \
  --services plccoach-api-service \
  --region us-east-1 \
  --query 'services[0].events[:10]'

# Check task logs
aws logs tail /ecs/plccoach/api --follow --region us-east-1
```

**Common Causes**:
1. **Health check failing** - Check `/api/health` endpoint
2. **Database connection failed** - Verify RDS is running, security groups allow access
3. **Secrets not accessible** - Verify Secrets Manager permissions
4. **Image pull failed** - Verify ECR image exists

### Database Connection Errors

**Symptoms**: "could not connect to server" or "connection timeout"

**Diagnosis**:
```bash
# Test database connectivity from local machine
psql -h plccoach-db.crws0amqe1e3.us-east-1.rds.amazonaws.com -U plccoach_admin -d plccoach

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier plccoach-db \
  --region us-east-1 \
  --query 'DBInstances[0].DBInstanceStatus'

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-04dd0c32191ab8ef3 \
  --region us-east-1
```

**Solutions**:
1. Verify ECS security group has access to RDS security group
2. Check RDS is in "available" state
3. Verify DATABASE_URL secret is correct

### OAuth Redirect Errors

**Symptoms**: "redirect_uri_mismatch" or "invalid_request"

**Diagnosis**:
```bash
# Check current OAuth configuration
curl -I http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/google/login
```

**Solutions**:
1. Verify redirect URI in Google/Clever console matches exactly:
   - `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/google/callback`
2. Check OAUTH_REDIRECT_BASE_URL environment variable in task definition
3. Verify secrets are loaded correctly from Secrets Manager

### High Response Times

**Symptoms**: API responses taking >1 second

**Diagnosis**:
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/plccoach-alb/... \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-01T23:59:59Z \
  --period 300 \
  --statistics Average \
  --region us-east-1

# Check database connection pool
# View logs for "connection pool exhausted" messages
aws logs filter-pattern "connection pool" \
  --log-group-name /ecs/plccoach/api \
  --region us-east-1
```

**Solutions**:
1. Increase ECS task count for more capacity
2. Optimize database queries
3. Add database connection pooling
4. Enable caching

---

## Environment Variables

### ECS Task Definition Environment Variables

| Variable | Source | Example Value | Purpose |
|----------|--------|---------------|---------|
| `ENVIRONMENT` | Task Definition | `production` | Application environment |
| `LOG_LEVEL` | Task Definition | `INFO` | Logging verbosity |
| `OAUTH_REDIRECT_BASE_URL` | Task Definition | `http://plccoach-alb...` | Base URL for OAuth callbacks |
| `DATABASE_URL` | Secrets Manager | `postgresql://...` | Database connection string |
| `GOOGLE_CLIENT_ID` | Secrets Manager | `xxx.apps.googleusercontent.com` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Secrets Manager | `GOCSPX-...` | Google OAuth client secret |
| `CLEVER_CLIENT_ID` | Secrets Manager | `xxx` | Clever SSO client ID |
| `CLEVER_CLIENT_SECRET` | Secrets Manager | `xxx` | Clever SSO client secret |
| `SESSION_SECRET_KEY` | Secrets Manager | `xxx` | Session encryption key |

### Frontend Build Environment Variables

| Variable | Set During | Example Value | Purpose |
|----------|------------|---------------|---------|
| `VITE_API_URL` | Build time | `http://plccoach-alb...` | Backend API endpoint |

---

## Monitoring

### CloudWatch Dashboards

**Dashboard Name**: `PLC-Coach-Production`

**URL**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=PLC-Coach-Production

**Metrics**:
- API request count (per minute)
- API error rate (4xx + 5xx percentage)
- API response time (p50, p95, p99)
- Database connections
- ECS task count and CPU/memory usage

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| API-Error-Rate-High | >5% for 5 minutes | SNS notification |
| API-Response-Time-High | p95 >10s for 5 minutes | SNS notification |
| Database-Connections-High | >80% pool utilization | SNS notification |
| ECS-Unhealthy-Tasks | >0 unhealthy tasks for 2 minutes | SNS notification |

### Viewing Logs

```bash
# Tail live logs
aws logs tail /ecs/plccoach/api --follow --region us-east-1

# Search for errors in last hour
aws logs filter-pattern "ERROR" \
  --log-group-name /ecs/plccoach/api \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region us-east-1

# View specific time range
aws logs tail /ecs/plccoach/api \
  --since 1h \
  --format short \
  --region us-east-1
```

### Health Checks

```bash
# API health
curl http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "service": "PLC Coach API",
#   "version": "0.1.0",
#   "database": "connected"
# }

# Database connectivity
curl http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/ready

# Expected: HTTP 200 if database is reachable
```

---

## Contacts

### On-Call Rotation
- **Primary**: [Your Name] - [your-email@example.com]
- **Secondary**: [Backup Name] - [backup-email@example.com]

### Escalation
- **Engineering Lead**: [Lead Name] - [lead-email@example.com]
- **DevOps Team**: [devops@example.com]

### External Vendors
- **Google OAuth Support**: https://support.google.com/cloud
- **Clever Support**: https://support.clever.com
- **AWS Support**: https://console.aws.amazon.com/support

---

## Appendix

### Useful AWS Console Links

- **ECS Cluster**: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/plccoach-cluster
- **ECR Repository**: https://console.aws.amazon.com/ecr/repositories/plccoach/api?region=us-east-1
- **RDS Database**: https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=plccoach-db
- **S3 Buckets**: https://s3.console.aws.amazon.com/s3/buckets?region=us-east-1
- **CloudFront**: https://console.aws.amazon.com/cloudfront/home
- **Secrets Manager**: https://console.aws.amazon.com/secretsmanager/home?region=us-east-1
- **CloudWatch Dashboards**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
- **CloudWatch Alarms**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:

### Terraform State

- **State Backend**: Local (infrastructure directory)
- **To recreate**: `cd infrastructure && terraform apply`

---

**Document Version**: 1.0
**Last Reviewed**: 2025-11-14
**Next Review Date**: 2026-01-14
