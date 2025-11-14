# Story 1.9 - Ultra-Verified Status & Setup Guide

**Generated**: 2025-11-14
**AWS Account**: 971422717446
**Region**: us-east-1

---

## ✅ ALREADY EXISTS (From Story 1.1)

### 1. ECR Repository
- **Status**: ✅ DEPLOYED
- **URL**: `971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api`
- **Action**: NONE - Ready to receive Docker images

### 2. ECS Cluster
- **Status**: ✅ DEPLOYED
- **Name**: `plccoach-cluster`
- **ARN**: `arn:aws:ecs:us-east-1:971422717446:cluster/plccoach-cluster`
- **Action**: NONE - Cluster is running

### 3. RDS PostgreSQL Database
- **Status**: ✅ DEPLOYED
- **Endpoint**: `plccoach-db.crws0amqe1e3.us-east-1.rds.amazonaws.com:5432`
- **Database**: `plccoach`
- **Secret ARN**: `arn:aws:secretsmanager:us-east-1:971422717446:secret:plccoach-db-password-OnoiFn`
- **Action**: NONE - Database is running with pgvector support

### 4. S3 Buckets
- **Status**: ✅ DEPLOYED
- **Frontend**: `plccoach-frontend-971422717446`
- **Content**: `plccoach-content-971422717446`
- **Backups**: `plccoach-backups-971422717446`
- **Exports**: `plccoach-exports-971422717446`
- **Action**: NONE - Buckets are configured

### 5. CloudFront Distribution
- **Status**: ✅ DEPLOYED
- **Distribution ID**: `E7TVM4BHHDN7X`
- **Domain**: `d3394we8ve9ne3.cloudfront.net`
- **Action**: ✅ CAN USE NOW (no custom domain yet)

### 6. Application Load Balancer
- **Status**: ✅ DEPLOYED
- **DNS**: `plccoach-alb-230561554.us-east-1.elb.amazonaws.com`
- **Target Groups**:
  - Primary: `arn:aws:elasticloadbalancing:us-east-1:971422717446:targetgroup/plccoach-api-tg/c0e176c1812c484f`
  - Alternate: `arn:aws:elasticloadbalancing:us-east-1:971422717446:targetgroup/plccoach-api-tg-alt/3490c1c494efd024`
- **Action**: NONE - Ready for blue-green deployments

### 7. CloudWatch & SNS
- **Status**: ✅ DEPLOYED
- **Log Group**: `/ecs/plccoach/api`
- **SNS Topic**: `arn:aws:sns:us-east-1:971422717446:plccoach-alarms`
- **Action**: ⚠️ Need to subscribe email to SNS topic

### 8. IAM Roles
- **Status**: ✅ DEPLOYED
- **Task Execution Role**: `arn:aws:iam::971422717446:role/plccoach-ecs-task-execution-role`
- **Task Role**: `arn:aws:iam::971422717446:role/plccoach-ecs-task-role`
- **Action**: NONE - Roles have correct permissions

### 9. VPC & Networking
- **Status**: ✅ DEPLOYED
- **VPC ID**: `vpc-03cd6462b46350c8e`
- **Subnets**: 2 public, 2 private
- **Security Groups**: Configured for ALB, ECS, RDS
- **Action**: NONE - Networking is ready

---

## ❌ MISSING - Need to Create

### 1. ECS Service
- **Status**: ❌ NOT DEPLOYED
- **Current**: `serviceArns: []` (No services running)
- **Needed**: ECS service to run API containers
- **Action**: ✅ AUTOMATED (will create via Terraform/script)

### 2. ECS Task Definition
- **Status**: ❌ NOT DEPLOYED
- **Needed**: Task definition with container specs
- **Action**: ✅ AUTOMATED (will create)

### 3. OAuth Secrets in Secrets Manager
- **Status**: ❌ NOT DEPLOYED
- **Current**: Only `plccoach-db-password` exists
- **Needed**:
  - `plccoach/production/google-oauth`
  - `plccoach/production/clever-sso`
  - `plccoach/production/session`
- **Action**: ⚠️ MANUAL (requires your OAuth credentials)

### 4. GitHub Actions Workflow
- **Status**: ❌ NOT CREATED
- **Current**: No `.github/workflows/` directory
- **Needed**: `deploy-production.yml`
- **Action**: ✅ AUTOMATED (will create)

