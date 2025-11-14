# Story 1.9: Deployment & Production Readiness

Status: ready-for-dev

## Story

As a DevOps engineer,
I want to deploy the foundation services to production,
so that authentication and basic infrastructure are live and tested.

## Acceptance Criteria

1. **AC1: GitHub Actions CI/CD Pipeline Configuration**
   - Given code is merged to main branch
   - When the GitHub Actions workflow runs
   - Then it executes the following steps in order:
     - Runs unit tests (all tests must pass)
     - Builds Docker images for backend API service
     - Pushes images to AWS ECR with tags (git SHA, latest)
     - Deploys to ECS Fargate using blue-green deployment strategy
     - Runs smoke tests against deployed services
   - And the pipeline fails if any step fails
   - And deployment rollback occurs automatically if smoke tests fail

2. **AC2: Frontend Build and Deployment**
   - Given the frontend code is ready for deployment
   - When the CI/CD pipeline runs
   - Then the frontend is built using `npm run build`
   - And the build output (static files) is uploaded to S3 bucket
   - And CloudFront CDN distribution serves the frontend assets
   - And CloudFront invalidation is triggered to clear cache
   - And the application frontend is accessible at the production URL

3. **AC3: Health Check Endpoints Validation**
   - Given the backend service is deployed
   - When smoke tests run
   - Then `GET /health` endpoint returns 200 OK with service status
   - And `GET /ready` endpoint returns 200 OK (database connectivity confirmed)
   - And health check responses include service version and timestamp
   - And unhealthy responses (500) trigger deployment rollback

4. **AC4: Authentication Smoke Tests**
   - Given the application is deployed to production
   - When smoke tests execute
   - Then users can successfully initiate Google OAuth flow (redirect to Google)
   - And users can successfully initiate Clever SSO flow (redirect to Clever)
   - And OAuth callback URLs are correctly configured for production domain
   - And session cookies are set correctly (httpOnly, secure, sameSite)
   - And authenticated requests to `/auth/me` return 200 OK

5. **AC5: CloudWatch Monitoring Dashboards**
   - Given the application is running in production
   - When CloudWatch dashboards are configured
   - Then the following metrics are visible:
     - API request count (per minute)
     - API error rate (4xx and 5xx as percentage)
     - API response time (p50, p95, p99 percentiles)
     - Database connection pool usage
     - ECS task count and CPU/memory utilization
   - And metrics are updated in real-time (1-minute intervals)
   - And dashboards are accessible to the operations team

6. **AC6: CloudWatch Alarms Configuration**
   - Given monitoring is operational
   - When CloudWatch alarms are configured
   - Then the following alarms exist and are in OK state:
     - **Error Rate Alarm**: Triggers if API error rate >5% for 5 consecutive minutes
     - **Response Time Alarm**: Triggers if API p95 response time >10 seconds for 5 minutes
     - **Database Connection Alarm**: Triggers if connection pool utilization >80%
     - **ECS Health Alarm**: Triggers if unhealthy task count >0 for 2 minutes
   - And alarm notifications are sent to SNS topic (email/Slack)
   - And alarm state changes are logged

7. **AC7: Environment Variables and Secrets Management**
   - Given the application requires configuration
   - When ECS tasks start
   - Then environment variables are loaded from:
     - ECS task definition (non-sensitive config)
     - AWS Secrets Manager (sensitive credentials)
   - And the following secrets are stored in Secrets Manager:
     - `DATABASE_URL` (RDS PostgreSQL connection string)
     - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
     - `CLEVER_CLIENT_ID` and `CLEVER_CLIENT_SECRET`
     - `SESSION_SECRET_KEY` (for session encryption)
   - And secrets are rotated automatically (90-day rotation policy)
   - And application code retrieves secrets at startup (not hardcoded)

