# PLC Coach - Production Deployment Quickstart

**🎯 Goal**: Get PLC Coach running in production in ~30 minutes

**Status**: 80% automated - only requires your OAuth credentials and email

---

## ✅ What's Already Done

From Story 1.1, you already have:
- ✅ ECR repository for Docker images
- ✅ ECS cluster ready to run containers
- ✅ RDS PostgreSQL database with pgvector
- ✅ S3 buckets for frontend hosting
- ✅ CloudFront CDN distribution
- ✅ Application Load Balancer with blue-green deployment
- ✅ VPC, subnets, security groups
- ✅ IAM roles with correct permissions
- ✅ CloudWatch logging and SNS alerts topic

**Cost**: ~$85-90/month already running

---

## 🚀 Quick Deployment (3 Steps)

### Step 1: Configure Secrets (5 minutes)

Run the automated script - it will prompt you for your OAuth credentials:

```bash
./scripts/setup-secrets.sh
```

**You'll be asked for**:
- Google OAuth Client ID
- Google OAuth Client Secret
- Clever SSO Client ID
- Clever SSO Client Secret
- Session secret (or auto-generate)

**Where to get these**:
- Google: https://console.cloud.google.com/apis/credentials
- Clever: https://apps.clever.com/

### Step 2: Build & Deploy Backend (10 minutes)

```bash
# Build Docker image
cd api-service
docker build -t 971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api:latest .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  971422717446.dkr.ecr.us-east-1.amazonaws.com

# Push image
docker push 971422717446.dkr.ecr.us-east-1.amazonaws.com/plccoach/api:latest

cd ..

# Deploy to ECS (automated)
./scripts/deploy-ecs-service.sh
```

### Step 3: Deploy Frontend (5 minutes)

```bash
./scripts/deploy-frontend.sh
```

**That's it!** Your app is now live at:
- Frontend: `https://d3394we8ve9ne3.cloudfront.net`
- Backend: `http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com`

---

## 🔧 Post-Deployment Setup (10 minutes)

### Update OAuth Redirect URLs

**Google OAuth**:
1. Go to https://console.cloud.google.com/apis/credentials
2. Click your OAuth 2.0 Client ID
3. Add to "Authorized redirect URIs":
   ```
   http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/google/callback
   ```
4. Save

**Clever SSO**:
1. Go to https://apps.clever.com/
2. Select your application
3. Add redirect URI:
   ```
   http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/auth/clever/callback
   ```
4. Save

### Subscribe to Alerts

```bash
./scripts/setup-sns-alerts.sh your-email@example.com
```

Check your email and confirm the subscription.

---

## ✅ Validation

Run smoke tests to verify everything works:

```bash
./scripts/smoke-tests.sh
```

Expected output:
```
Testing: Health endpoint... ✅ PASSED
Testing: Ready endpoint... ✅ PASSED
Testing: Google OAuth... ✅ PASSED
Testing: Clever SSO... ✅ PASSED
Testing: Frontend... ✅ PASSED

🎉 All smoke tests passed!
```

---

## 🔄 Setting Up CI/CD (Optional - 15 minutes)

Enable automatic deployments on git push:

### 1. Create GitHub Secrets

```bash
# This script shows you exactly what to do
./scripts/setup-github-secrets.sh
```

You need to add these secrets to GitHub:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`

### 2. Test Automated Deployment

```bash
# Make a small change
git commit -am "Test automated deployment"
git push origin main

# GitHub Actions will automatically:
# - Run tests
# - Build Docker image
# - Run database migrations
# - Deploy to ECS
# - Run smoke tests
# - Deploy frontend
```

Watch the deployment:
```bash
gh run watch
```

Or visit: https://github.com/reena96/plccoach/actions

---

## 📊 Monitoring

### CloudWatch Dashboard

View metrics: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:

### View Logs

```bash
# Live tail
aws logs tail /ecs/plccoach/api --follow --region us-east-1

# Search for errors
aws logs filter-pattern "ERROR" --log-group-name /ecs/plccoach/api --region us-east-1
```

### Check Service Health

```bash
# Service status
aws ecs describe-services \
  --cluster plccoach-cluster \
  --services plccoach-api-service \
  --region us-east-1 \
  --query 'services[0].{Running:runningCount,Desired:desiredCount,Status:status}'

# Health check
curl http://plccoach-alb-230561554.us-east-1.elb.amazonaws.com/api/health | jq
```

---

## 🆘 Troubleshooting

### Issue: Docker build fails

**Solution**: Check you're in the right directory
```bash
cd api-service
ls Dockerfile  # Should exist
```

### Issue: ECR login fails

**Solution**: Verify AWS credentials
```bash
aws sts get-caller-identity
# Should show your AWS account
```

### Issue: ECS tasks keep restarting

**Solution**: Check logs for errors
```bash
aws logs tail /ecs/plccoach/api --since 5m --region us-east-1
```

Common causes:
- Database connection failed (check security groups)
- Secrets not accessible (check IAM permissions)
- Health check failing (check `/api/health` endpoint)

### Issue: Frontend shows old version

**Solution**: Invalidate CloudFront cache
```bash
cd infrastructure
CLOUDFRONT_ID=$(terraform output -json | jq -r '.cloudfront_distribution_id.value')
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*"
```

---

## 📖 Full Documentation

- **Deployment Runbook**: `docs/deployment-runbook.md` (detailed procedures)
- **Status Report**: `docs/deployment/STORY-1.9-STATUS.md` (what exists vs needed)
- **Architecture**: `docs/technical/architecture.md`

---

## 💰 Cost Breakdown

**Already Running** (Story 1.1): ~$85-90/month
- RDS db.t3.medium: ~$60/month
- ALB: ~$23/month
- CloudFront: ~$1-5/month
- S3: ~$1-3/month

**Adding Now** (Story 1.9): +$33-37/month
- ECS Fargate (2 tasks): ~$30/month
- CloudWatch Logs: ~$2-5/month
- Secrets Manager: ~$1.60/month

**Total**: ~$120-130/month

---

## 🎯 Next Steps After Deployment

1. ✅ Test the application thoroughly
2. ✅ Verify both Google and Clever login work
3. ✅ Set up monitoring alerts
4. ⏭️ Move to Epic 2: Core AI Coach implementation

---

## 🔒 Security Notes

- All secrets stored in AWS Secrets Manager (encrypted at rest)
- No secrets in git repository
- OAuth callbacks use HTTPS in production (if using custom domain)
- Database in private subnet (not publicly accessible)
- ECS tasks have minimal IAM permissions

---

**Ready to deploy?** Start with Step 1!

Questions? See `docs/deployment-runbook.md` for detailed troubleshooting.