### 5. GitHub Secrets
- **Status**: ⚠️ UNKNOWN (need to check GitHub)
- **Needed**:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION` (us-east-1)
  - `ECR_REPOSITORY` (971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api)
- **Action**: ⚠️ MANUAL (requires AWS credentials)

### 6. Production Domain
- **Status**: ❌ NOT CONFIGURED
- **Current**: `domain_name = ""` in terraform.tfvars
- **Options**:
  - **Option A**: Use ALB DNS (available now): `plccoach-alb-230561554.us-east-1.elb.amazonaws.com`
  - **Option B**: Configure custom domain (requires domain registration)
- **Action**: ⚠️ DECISION NEEDED

### 7. SSL Certificate
- **Status**: ⚠️ DEPENDS ON DOMAIN
- **If using ALB DNS**: Can test with HTTP (no SSL needed initially)
- **If using custom domain**: Need ACM certificate
- **Action**: ⚠️ CONDITIONAL

---

## 🤖 AUTOMATED SETUP STEPS

I will create automation scripts for everything possible:

### Script 1: Create OAuth Secrets (Requires Your Input)
```bash
./scripts/setup-secrets.sh
```
**Prompts you for**:
- Google OAuth Client ID
- Google OAuth Client Secret
- Clever Client ID
- Clever Client Secret
- Session Secret (or auto-generates)

### Script 2: Deploy ECS Service
```bash
./scripts/deploy-ecs-service.sh
```
**Automatically**:
- Creates ECS task definition
- Creates ECS service
- Configures blue-green deployment
- Connects to ALB

### Script 3: Setup GitHub Actions
```bash
./scripts/setup-github-actions.sh
```
**Automatically**:
- Creates `.github/workflows/deploy-production.yml`
- Provides commands to set GitHub secrets

### Script 4: Subscribe to SNS Alerts
```bash
./scripts/setup-sns-alerts.sh your-email@example.com
```
**Automatically**:
- Subscribes email to SNS topic
- You confirm subscription via email

### Script 5: Deploy Frontend to S3/CloudFront
```bash
./scripts/deploy-frontend.sh
```
**Automatically**:
- Builds frontend
- Uploads to S3
- Invalidates CloudFront cache

---

## ⚠️ MANUAL STEPS YOU MUST DO

### Step 1: Configure OAuth Production URLs

#### Google OAuth:
1. Go to: https://console.cloud.google.com/apis/credentials
2. Select your OAuth 2.0 Client ID
3. Add Authorized redirect URI: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/google/callback`
4. Save changes

#### Clever SSO:
1. Go to: https://apps.clever.com/
2. Select your application
3. Add redirect URI: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/clever/callback`
4. Save changes

### Step 2: Create GitHub Secrets
1. Go to: https://github.com/reena96/plccoach/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret:
   - `AWS_ACCESS_KEY_ID`: (Get from AWS IAM)
   - `AWS_SECRET_ACCESS_KEY`: (Get from AWS IAM)
   - `AWS_REGION`: `us-east-1`
   - `ECR_REPOSITORY`: `971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api`

**To create AWS credentials for GitHub Actions**:
```bash
aws iam create-access-key --user-name github-actions-plccoach
```

### Step 3: (Optional) Configure Custom Domain
If you want a custom domain instead of ALB DNS:

1. **Register domain** (if you don't have one)
2. **Request ACM certificate**:
   ```bash
   aws acm request-certificate \
     --domain-name plccoach.yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```
3. **Add DNS validation records** to your domain
4. **Update terraform.tfvars**: `domain_name = "plccoach.yourdomain.com"`
5. **Re-run Terraform**: `cd infrastructure && terraform apply`

---

## 📊 COST ESTIMATE

Based on current infrastructure:

**Already Running (Story 1.1)**:
- RDS db.t3.medium: ~$60/month
- ALB: ~$23/month
- CloudFront: ~$1-5/month (varies with usage)
- S3: ~$1-3/month
- **Subtotal**: ~$85-90/month

**Will Add (Story 1.9)**:
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB): ~$30/month
- CloudWatch Logs (90-day retention): ~$2-5/month
- Secrets Manager (4 secrets): ~$1.60/month
- **Additional**: ~$33-37/month

**Total Estimated Cost**: ~$120-130/month

---

## 🚀 QUICK START - Get Running NOW

**Want to deploy with what we have right now?**

```bash
# Step 1: Create OAuth secrets (I'll prompt you)
./scripts/setup-secrets.sh

# Step 2: Deploy ECS service
./scripts/deploy-ecs-service.sh

# Step 3: Deploy frontend
./scripts/deploy-frontend.sh

# Step 4: Test it!
curl http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/health
```

**Access your app**:
- Frontend: `https://d3394we8ve9ne3.cloudfront.net`
- Backend API: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com`

---

## ✅ NEXT ACTIONS

**Priority 1 - Can Deploy NOW**:
1. ✅ I'll create all automation scripts
2. ⚠️ You run `./scripts/setup-secrets.sh` (enter your OAuth credentials)
3. ✅ I'll deploy ECS service
4. ✅ I'll deploy frontend
5. ✅ Test deployment works

**Priority 2 - For GitHub Actions CI/CD**:
6. ⚠️ You create GitHub secrets (AWS credentials)
7. ✅ I'll create GitHub Actions workflow
8. ✅ Test automated deployment

**Priority 3 - Production Polish (Optional)**:
9. ⚠️ You decide on custom domain
10. ⚠️ If custom domain, configure DNS + SSL
11. ⚠️ Update OAuth redirect URLs to use custom domain

---

**Ready to proceed?** I'll create all the automation scripts now!