8. **AC8: Database Migration Execution**
   - Given the database schema needs to be applied
   - When deployment occurs
   - Then Alembic database migrations run automatically before app deployment
   - And migrations are idempotent (safe to run multiple times)
   - And migration failures prevent deployment from proceeding
   - And a rollback plan is documented for failed migrations

9. **AC9: Production URL and SSL/TLS Configuration**
   - Given the application needs a secure URL
   - When users access the production domain
   - Then the application is accessible via HTTPS only (HTTP redirects to HTTPS)
   - And SSL/TLS certificate is valid (not expired, trusted CA)
   - And certificate auto-renewal is configured (AWS Certificate Manager)
   - And security headers are configured (HSTS, X-Frame-Options, CSP)

10. **AC10: Deployment Runbook Documentation**
    - Given the team needs to understand deployment
    - When deployment documentation is created
    - Then a runbook exists at `/docs/deployment-runbook.md` with:
      - Step-by-step deployment process
      - Rollback procedure for failed deployments
      - Environment variable reference
      - Troubleshooting guide for common issues
      - Smoke test execution instructions
    - And the runbook is tested by performing a deployment
    - And deployment steps are validated and accurate

## Tasks / Subtasks

- [ ] **Task 1: Create GitHub Actions Workflow File** (AC: 1)
  - [ ] Subtask 1.1: Create `.github/workflows/deploy-production.yml`
  - [ ] Subtask 1.2: Configure workflow trigger on push to `main` branch
  - [ ] Subtask 1.3: Add job: Run backend tests (`pytest` in Docker)
  - [ ] Subtask 1.4: Add job: Build Docker image for `api-service`
  - [ ] Subtask 1.5: Add job: Push Docker image to AWS ECR with tags (SHA, latest)
  - [ ] Subtask 1.6: Add job: Deploy to ECS Fargate (update service with new task definition)
  - [ ] Subtask 1.7: Add job: Run smoke tests (curl health endpoints, test OAuth redirects)
  - [ ] Subtask 1.8: Configure automatic rollback on smoke test failure
  - [ ] Subtask 1.9: Add AWS credentials configuration (GitHub Secrets)

- [ ] **Task 2: Configure AWS ECR Repository** (AC: 1)
  - [ ] Subtask 2.1: Create ECR repository: `plccoach/api-service`
  - [ ] Subtask 2.2: Configure image scanning on push (vulnerability detection)
  - [ ] Subtask 2.3: Set lifecycle policy (keep last 10 images, delete old)
  - [ ] Subtask 2.4: Document ECR repository URL in deployment runbook

- [ ] **Task 3: Create ECS Task Definition** (AC: 1, 7)
  - [ ] Subtask 3.1: Create task definition JSON for `plccoach-api-task`
  - [ ] Subtask 3.2: Configure container definition with image from ECR
  - [ ] Subtask 3.3: Set resource limits (CPU: 512, Memory: 1024 MB)
  - [ ] Subtask 3.4: Configure port mappings (8000 for API)
  - [ ] Subtask 3.5: Add environment variables for non-sensitive config
  - [ ] Subtask 3.6: Add secrets from AWS Secrets Manager (DATABASE_URL, OAuth keys)
  - [ ] Subtask 3.7: Configure CloudWatch log group for container logs
  - [ ] Subtask 3.8: Add health check command (`CMD-SHELL, curl -f http://localhost:8000/health || exit 1`)

- [ ] **Task 4: Configure ECS Service with Blue-Green Deployment** (AC: 1)
  - [ ] Subtask 4.1: Create ECS service: `plccoach-api-service`
  - [ ] Subtask 4.2: Configure desired task count (2 for redundancy)
  - [ ] Subtask 4.3: Attach to Application Load Balancer target group
  - [ ] Subtask 4.4: Enable blue-green deployment with CodeDeploy
  - [ ] Subtask 4.5: Configure deployment circuit breaker (auto-rollback on failure)
  - [ ] Subtask 4.6: Set deployment configuration (min healthy: 100%, max: 200%)

