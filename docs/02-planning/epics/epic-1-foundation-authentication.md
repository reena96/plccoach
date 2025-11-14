# Epic 1: Foundation & Authentication

**Author:** Reena
**Date:** 2025-11-12
**Duration:** 2-3 weeks
**Project:** AI Powered PLC at Work Virtual Coach

---

## Epic Goal

Establish secure infrastructure foundation and user authentication system that enables educators to access the PLC Coach through Google or Clever SSO with automatic user provisioning and role-based access control.

**Business Value:** Users can securely log in and access the application with zero manual account creation. Infrastructure foundation enables all subsequent development.

---

## Stories

### Story 1.1: Project Infrastructure Setup

**As a** DevOps engineer,
**I want** to provision AWS infrastructure and set up deployment pipeline,
**So that** the team can deploy and run the application in a production-ready environment.

**Acceptance Criteria:**

**Given** we need a production-ready cloud environment
**When** infrastructure is provisioned
**Then** the following AWS resources are created and configured:
- VPC with public and private subnets (10.0.0.0/16)
- ECS Fargate cluster for container orchestration
- RDS PostgreSQL 15 instance (Multi-AZ for production)
- S3 buckets (content, exports, backups)
- CloudFront CDN for frontend assets
- Application Load Balancer with SSL/TLS
- CloudWatch log groups and basic metrics
- Secrets Manager for credentials

**And** a CI/CD pipeline using GitHub Actions is configured with:
- Automated builds on push to main branch
- Docker image creation and push to ECR
- Automated deployment to ECS Fargate
- Blue-green deployment strategy

**And** all infrastructure is defined as code (Terraform or CloudFormation)

**And** basic monitoring and alerting is configured in CloudWatch

**Prerequisites:** None (foundation story)

**Technical Notes:**
- Use AWS CDK or Terraform for infrastructure as code
- Configure VPC with separate public/private subnets
- Enable encryption at rest (AWS KMS) for RDS and S3
- Set up CloudWatch log retention (90 days)
- Configure security groups with least privilege access
- Document infrastructure setup in `/docs/infrastructure.md`
- Reference: TECHNICAL_ARCHITECTURE.md Section 7 (Infrastructure & Deployment)

---

### Story 1.2: Database Schema Creation

**As a** backend developer,
**I want** to create the initial PostgreSQL database schema,
**So that** the application can store users, sessions, conversations, and messages.

**Acceptance Criteria:**

**Given** the RDS PostgreSQL instance is running
**When** database migrations are executed
**Then** the following tables are created with proper indexes:
- `users` table with fields: id, email, name, role, organization_id, sso_provider, sso_id, created_at, last_login
- `sessions` table with fields: id, user_id, expires_at, created_at, last_accessed_at
- `conversations` table with fields: id, user_id, title, status, created_at, updated_at, share_token, share_enabled
- `messages` table with fields: id, conversation_id, role, content, citations (JSONB), domains, feedback_score, input_tokens, output_tokens, cost_usd, created_at

**And** the `pgvector` extension is installed for vector embeddings

**And** all appropriate indexes are created:
- `idx_users_email` on users(email)
- `idx_sessions_id` on sessions(id) WHERE expires_at > NOW()
- `idx_conversations_user` on conversations(user_id)
- `idx_messages_conversation` on messages(conversation_id, created_at)

**And** database migration scripts are created using Alembic

**And** a rollback procedure is documented

**Prerequisites:** Story 1.1 (infrastructure must exist)

**Technical Notes:**
- Use Alembic for database migrations
- Enable JSONB for flexible citation storage
- Configure connection pooling (20 connections per service)
- Set up automated daily snapshots with 30-day retention
- Reference: TECHNICAL_ARCHITECTURE.md Section 3.1 (Database Schema)
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #3 (PostgreSQL choice)

---

### Story 1.3: Backend API Service Foundation

**As a** backend developer,
**I want** to create the FastAPI application structure,
**So that** we have a foundation for building API endpoints.

**Acceptance Criteria:**

**Given** we need a Python backend service
**When** the FastAPI application is created
**Then** the following structure exists:
```
api-service/
├── routers/
│   ├── auth.py
│   ├── conversations.py
│   ├── messages.py
│   └── health.py
├── services/
│   ├── auth_service.py
│   └── database.py
├── models/
│   ├── user.py
│   ├── session.py
│   └── conversation.py
├── main.py
├── config.py
└── requirements.txt
```

**And** health check endpoints are implemented:
- `GET /health` returns 200 OK with service status
- `GET /ready` returns 200 when database is accessible

**And** database connection pooling is configured (SQLAlchemy)

**And** CORS middleware is configured for frontend access

**And** structured logging is implemented (JSON format to CloudWatch)

