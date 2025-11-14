# Story 1.9 Validation Guide: Deployment & Production Readiness

**Story ID**: 1.9
**Epic**: Epic 1 - Foundation & Authentication
**Status**: ready-for-dev (implementation requires AWS infrastructure access)
**Nature**: Infrastructure & Deployment Story

---

## Important Note

**Story 1.9 is an infrastructure and deployment story that cannot be fully automated in a local development environment.** This validation guide provides comprehensive documentation, checklists, and manual verification steps for deploying the PLC Coach application to AWS production infrastructure.

**Prerequisites for Implementation:**
- AWS account with appropriate permissions (ECS, ECR, S3, CloudFront, Secrets Manager, CloudWatch)
- GitHub repository with Actions enabled
- Production domain registered and accessible
- Google OAuth application registered with production redirect URIs
- Clever SSO application configured with production callback URLs
- AWS CLI configured with production credentials

---

## 30-Second Quick Validation

**For Local Development (Pre-Deployment):**
```bash
# Verify all Story 1.1-1.8 tests pass
cd /Users/reena/plccoach/api-service
docker-compose up -d
docker-compose exec api pytest -v

# Expected: 47 passed

# Verify frontend builds successfully
cd /Users/reena/plccoach/frontend
npm run build

# Expected: dist/ folder created with optimized bundles
```

**For Production Deployment (Post-Deployment):**
```bash
# Run smoke tests
./scripts/smoke-tests.sh https://plccoach.example.com

# Expected: All health checks pass, OAuth redirects work
```

---

## Acceptance Criteria Validation

### AC1: GitHub Actions CI/CD Pipeline Configuration