- [ ] **Task 5: Frontend Build and S3 Deployment** (AC: 2)
  - [ ] Subtask 5.1: Add frontend build step to GitHub Actions workflow
  - [ ] Subtask 5.2: Run `npm ci && npm run build` in `frontend/` directory
  - [ ] Subtask 5.3: Create S3 bucket: `plccoach-frontend-production`
  - [ ] Subtask 5.4: Configure S3 bucket for static website hosting
  - [ ] Subtask 5.5: Upload build output (`frontend/dist/`) to S3 bucket
  - [ ] Subtask 5.6: Set S3 object permissions (public read for static files)
  - [ ] Subtask 5.7: Configure S3 bucket policy for CloudFront access

- [ ] **Task 6: Configure CloudFront Distribution** (AC: 2, 9)
  - [ ] Subtask 6.1: Create CloudFront distribution with S3 origin
  - [ ] Subtask 6.2: Configure custom domain (e.g., plccoach.example.com)
  - [ ] Subtask 6.3: Attach SSL/TLS certificate from AWS Certificate Manager
  - [ ] Subtask 6.4: Configure default root object (`index.html`)
  - [ ] Subtask 6.5: Configure error pages (404 → index.html for client-side routing)
  - [ ] Subtask 6.6: Enable compression (Gzip)
  - [ ] Subtask 6.7: Add CloudFront invalidation step to CI/CD pipeline (`/*` path)
  - [ ] Subtask 6.8: Configure security headers (HSTS, X-Frame-Options, CSP)

- [ ] **Task 7: Configure AWS Secrets Manager** (AC: 7)
  - [ ] Subtask 7.1: Create secret: `plccoach/production/database`
  - [ ] Subtask 7.2: Store DATABASE_URL in secret
  - [ ] Subtask 7.3: Create secret: `plccoach/production/google-oauth`
  - [ ] Subtask 7.4: Store GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
  - [ ] Subtask 7.5: Create secret: `plccoach/production/clever-sso`
  - [ ] Subtask 7.6: Store CLEVER_CLIENT_ID and CLEVER_CLIENT_SECRET
  - [ ] Subtask 7.7: Create secret: `plccoach/production/session`
  - [ ] Subtask 7.8: Generate and store SESSION_SECRET_KEY (random 64-char string)
  - [ ] Subtask 7.9: Configure 90-day automatic rotation policy
  - [ ] Subtask 7.10: Grant ECS task execution role permissions to read secrets

- [ ] **Task 8: Database Migration Automation** (AC: 8)
  - [ ] Subtask 8.1: Create migration script: `scripts/run-migrations.sh`
  - [ ] Subtask 8.2: Script runs `alembic upgrade head` using DATABASE_URL from Secrets Manager
  - [ ] Subtask 8.3: Add migration job to GitHub Actions (runs before ECS deployment)
  - [ ] Subtask 8.4: Configure migration job to fail pipeline if migrations fail
  - [ ] Subtask 8.5: Test idempotency (run migrations twice, should succeed)
  - [ ] Subtask 8.6: Document rollback procedure (`alembic downgrade -1`)

- [ ] **Task 9: CloudWatch Dashboards Setup** (AC: 5)
  - [ ] Subtask 9.1: Create CloudWatch dashboard: `PLC-Coach-Production`
  - [ ] Subtask 9.2: Add widget: API request count metric (ALB RequestCount)
  - [ ] Subtask 9.3: Add widget: API error rate (ALB 4XXCount + 5XXCount / RequestCount)
  - [ ] Subtask 9.4: Add widget: API response time (ALB TargetResponseTime p50, p95, p99)
  - [ ] Subtask 9.5: Add widget: Database connections (RDS DatabaseConnections metric)
  - [ ] Subtask 9.6: Add widget: ECS task count and CPU/memory utilization
  - [ ] Subtask 9.7: Set time range to 1 hour, auto-refresh every 1 minute