**And** the service runs in a Docker container

**And** environment variables are loaded from AWS Secrets Manager

**Prerequisites:** Story 1.2 (database schema must exist)

**Technical Notes:**
- Python 3.11+ with FastAPI
- Use SQLAlchemy 2.0 for ORM
- Configure Uvicorn as ASGI server
- Add request ID middleware for tracing
- Set up OpenAPI/Swagger docs at `/docs`
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.2 (Backend Services)

---

### Story 1.4: Google OIDC Authentication

**As an** educator,
**I want** to log in using my Google account,
**So that** I can access the PLC Coach without creating a separate account.

**Acceptance Criteria:**

**Given** I am a new user with a Google account
**When** I click "Login with Google" on the login page
**Then** I am redirected to Google's OAuth consent screen

**And** after granting consent, I am redirected back to the application

**And** a new user record is created in the database (JIT provisioning) with:
- Email from Google profile
- Name from Google profile
- Role defaulted to 'educator'
- sso_provider = 'google'
- sso_id = Google user ID

**And** a secure session is created in the sessions table

**And** a session cookie is set (httpOnly, secure, sameSite=strict)

**And** I am redirected to the dashboard

**Given** I am an existing user
**When** I log in with Google
**Then** my existing user record is updated with last_login timestamp

**And** a new session is created

**Prerequisites:** Story 1.3 (backend API foundation must exist)

**Technical Notes:**
- Use authlib library for OAuth 2.0 / OIDC
- Store Google Client ID and Secret in AWS Secrets Manager
- Implement CSRF protection with state parameter
- Session expiry: 24 hours with auto-refresh on activity
- Session timeout after 30 minutes of inactivity
- Reference: TECHNICAL_ARCHITECTURE.md Section 6.2 (Authentication)
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #6 (Server-side sessions)

---

### Story 1.5: Clever SSO Authentication

**As an** educator at a school using Clever,
**I want** to log in using Clever SSO,
**So that** I can access the PLC Coach with my school's single sign-on system.

**Acceptance Criteria:**

**Given** I am a user from a Clever-enabled school
**When** I click "Login with Clever" on the login page
**Then** I am redirected to Clever's OAuth authorization page

**And** after authorizing, I am redirected back to the application

**And** a new user record is created (JIT provisioning) with:
- Email from Clever profile
- Name from Clever profile
- Role defaulted to 'educator'
- sso_provider = 'clever'
- sso_id = Clever user ID
- organization_id extracted from Clever district data (if available)

**And** a secure session is created

**And** I am redirected to the dashboard

**Given** Clever provides role information (district_admin, school_admin)
**When** a user logs in
**Then** their role is automatically set to 'admin' if they are a district or school admin

**Prerequisites:** Story 1.4 (Google authentication pattern established)

**Technical Notes:**
- Use Clever OAuth 2.0 API
- Store Clever Client ID and Secret in AWS Secrets Manager
- Extract organization/district data from Clever API
- Handle role mapping from Clever to PLC Coach roles
- Clever API documentation: https://dev.clever.com/docs
- Reference: PRD Section 6.1 (Authentication Requirements FR-1.2)

---

### Story 1.6: Session Management & Logout

**As a** logged-in user,
**I want** to log out and have my session invalidated,
**So that** my account is secure when I'm done using the application.

**Acceptance Criteria:**

**Given** I am logged in with an active session
**When** I click the "Logout" button
**Then** my session is deleted from the sessions table

**And** my session cookie is cleared

**And** I am redirected to the login page

**And** subsequent requests with the old session cookie are rejected with 401 Unauthorized

**Given** my session has been inactive for 30 minutes
**When** I make a request
**Then** my session is considered expired

**And** I receive a 401 Unauthorized response

**And** I am prompted to log in again

**Given** I have an active session
**When** I make a request
**Then** the last_accessed_at timestamp is updated

**And** my session expiry is extended

**Prerequisites:** Story 1.5 (authentication must be working)

**Technical Notes:**
- Implement session cleanup background job (delete expired sessions daily)
- Add session validation middleware to all protected endpoints
- Log all session creation and deletion events for audit
- Implement session refresh logic (extend expiry on activity)
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.2.1 (Session Management)

---

### Story 1.7: Frontend Application Shell

**As a** user,
**I want** a responsive web interface,
**So that** I can interact with the PLC Coach on desktop, tablet, or mobile.

**Acceptance Criteria:**