**Implementation Checklist:**
- [ ] Create `.github/workflows/deploy-production.yml`
- [ ] Configure trigger on push to `main` branch
- [ ] Job 1: Run backend tests (`pytest`)
- [ ] Job 2: Build Docker image for `api-service`
- [ ] Job 3: Push Docker image to AWS ECR (tags: git SHA, latest)
- [ ] Job 4: Run database migrations (`alembic upgrade head`)
- [ ] Job 5: Deploy to ECS Fargate (update service with new task definition)
- [ ] Job 6: Run smoke tests post-deployment
- [ ] Job 7: Rollback on smoke test failure
- [ ] Configure GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`

**Validation Steps:**
1. Review workflow file syntax:
   ```bash
   # Validate YAML syntax
   yamllint .github/workflows/deploy-production.yml
   ```

2. Test workflow locally (if using act):
   ```bash
   act -n  # Dry run to validate workflow
   ```

3. Manual trigger test:
   ```bash
   # Push to main and monitor GitHub Actions tab
   git push origin main
   # Visit https://github.com/<org>/<repo>/actions
   ```

4. Verify pipeline stages execute in order:
   - ✅ Tests pass
   - ✅ Docker image built and pushed to ECR
   - ✅ Migrations run successfully
   - ✅ ECS service updated
   - ✅ Smoke tests pass
   - ✅ Deployment marked successful

5. Test failure handling:
   - Introduce failing test → verify pipeline stops
   - Introduce failing migration → verify deployment blocked
   - Introduce failing smoke test → verify rollback triggered

**Expected Outcome:**
- Pipeline executes successfully on clean push to main
- Failed tests/migrations/smoke-tests prevent deployment
- Rollback works automatically

---

### AC2: Frontend Build and Deployment

**Implementation Checklist:**
- [ ] Create S3 bucket: `plccoach-frontend-production`
- [ ] Configure S3 bucket for static website hosting
- [ ] Set S3 bucket policy for CloudFront access
- [ ] Add frontend build job to GitHub Actions workflow
- [ ] Upload `frontend/dist/` to S3 bucket
- [ ] Trigger CloudFront invalidation (`/*` path)

**Validation Steps:**
1. Verify frontend builds locally:
   ```bash
   cd frontend
   npm ci
   npm run build
   ls -la dist/
   ```
   **Expected**: `dist/` folder with `index.html`, `assets/`, optimized JS/CSS

2. Test S3 upload (manual):
   ```bash
   aws s3 sync frontend/dist/ s3://plccoach-frontend-production/ --delete
   ```

3. Verify S3 bucket website endpoint:
   ```bash
   curl http://plccoach-frontend-production.s3-website-us-east-1.amazonaws.com/
   ```
   **Expected**: HTML content returned

4. Test CloudFront distribution:
   ```bash
   curl https://plccoach.example.com/
   ```
   **Expected**: Frontend application loads

5. Verify CloudFront invalidation:
   ```bash
   aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
   ```

**Expected Outcome:**
- Frontend builds without errors
- S3 bucket serves static files
- CloudFront distributes frontend globally
- Cache invalidation clears old versions

---

### AC3: Health Check Endpoints Validation

**Implementation Checklist:**
- [ ] Update `GET /health` to include `version` field
- [ ] Update `GET /health` to include `timestamp` field
- [ ] Modify `HealthResponse` schema to add new fields
- [ ] Update `/ready` to return 503 when database is down
- [ ] Add version from environment variable (`APP_VERSION`)

**Code Changes:**
```python
# api-service/app/routers/health.py
from datetime import datetime, timezone
from app.config import settings

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,  # New field
        timestamp=datetime.now(timezone.utc)  # New field
    )
```

**Validation Steps:**
1. Test health endpoint locally:
   ```bash
   curl http://localhost:8000/health
   ```
   **Expected Response:**
   ```json
   {
     "status": "healthy",
     "service": "plc-coach-api",
     "version": "1.0.0",
     "timestamp": "2025-11-13T12:00:00Z"
   }
   ```

2. Test readiness endpoint with database online:
   ```bash
   curl http://localhost:8000/ready
   ```
   **Expected**: 200 OK with database: "connected"

3. Test readiness endpoint with database offline:
   ```bash
   docker-compose stop postgres
   curl http://localhost:8000/ready
   ```
   **Expected**: 503 Service Unavailable

4. Test in production:
   ```bash
   curl https://api.plccoach.example.com/health
   curl https://api.plccoach.example.com/ready
   ```

**Expected Outcome:**
- Health endpoint returns version and timestamp
- Readiness endpoint validates database connectivity
- Smoke tests use these endpoints for deployment validation

---

### AC4: Authentication Smoke Tests

**Implementation Checklist:**
- [ ] Register production OAuth redirect URIs with Google
- [ ] Register production OAuth redirect URIs with Clever
- [ ] Update backend config to use production callback URLs
- [ ] Create smoke test script: `scripts/smoke-tests.sh`
- [ ] Test 1: GET /auth/google/login returns 302 redirect
- [ ] Test 2: GET /auth/clever/login returns 302 redirect
- [ ] Test 3: Verify session cookies set correctly
- [ ] Test 4: GET /auth/me works with valid session

**Smoke Test Script:**
```bash
#!/bin/bash
# scripts/smoke-tests.sh

BASE_URL="${1:-https://plccoach.example.com}"
ERRORS=0

echo "Running smoke tests against $BASE_URL"

# Test 1: Health check
echo "Test 1: Health check"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Health check passed"
else
  echo "❌ Health check failed (HTTP $HTTP_STATUS)"
  ERRORS=$((ERRORS + 1))
fi

# Test 2: Ready check
echo "Test 2: Readiness check"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/ready")
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Readiness check passed"
else
  echo "❌ Readiness check failed (HTTP $HTTP_STATUS)"
  ERRORS=$((ERRORS + 1))
fi

# Test 3: Google OAuth redirect
echo "Test 3: Google OAuth redirect"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/auth/google/login")
if [ "$HTTP_STATUS" -eq 302 ] || [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Google OAuth redirect works"
else
  echo "❌ Google OAuth failed (HTTP $HTTP_STATUS)"
  ERRORS=$((ERRORS + 1))
fi

# Test 4: Clever SSO redirect
echo "Test 4: Clever SSO redirect"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L "$BASE_URL/auth/clever/login")
if [ "$HTTP_STATUS" -eq 302 ] || [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Clever SSO redirect works"
else
  echo "❌ Clever SSO failed (HTTP $HTTP_STATUS)"
  ERRORS=$((ERRORS + 1))
fi

# Test 5: Frontend loads
echo "Test 5: Frontend loads"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "✅ Frontend loads successfully"
else
  echo "❌ Frontend failed (HTTP $HTTP_STATUS)"
  ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
  echo ""
  echo "🎉 All smoke tests passed!"
  exit 0
else
  echo ""
  echo "💥 $ERRORS smoke test(s) failed"
  exit 1
fi
```

**Validation Steps:**
1. Make script executable:
   ```bash
   chmod +x scripts/smoke-tests.sh
   ```

2. Run locally:
   ```bash
   ./scripts/smoke-tests.sh http://localhost:8000
   ```

3. Run against production:
   ```bash
   ./scripts/smoke-tests.sh https://plccoach.example.com
   ```

4. Test OAuth flows manually:
   - Visit https://plccoach.example.com
   - Click "Login with Google" → redirected to Google
   - After consent → redirected back with session cookie
   - Verify logged in (user name in header)

**Expected Outcome:**
- All smoke tests pass
- OAuth flows work end-to-end in production
- Session cookies set with `secure` flag

---

### AC5: CloudWatch Monitoring Dashboards

**Implementation Checklist:**
- [ ] Create CloudWatch dashboard: `PLC-Coach-Production`
- [ ] Add widget: API request count (ALB RequestCount metric)
- [ ] Add widget: API error rate (4XXCount + 5XXCount / RequestCount * 100)
- [ ] Add widget: API response time (ALB TargetResponseTime p50, p95, p99)
- [ ] Add widget: Database connections (RDS DatabaseConnections)
- [ ] Add widget: ECS task count and CPU/memory utilization
- [ ] Configure 1-minute refresh interval

**Dashboard JSON Template:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/ApplicationELB", "RequestCount", { "stat": "Sum", "label": "Request Count" } ]
        ],
        "period": 60,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Request Count"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ { "expression": "(m1 + m2) / m3 * 100", "label": "Error Rate %", "id": "e1" } ],
          [ "AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", { "id": "m1", "visible": false } ],
          [ ".", "HTTPCode_Target_5XX_Count", { "id": "m2", "visible": false } ],
          [ ".", "RequestCount", { "id": "m3", "visible": false } ]
        ],
        "title": "API Error Rate"
      }
    }
  ]
}
```

**Validation Steps:**
1. Create dashboard via AWS CLI:
   ```bash
   aws cloudwatch put-dashboard --dashboard-name PLC-Coach-Production --dashboard-body file://dashboard.json
   ```

2. Verify dashboard exists:
   ```bash
   aws cloudwatch list-dashboards
   ```

3. Access dashboard in console:
   - Navigate to CloudWatch → Dashboards
   - Open `PLC-Coach-Production`
   - Verify all widgets display metrics

4. Generate traffic and verify metrics update:
   ```bash
   # Generate requests
   for i in {1..100}; do curl https://plccoach.example.com/health; done

   # Wait 2 minutes, refresh dashboard
   # Verify request count increased
   ```

**Expected Outcome:**
- Dashboard visible in CloudWatch console
- Metrics populate within 5 minutes of deployment
- Graphs update in real-time

---

### AC6: CloudWatch Alarms Configuration

**Implementation Checklist:**
- [ ] Create SNS topic: `plccoach-production-alerts`
- [ ] Subscribe email to SNS topic and confirm subscription
- [ ] Create alarm: `API-Error-Rate-High` (>5% for 5 minutes)
- [ ] Create alarm: `API-Response-Time-High` (p95 >10s for 5 minutes)
- [ ] Create alarm: `Database-Connections-High` (>80% for 5 minutes)
- [ ] Create alarm: `ECS-Unhealthy-Tasks` (>0 for 2 minutes)

**Alarm Configuration (Error Rate Example):**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name API-Error-Rate-High \
  --alarm-description "API error rate exceeded 5% threshold" \
  --actions-enabled \
  --alarm-actions arn:aws:sns:us-east-1:123456789:plccoach-production-alerts \
  --evaluation-periods 5 \
  --datapoints-to-alarm 5 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --metrics file://error-rate-metric.json
```

**Validation Steps:**
1. Create all 4 alarms via CLI or console

2. Verify alarms exist:
   ```bash
   aws cloudwatch describe-alarms --alarm-names API-Error-Rate-High API-Response-Time-High Database-Connections-High ECS-Unhealthy-Tasks
   ```

3. Test alarm triggering (Error Rate):
   ```bash
   # Trigger 500 errors by stopping database
   docker-compose stop postgres

   # Generate requests
   for i in {1..1000}; do curl https://plccoach.example.com/ready; done

   # Wait 5 minutes
   # Check alarm state
   aws cloudwatch describe-alarms --alarm-names API-Error-Rate-High
   ```
   **Expected**: Alarm state = ALARM, SNS notification sent

4. Test ECS health alarm:
   ```bash
   # Stop one ECS task
   aws ecs update-service --cluster plccoach-cluster --service plccoach-api-service --desired-count 1

   # Wait 2 minutes
   # Verify alarm triggered
   ```

**Expected Outcome:**
- All 4 alarms created and in OK state
- Alarms trigger when thresholds exceeded
- SNS notifications delivered to email

---

### AC7: Environment Variables and Secrets Management

**Implementation Checklist:**
- [ ] Create secret: `plccoach/production/database`
- [ ] Store `DATABASE_URL` in secret
- [ ] Create secret: `plccoach/production/google-oauth`
- [ ] Store `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- [ ] Create secret: `plccoach/production/clever-sso`
- [ ] Store `CLEVER_CLIENT_ID` and `CLEVER_CLIENT_SECRET`
- [ ] Create secret: `plccoach/production/session`
- [ ] Generate and store `SESSION_SECRET_KEY` (64-char random string)
- [ ] Configure 90-day rotation policy
- [ ] Grant ECS task execution role permissions to read secrets

**Create Secrets:**
```bash
# Database URL
aws secretsmanager create-secret \
  --name plccoach/production/database \
  --description "Production database connection string" \
  --secret-string '{"DATABASE_URL":"postgresql://user:pass@rds-endpoint:5432/plccoach"}'

# Google OAuth
aws secretsmanager create-secret \
  --name plccoach/production/google-oauth \
  --description "Google OAuth credentials" \
  --secret-string '{"GOOGLE_CLIENT_ID":"xxx.apps.googleusercontent.com","GOOGLE_CLIENT_SECRET":"GOCSPX-xxx"}'

# Clever SSO
aws secretsmanager create-secret \
  --name plccoach/production/clever-sso \
  --description "Clever SSO credentials" \
  --secret-string '{"CLEVER_CLIENT_ID":"xxx","CLEVER_CLIENT_SECRET":"xxx"}'

# Session secret
SESSION_KEY=$(openssl rand -hex 32)
aws secretsmanager create-secret \
  --name plccoach/production/session \
  --description "Session encryption key" \
  --secret-string "{\"SESSION_SECRET_KEY\":\"$SESSION_KEY\"}"
```

**ECS Task Definition (Secrets Reference):**
```json
{
  "secrets": [
    {
      "name": "DATABASE_URL",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:plccoach/production/database:DATABASE_URL::"
    },
    {
      "name": "GOOGLE_CLIENT_ID",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:plccoach/production/google-oauth:GOOGLE_CLIENT_ID::"
    }
  ]
}
```

**Validation Steps:**
1. Verify secrets exist:
   ```bash
   aws secretsmanager list-secrets | grep plccoach
   ```

2. Test secret retrieval:
   ```bash
   aws secretsmanager get-secret-value --secret-id plccoach/production/database
   ```

3. Verify ECS task can access secrets:
   - Deploy ECS task
   - Check task logs for successful database connection
   - Verify no "secret not found" errors

4. Test rotation policy:
   ```bash
   aws secretsmanager describe-secret --secret-id plccoach/production/session
   # Verify RotationEnabled: true, RotationRules: { AutomaticallyAfterDays: 90 }
   ```

**Expected Outcome:**
- All 4 secrets created in Secrets Manager
- ECS tasks can retrieve secrets at runtime
- Application starts successfully with production credentials
- Rotation policy configured

---

### AC8: Database Migration Execution

**Implementation Checklist:**
- [ ] Create migration script: `scripts/run-migrations.sh`
- [ ] Script retrieves DATABASE_URL from Secrets Manager
- [ ] Script runs `alembic upgrade head`
- [ ] Add migration job to GitHub Actions workflow
- [ ] Migration job runs before ECS deployment
- [ ] Pipeline fails if migrations fail

**Migration Script:**
```bash
#!/bin/bash
# scripts/run-migrations.sh

set -e  # Exit on error

echo "Retrieving database credentials from Secrets Manager..."
DB_SECRET=$(aws secretsmanager get-secret-value --secret-id plccoach/production/database --query SecretString --output text)
export DATABASE_URL=$(echo $DB_SECRET | jq -r '.DATABASE_URL')

echo "Running database migrations..."
cd api-service
alembic upgrade head

echo "Migrations completed successfully"
```

**Validation Steps:**
1. Test migration script locally (against staging database):
   ```bash
   chmod +x scripts/run-migrations.sh
   ./scripts/run-migrations.sh
   ```

2. Test idempotency (run twice):
   ```bash
   ./scripts/run-migrations.sh
   ./scripts/run-migrations.sh
   # Should succeed both times without errors
   ```

3. Test failure handling:
   ```bash
   # Create migration with syntax error
   # Run script
   # Verify script exits with non-zero code
   ```

4. Verify migrations in production:
   ```bash
   # After deployment, check database schema
   psql $DATABASE_URL -c "\dt"
   # Verify all tables exist: users, sessions, conversations, messages
   ```

**Expected Outcome:**
- Migrations run successfully before deployment
- Idempotent (can run multiple times safely)
- Failed migrations block deployment

---

### AC9: Production URL and SSL/TLS Configuration

**Implementation Checklist:**
- [ ] Request SSL certificate from AWS Certificate Manager for production domain
- [ ] Validate domain ownership (DNS validation)
- [ ] Attach certificate to CloudFront distribution
- [ ] Attach certificate to Application Load Balancer
- [ ] Configure ALB HTTP listener to redirect to HTTPS
- [ ] Enable auto-renewal for certificate
- [ ] Configure security headers on CloudFront

**Security Headers (CloudFront Function):**
```javascript
function handler(event) {
    var response = event.response;
    var headers = response.headers;

    headers['strict-transport-security'] = { value: 'max-age=31536000; includeSubDomains' };
    headers['x-frame-options'] = { value: 'DENY' };
    headers['x-content-type-options'] = { value: 'nosniff' };
    headers['content-security-policy'] = { value: "default-src 'self'" };

    return response;
}
```

**Validation Steps:**
1. Verify SSL certificate:
   ```bash
   openssl s_client -connect plccoach.example.com:443 -servername plccoach.example.com
   # Verify certificate is valid, not expired
   ```

2. Test HTTPS access:
   ```bash
   curl -I https://plccoach.example.com/
   # Expected: HTTP/2 200
   ```

3. Test HTTP redirect:
   ```bash
   curl -I http://plccoach.example.com/
   # Expected: HTTP 301 or 302, Location: https://...
   ```

4. Test security headers:
   ```bash
   curl -I https://plccoach.example.com/ | grep -i "strict-transport-security\|x-frame-options\|content-security-policy"
   ```
   **Expected**:
   ```
   strict-transport-security: max-age=31536000; includeSubDomains
   x-frame-options: DENY
   content-security-policy: default-src 'self'
   x-content-type-options: nosniff
   ```

5. Use online security scanner:
   ```
   Visit: https://securityheaders.com
   Enter: https://plccoach.example.com
   Expected grade: A or higher
   ```

**Expected Outcome:**
- HTTPS works with valid certificate
- HTTP redirects to HTTPS
- Security headers present in all responses
- No certificate warnings in browser

---

### AC10: Deployment Runbook Documentation

**Implementation Checklist:**
- [ ] Create `/docs/deployment-runbook.md`
- [ ] Document deployment process step-by-step
- [ ] Document rollback procedure
- [ ] Document environment variables reference
- [ ] Document troubleshooting guide
- [ ] Document smoke test execution
- [ ] Test runbook by performing a deployment

**Runbook Template:**
```markdown
# PLC Coach Deployment Runbook

## Deployment Process

### 1. Pre-Deployment Checklist
- [ ] All tests passing locally
- [ ] GitHub Actions workflow configured
- [ ] AWS credentials configured in GitHub Secrets
- [ ] Secrets created in AWS Secrets Manager
- [ ] Production OAuth redirect URIs registered

### 2. Deployment Steps
1. Merge feature branch to `main`
2. GitHub Actions automatically triggers
3. Monitor pipeline: https://github.com/<org>/<repo>/actions
4. Wait for all jobs to complete (5-10 minutes)
5. Verify deployment: `./scripts/smoke-tests.sh https://plccoach.example.com`

### 3. Rollback Procedure
If deployment fails or issues detected:

**Option 1: Revert Git Commit**
```bash
git revert HEAD
git push origin main
# Wait for pipeline to redeploy previous version
```

**Option 2: Manual ECS Rollback**
```bash
# List task definitions
aws ecs list-task-definitions --family-prefix plccoach-api

# Update service to previous task definition
aws ecs update-service \
  --cluster plccoach-cluster \
  --service plccoach-api-service \
  --task-definition plccoach-api-task:PREVIOUS_VERSION
```

## Troubleshooting

### Deployment Fails at Test Stage
- Check GitHub Actions logs for failing test
- Run tests locally: `docker-compose exec api pytest -v`
- Fix failing test, commit, push

### Deployment Fails at Migration Stage
- Check migration script logs
- Verify DATABASE_URL secret is correct
- Run migrations manually: `./scripts/run-migrations.sh`
- If migration has errors, create rollback migration

### Smoke Tests Fail
- Check which endpoint failed (health, ready, auth)
- Review CloudWatch logs for errors
- Verify secrets loaded correctly
- Check ECS task health status

### Application Not Accessible
- Verify CloudFront distribution status (deployed)
- Check ALB target group health
- Verify security groups allow traffic
- Check Route53 DNS records
```

**Validation Steps:**
1. Review runbook completeness
2. Perform test deployment following runbook
3. Document any missing steps or corrections
4. Update runbook based on real deployment experience

**Expected Outcome:**
- Runbook is complete and accurate
- Team can follow runbook to deploy successfully
- Troubleshooting guide covers common issues

---

## Manual Integration Testing

Since Story 1.9 requires AWS infrastructure, the following integration tests should be performed **after AWS resources are provisioned:**

1. **Complete Deployment Test:**
   - Create test commit and push to main
   - Monitor GitHub Actions pipeline
   - Verify all jobs pass
   - Access production URL
   - Test authentication flows

2. **Rollback Test:**
   - Introduce intentional failure
   - Verify pipeline rolls back
   - Verify previous version restored

3. **Monitoring Test:**
   - Generate production traffic
   - Verify CloudWatch metrics populate
   - Trigger alarm condition
   - Verify SNS notification received

4. **End-to-End User Flow:**
   - Visit production URL
   - Log in with Google
   - Access dashboard
   - Log out
   - Log in with Clever
   - Verify session persistence

---

## Known Limitations

**This story cannot be fully implemented without:**
1. AWS account access
2. Production domain ownership
3. GitHub repository with Actions enabled
4. OAuth provider production registration

**Recommendation:**
- Complete Stories 1.1-1.8 first (all done)
- Provision AWS infrastructure manually or with Terraform
- Configure GitHub Actions with AWS credentials
- Follow this validation guide to deploy step-by-step

---

## Files to Create

**Deployment:**
- `.github/workflows/deploy-production.yml` - CI/CD pipeline
- `scripts/run-migrations.sh` - Database migration script
- `scripts/smoke-tests.sh` - Post-deployment validation
- `infrastructure/ecs-task-definition.json` - ECS task configuration

**Documentation:**
- `docs/deployment-runbook.md` - Deployment procedures
- `docs/troubleshooting.md` - Common issues and solutions

**Tests:**
- `tests/deployment/test_smoke.py` - Automated smoke tests

---

## Next Steps

After Story 1.9 implementation:
1. **Epic 1 Complete** - All 9 stories done
2. **Epic Validation** - Create comprehensive Epic 1 validation guide
3. **Production Ready** - Authentication and infrastructure deployed
4. **Epic 2** - Begin Core AI Coach development

---

**Validation Guide Created By**: Claude Sonnet 4.5
**Date**: 2025-11-13
**Story Status**: ready-for-dev (requires AWS infrastructure for implementation)