- [ ] **Task 10: CloudWatch Alarms Configuration** (AC: 6)
  - [ ] Subtask 10.1: Create SNS topic: `plccoach-production-alerts`
  - [ ] Subtask 10.2: Subscribe email address to SNS topic
  - [ ] Subtask 10.3: Create alarm: `API-Error-Rate-High` (>5% for 5 minutes)
  - [ ] Subtask 10.4: Create alarm: `API-Response-Time-High` (p95 >10s for 5 minutes)
  - [ ] Subtask 10.5: Create alarm: `Database-Connections-High` (>80% pool utilization)
  - [ ] Subtask 10.6: Create alarm: `ECS-Unhealthy-Tasks` (unhealthy count >0 for 2 minutes)
  - [ ] Subtask 10.7: Test alarms by triggering condition (e.g., stop ECS task)
  - [ ] Subtask 10.8: Verify SNS notifications are received

- [ ] **Task 11: Health Check Endpoint Enhancement** (AC: 3)
  - [ ] Subtask 11.1: Open `api-service/app/routers/health.py`
  - [ ] Subtask 11.2: Update `GET /health` to include version (from environment variable)
  - [ ] Subtask 11.3: Update `GET /health` to include timestamp
  - [ ] Subtask 11.4: Return 503 Service Unavailable if critical dependencies are down
  - [ ] Subtask 11.5: Update `GET /ready` to test database connectivity (execute `SELECT 1`)
  - [ ] Subtask 11.6: Return 200 if database is reachable, 503 if not

- [ ] **Task 12: Smoke Tests Implementation** (AC: 4)
  - [ ] Subtask 12.1: Create `scripts/smoke-tests.sh`
  - [ ] Subtask 12.2: Test 1: `curl GET /health` returns 200
  - [ ] Subtask 12.3: Test 2: `curl GET /ready` returns 200
  - [ ] Subtask 12.4: Test 3: `curl GET /auth/google/login` returns 302 redirect to Google
  - [ ] Subtask 12.5: Test 4: `curl GET /auth/clever/login` returns 302 redirect to Clever
  - [ ] Subtask 12.6: Test 5: Frontend URL loads successfully (HTTP 200)
  - [ ] Subtask 12.7: Add smoke tests to GitHub Actions workflow (post-deployment step)
  - [ ] Subtask 12.8: Configure pipeline to rollback if smoke tests fail