**Given** the frontend needs to be built
**When** the React application is created with Vite
**Then** the following structure exists:
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   └── Chat.tsx
│   ├── components/
│   │   ├── auth/
│   │   ├── shared/
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── auth.ts
│   ├── App.tsx
│   └── main.tsx
├── index.html
└── vite.config.ts
```

**And** Tailwind CSS is configured for styling

**And** React Router is configured for client-side routing

**And** React Query (@tanstack/react-query) is configured for API data fetching

**And** the login page displays:
- "Login with Google" button
- "Login with Clever" button
- Solution Tree branding

**And** protected routes redirect to login if not authenticated

**And** the application is responsive (mobile, tablet, desktop)

**And** the build output is static files that can be deployed to S3

**Prerequisites:** Story 1.3 (backend API must exist)

**Technical Notes:**
- Vite 5 + React 18
- Use Axios for HTTP client
- Implement authentication context with React Context
- Store session state in httpOnly cookies (handled by backend)
- Configure Vite proxy for local development
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.1 (Frontend Application)
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #1 (Vite + React choice)

---

### Story 1.8: User Profile & Role Management

**As a** logged-in user,
**I want** to view my profile information,
**So that** I can see my name, email, role, and organization.

**Acceptance Criteria:**

**Given** I am logged in
**When** I access the `/auth/me` endpoint
**Then** I receive my user profile with:
- id
- email
- name
- role (educator, coach, or admin)
- organization (if available)
- created_at
- last_login

**Given** I am an administrator
**When** I access the admin panel
**Then** I can view a list of all users

**And** I can change a user's role (educator → coach, coach → admin, etc.)

**And** the role change takes effect immediately for new sessions

**Given** a user's role is changed
**When** they make their next request
**Then** their permissions reflect the new role

**Prerequisites:** Story 1.6 (session management must be working)

**Technical Notes:**
- Implement `GET /auth/me` endpoint
- Implement `GET /admin/users` endpoint (admin only)
- Implement `PATCH /admin/users/:id` endpoint (admin only)
- Add role-based access control (RBAC) middleware
- Log all role changes for audit trail
- Reference: PRD Section 11 (User Roles & Permissions)

---

### Story 1.9: Deployment & Production Readiness

**As a** DevOps engineer,
**I want** to deploy the foundation services to production,
**So that** authentication and basic infrastructure are live and tested.

**Acceptance Criteria:**

**Given** all foundation stories are complete
**When** code is merged to main branch
**Then** GitHub Actions CI/CD pipeline:
- Runs unit tests (must pass)
- Builds Docker images for backend
- Pushes images to AWS ECR
- Deploys to ECS Fargate using blue-green strategy
- Runs smoke tests against deployed services

**And** the frontend is built and deployed to S3

**And** CloudFront distribution serves the frontend

**And** the application is accessible at the production URL

**And** health checks pass: `/health` and `/ready` return 200

**And** users can log in via Google and Clever SSO

**And** CloudWatch dashboards show:
- Request count
- Error rate
- Response time (p50, p95, p99)
- Database connection count

**And** CloudWatch alarms are configured for:
- Error rate >5% for 5 minutes
- API p95 response time >10 seconds

**Prerequisites:** All previous stories in Epic 1

**Technical Notes:**
- Test OAuth callbacks work in production environment
- Verify SSL/TLS certificates are valid
- Test session persistence across container restarts
- Document deployment process in runbook
- Set up staging environment for testing before production
- Reference: TECHNICAL_ARCHITECTURE.md Section 7.4 (CI/CD Pipeline)

---

## Epic Completion Criteria

- [ ] Users can log in with Google OIDC
- [ ] Users can log in with Clever SSO
- [ ] New users are auto-provisioned (JIT) with 'educator' role
- [ ] Sessions are secure (httpOnly cookies, server-side storage)
- [ ] Users can log out and sessions are invalidated
- [ ] Infrastructure is deployed on AWS (VPC, ECS, RDS, S3, CloudFront)
- [ ] CI/CD pipeline deploys automatically on merge to main
- [ ] Database schema is created with proper indexes
- [ ] Basic monitoring and alerting is operational
- [ ] Application is accessible and responsive on all devices

---

## Definition of Done

- All 9 stories completed and acceptance criteria met
- Unit tests written for authentication logic (>80% coverage)
- Integration tests verify OAuth flows end-to-end
- Security review completed (no critical vulnerabilities)
- Infrastructure documented in `/docs/infrastructure.md`
- Deployment runbook created
- Production deployment successful
- No critical or high-severity bugs

---

## Dependencies & Risks

**External Dependencies:**
- Google OAuth API availability
- Clever SSO API availability
- AWS service availability

**Risks:**
- OAuth configuration complexity (Mitigation: Test in staging first)
- Session management edge cases (Mitigation: Comprehensive testing)
- Infrastructure provisioning delays (Mitigation: Use IaC for repeatability)

**Next Epic:** Epic 2 - Core AI Coach (depends on authentication foundation)