- [ ] **Task 13: OAuth Production Configuration** (AC: 4, 9)
  - [ ] Subtask 13.1: Register production OAuth redirect URIs with Google (https://plccoach.example.com/auth/google/callback)
  - [ ] Subtask 13.2: Register production OAuth redirect URIs with Clever
  - [ ] Subtask 13.3: Update backend config to use production redirect URIs (from environment variable)
  - [ ] Subtask 13.4: Test Google OAuth flow in production (manually log in)
  - [ ] Subtask 13.5: Test Clever SSO flow in production
  - [ ] Subtask 13.6: Verify session cookies are set with secure flag

- [ ] **Task 14: SSL/TLS Certificate Configuration** (AC: 9)
  - [ ] Subtask 14.1: Request SSL certificate from AWS Certificate Manager for production domain
  - [ ] Subtask 14.2: Validate domain ownership (DNS validation)
  - [ ] Subtask 14.3: Attach certificate to CloudFront distribution
  - [ ] Subtask 14.4: Attach certificate to Application Load Balancer (HTTPS listener)
  - [ ] Subtask 14.5: Configure ALB HTTP listener to redirect to HTTPS
  - [ ] Subtask 14.6: Enable auto-renewal for certificate
  - [ ] Subtask 14.7: Test HTTPS access (https://plccoach.example.com)

- [ ] **Task 15: Security Headers Configuration** (AC: 9)
  - [ ] Subtask 15.1: Configure CloudFront to add HTTP Strict Transport Security (HSTS) header
  - [ ] Subtask 15.2: Add X-Frame-Options: DENY header
  - [ ] Subtask 15.3: Add Content-Security-Policy header (restrict script sources)
  - [ ] Subtask 15.4: Add X-Content-Type-Options: nosniff header
  - [ ] Subtask 15.5: Test security headers using https://securityheaders.com

- [ ] **Task 16: Create Deployment Runbook** (AC: 10)
  - [ ] Subtask 16.1: Create `/docs/deployment-runbook.md`
  - [ ] Subtask 16.2: Document: Step-by-step deployment process (git push → CI/CD)
  - [ ] Subtask 16.3: Document: Rollback procedure (revert git commit, redeploy)
  - [ ] Subtask 16.4: Document: Environment variables reference (all required vars)
  - [ ] Subtask 16.5: Document: Troubleshooting guide (common deployment failures)
  - [ ] Subtask 16.6: Document: Smoke test execution instructions
  - [ ] Subtask 16.7: Document: How to access CloudWatch logs and dashboards
  - [ ] Subtask 16.8: Review runbook with team and validate accuracy

- [ ] **Task 17: Integration Testing - End-to-End Deployment** (AC: All)
  - [ ] Subtask 17.1: Trigger deployment by pushing to `main` branch
  - [ ] Subtask 17.2: Monitor GitHub Actions workflow execution
  - [ ] Subtask 17.3: Verify all jobs pass (tests, build, deploy, smoke tests)
  - [ ] Subtask 17.4: Verify ECS service shows new task definition running
  - [ ] Subtask 17.5: Access production URL and verify frontend loads
  - [ ] Subtask 17.6: Test Google login flow end-to-end
  - [ ] Subtask 17.7: Test Clever login flow end-to-end
  - [ ] Subtask 17.8: Verify CloudWatch metrics are populating
  - [ ] Subtask 17.9: Verify CloudWatch alarms are in OK state
  - [ ] Subtask 17.10: Review application logs in CloudWatch Logs

- [ ] **Task 18: Write Deployment Tests** (AC: All)
  - [ ] Subtask 18.1: Create `tests/deployment/test_smoke.py`
  - [ ] Subtask 18.2: Test health endpoint returns expected format
  - [ ] Subtask 18.3: Test ready endpoint confirms database connectivity
  - [ ] Subtask 18.4: Test OAuth redirect endpoints return 302
  - [ ] Subtask 18.5: Run tests in CI/CD pipeline post-deployment

## Dev Notes

### Learnings from Previous Story

**From Story 1.8: User Profile & Role Management (Status: review)**

- **Docker-based Development:**
  - All development and testing done within Docker containers
  - `docker-compose up -d` to start services
  - `docker-compose exec api pytest` to run tests
  - **THIS STORY EXTENDS**: Add production Docker build to CI/CD pipeline

- **Testing Infrastructure:**
  - 47 tests passing (28 regression + 19 Story 1.8)
  - pytest configured in `api-service/tests/`
  - Test fixtures in `conftest.py`
  - **THIS STORY USES**: Existing test suite in CI/CD pipeline (must pass before deploy)

- **Backend Service Ready:**
  - FastAPI application structure complete
  - Health endpoints exist: `/health`, `/ready`
  - **THIS STORY ENHANCES**: Add version info and improved health checks

- **Database Migrations:**
  - Alembic configured for database migrations
  - Migrations created in Story 1.2
  - **THIS STORY AUTOMATES**: Migration execution in deployment pipeline

- **Frontend Build:**
  - Vite configured for production builds
  - `npm run build` creates static files in `frontend/dist/`
  - **THIS STORY DEPLOYS**: Frontend static files to S3 + CloudFront

- **Authentication Ready:**
  - Google OIDC and Clever SSO fully implemented
  - OAuth callback URLs configured for local development
  - **THIS STORY CONFIGURES**: Production OAuth redirect URIs

- **Environment Variables:**
  - Local development uses `.env` files
  - Config loaded via `app/config.py`
  - **THIS STORY IMPLEMENTS**: AWS Secrets Manager for production secrets

[Source: docs/scrum/stories/1-8-user-profile-role-management.md#Dev-Agent-Record]

### Architecture & Deployment Patterns

**Blue-Green Deployment Strategy:**
- AWS CodeDeploy manages traffic shifting
- New task definition (green) deployed alongside old (blue)
- Health checks pass → traffic shifts to green
- Health checks fail → rollback to blue
- Zero-downtime deployments

**Infrastructure as Code:**
- ECS task definitions in JSON
- CloudFormation/Terraform for infrastructure (from Story 1.1)
- GitHub Actions workflows in YAML
- Versioned and tracked in git

**Secrets Management:**
- AWS Secrets Manager for sensitive config
- ECS task execution role has read permissions
- Automatic rotation policies (90 days)
- Never commit secrets to git

**Monitoring Philosophy:**
- Proactive monitoring (dashboards + alarms)
- Metrics: Golden Signals (latency, traffic, errors, saturation)
- Alerts route to SNS → Email/Slack
- CloudWatch Logs for debugging

**CI/CD Pipeline Stages:**
1. Test (pytest must pass)
2. Build (Docker images)
3. Push (to ECR)
4. Migrate (database schema)
5. Deploy (ECS service update)
6. Smoke Test (validate deployment)
7. Rollback (if smoke tests fail)

### Project Structure Notes

**Files to Create:**
- `.github/workflows/deploy-production.yml` - GitHub Actions workflow
- `scripts/run-migrations.sh` - Database migration script
- `scripts/smoke-tests.sh` - Post-deployment validation
- `docs/deployment-runbook.md` - Deployment documentation
- `tests/deployment/test_smoke.py` - Deployment tests
- `infrastructure/ecs-task-definition.json` - ECS task definition

**Files to Modify:**
- `api-service/app/routers/health.py` - Enhanced health checks
- `api-service/Dockerfile` - Production-optimized Docker build (if needed)
- `frontend/vite.config.ts` - Production build configuration

**AWS Resources to Configure:**
- ECR repository: `plccoach/api-service`
- ECS task definition: `plccoach-api-task`
- ECS service: `plccoach-api-service`
- S3 bucket: `plccoach-frontend-production`
- CloudFront distribution
- Secrets Manager secrets (4 secrets)
- CloudWatch dashboard: `PLC-Coach-Production`
- CloudWatch alarms (4 alarms)
- SNS topic: `plccoach-production-alerts`
- ACM certificate for domain

**Environment Variables Required:**
- `DATABASE_URL` (from Secrets Manager)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (from Secrets Manager)
- `CLEVER_CLIENT_ID`, `CLEVER_CLIENT_SECRET` (from Secrets Manager)
- `SESSION_SECRET_KEY` (from Secrets Manager)
- `ENVIRONMENT` (production)
- `APP_VERSION` (git SHA)
- `OAUTH_REDIRECT_BASE_URL` (https://plccoach.example.com)

### References

- [Source: docs/epics/epic-1-foundation-authentication.md#Story-1.9]
- [Infrastructure Plan: Story 1.1 notes (if documented)]
- [Database Schema: docs/scrum/stories/1-2-database-schema-creation.md]
- [Backend Health Endpoints: api-service/app/routers/health.py]
- [Frontend Build: frontend/package.json scripts]
- GitHub Actions Docs: https://docs.github.com/en/actions
- AWS ECS Blue-Green: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html
- AWS Secrets Manager: https://docs.aws.amazon.com/secretsmanager/
- CloudWatch Alarms: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html

## Dev Agent Record

### Context Reference

- docs/scrum/stories/1-9-deployment-production-readiness.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

### Completion Notes List

### File List
