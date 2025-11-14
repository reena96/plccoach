# Epic 1 Manual Validation Guide

**Last Updated**: 2025-11-14
**Test Status**: ✅ 80/80 functional tests passing
**Epic Status**: Ready for manual validation

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Google OAuth credentials (already configured in .env)
- Clever OAuth credentials (already configured in .env)
- Ports 8000 (API) and 5433 (PostgreSQL) available

### 1. Start the System

```bash
# Navigate to api-service directory
cd /Users/reena/plccoach/api-service

# Start Docker services
docker-compose up -d

# Verify services are running
docker-compose ps
# Expected: Both 'api' and 'db' should be "Up" and healthy
```

**✅ Pass Criteria:**
- Both containers are running
- API shows "Up" (may show "unhealthy" initially, wait 30 seconds)
- Database shows "Up (healthy)"

---

## 2. Backend API Validation

### 2.1 Health Endpoints

```bash
# Test basic health
curl http://localhost:8000/api/health | python -m json.tool

# Expected output:
{
    "status": "healthy",
    "service": "PLC Coach API",
    "version": "0.1.0",
    "database": null
}

# Test database readiness
curl http://localhost:8000/api/ready | python -m json.tool

# Expected output:
{
    "status": "ready",
    "database": "connected"
}
```

**✅ Pass Criteria:**
- Health endpoint returns status "healthy"
- Ready endpoint returns database "connected"
- Both return HTTP 200

### 2.2 Run Full Test Suite

```bash
# Run all backend tests
docker-compose exec -T api pytest

# Expected output (last line):
# ================= 80 passed, 12 skipped, 22 warnings in ~1.20s ==================
```

**✅ Pass Criteria:**
- 80 tests pass
- 12 tests skipped (migration tests - this is expected)
- 0 failures
- 0 errors

### 2.3 Test Individual Modules

```bash
# Test Google OAuth
docker-compose exec -T api pytest tests/test_auth_google.py -v
# Expected: 12 passed

# Test Clever SSO
docker-compose exec -T api pytest tests/test_auth_clever.py -v
# Expected: 16 passed

# Test Session Management
docker-compose exec -T api pytest tests/test_session_management.py -v
# Expected: 17 passed

# Test Admin Endpoints
docker-compose exec -T api pytest tests/test_admin_users.py -v
# Expected: 12 passed
```

**✅ Pass Criteria:**
- All module-level tests pass
- No errors when running individually

---

## 3. Database Validation

### 3.1 Connect to Database

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d plccoach

# Inside psql, list tables:
\dt

# Expected tables:
# - users
# - sessions
# - conversations
# - messages
```

### 3.2 Verify Schema

```sql
-- Check users table structure
\d users

-- Expected columns:
-- - id (uuid, primary key)
-- - email (character varying, unique)
-- - name (character varying)
-- - role (character varying) with CHECK constraint
-- - organization_id (uuid, nullable)
-- - sso_provider (character varying)
-- - sso_id (character varying)
-- - created_at (timestamp with time zone)
-- - last_login (timestamp with time zone)

-- Check indexes
\di

-- Expected indexes on:
-- - users.email
-- - sessions.user_id
-- - conversations.user_id
-- - messages.conversation_id

-- Exit psql
\q
```

**✅ Pass Criteria:**
- All 4 tables exist
- All columns present with correct types
- All indexes created
- Foreign key relationships configured

---

## 4. Authentication Flow Validation

### 4.1 Google OAuth Flow (Manual Browser Test)

**Note**: This requires actual Google OAuth credentials and a browser.

```bash
# Start frontend dev server (in new terminal)
cd /Users/reena/plccoach/frontend
npm run dev

# Open browser to http://localhost:5173
```

**Manual Steps:**

1. **Navigate to Login Page**
   - Open http://localhost:5173
   - ✅ See "Login with Google" button
   - ✅ See "Login with Clever" button

2. **Initiate Google Login**
   - Click "Login with Google"
   - ✅ Redirected to Google OAuth consent screen
   - ✅ URL contains `accounts.google.com`

3. **Complete OAuth**
   - Select Google account
   - Grant permissions
   - ✅ Redirected back to http://localhost:5173/dashboard
   - ✅ See user name displayed in header

4. **Verify Session**
   - Check browser DevTools → Application → Cookies
   - ✅ Cookie named `plc_session` exists
   - ✅ Cookie has `HttpOnly` flag
   - ✅ Cookie has `SameSite=lax`

5. **Test Session Persistence**
   - Refresh the page (F5)
   - ✅ User remains logged in
   - ✅ User name still displayed

6. **Test /auth/me Endpoint**
   ```bash
   # Copy the session cookie value from DevTools
   curl -H "Cookie: plc_session=<session-id>" http://localhost:8000/auth/me | python -m json.tool

   # Expected output:
   {
       "id": "<uuid>",
       "email": "user@example.com",
       "name": "User Name",
       "role": "educator",
       "organization_id": null,
       "sso_provider": "google",
       "created_at": "2025-11-14T...",
       "last_login": "2025-11-14T..."
   }
   ```

7. **Test Logout**
   - Click "Logout" button
   - ✅ Redirected to login page
   - ✅ Session cookie deleted
   - ✅ Cannot access protected routes

**✅ Pass Criteria:**
- Complete OAuth flow works end-to-end
- Session cookie created with correct attributes
- Session persists across page refresh
- /auth/me returns correct user data
- Logout clears session

### 4.2 Clever OAuth Flow

Repeat the same steps as 4.1, but:
- Click "Login with Clever" instead
- Use Clever credentials
- Verify role mapping works (district_admin → admin, teacher → educator)

**✅ Pass Criteria:**
- Same as Google OAuth
- Role mapping correct based on Clever user type

---

## 5. Role-Based Access Control

### 5.1 Create Test Users

```bash
# Connect to database
docker-compose exec db psql -U postgres -d plccoach

# Create admin user
INSERT INTO users (id, email, name, role, sso_provider, sso_id, created_at, last_login)
VALUES (
  gen_random_uuid(),
  'admin@test.com',
  'Test Admin',
  'admin',
  'google',
  'google-admin-123',
  NOW(),
  NOW()
);

# Create educator user
INSERT INTO users (id, email, name, role, sso_provider, sso_id, created_at, last_login)
VALUES (
  gen_random_uuid(),
  'educator@test.com',
  'Test Educator',
  'educator',
  'google',
  'google-educator-123',
  NOW(),
  NOW()
);

# Create sessions for testing
-- Note the user IDs from above
INSERT INTO sessions (id, user_id, expires_at, last_accessed_at, created_at)
VALUES (
  gen_random_uuid(),
  (SELECT id FROM users WHERE email = 'admin@test.com'),
  NOW() + INTERVAL '24 hours',
  NOW(),
  NOW()
);

INSERT INTO sessions (id, user_id, expires_at, last_accessed_at, created_at)
VALUES (
  gen_random_uuid(),
  (SELECT id FROM users WHERE email = 'educator@test.com'),
  NOW() + INTERVAL '24 hours',
  NOW(),
  NOW()
);

-- Get session IDs
SELECT id, user_id FROM sessions WHERE user_id IN (
  SELECT id FROM users WHERE email IN ('admin@test.com', 'educator@test.com')
);

\q
```

### 5.2 Test Admin Endpoints

```bash
# Copy admin session ID from above
ADMIN_SESSION="<admin-session-id>"
EDUCATOR_SESSION="<educator-session-id>"

# Test admin can list users
curl -H "Cookie: plc_session=$ADMIN_SESSION" http://localhost:8000/admin/users | python -m json.tool

# Expected: JSON array of users
# Status: 200 OK

# Test educator CANNOT list users
curl -i -H "Cookie: plc_session=$EDUCATOR_SESSION" http://localhost:8000/admin/users

# Expected: 403 Forbidden
# Response should contain "Admin access required"
```

**✅ Pass Criteria:**
- Admin can access /admin/users
- Educator gets 403 Forbidden on /admin/users
- Error messages are informative

### 5.3 Test Manual Session Cleanup (Admin Only)

```bash
# Test admin can trigger cleanup
curl -X POST -H "Cookie: plc_session=$ADMIN_SESSION" \
  http://localhost:8000/api/admin/cleanup-sessions | python -m json.tool

# Expected output:
{
    "status": "completed",
    "sessions_deleted": <number>,
    "message": "Successfully deleted <number> expired sessions"
}

# Test educator CANNOT trigger cleanup
curl -i -X POST -H "Cookie: plc_session=$EDUCATOR_SESSION" \
  http://localhost:8000/api/admin/cleanup-sessions

# Expected: 403 Forbidden
```

**✅ Pass Criteria:**
- Admin can trigger session cleanup
- Educator gets 403 Forbidden
- Cleanup returns count of deleted sessions

---

## 6. Session Management

### 6.1 Test Session Expiry

```bash
# Create test session that expires in 5 seconds
docker-compose exec db psql -U postgres -d plccoach -c "
INSERT INTO sessions (id, user_id, expires_at, last_accessed_at, created_at)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  (SELECT id FROM users LIMIT 1),
  NOW() + INTERVAL '5 seconds',
  NOW(),
  NOW()
);
"

# Immediately test with this session
curl -H "Cookie: plc_session=11111111-1111-1111-1111-111111111111" \
  http://localhost:8000/auth/me

# Expected: 200 OK with user data

# Wait 6 seconds
sleep 6

# Try again
curl -i -H "Cookie: plc_session=11111111-1111-1111-1111-111111111111" \
  http://localhost:8000/auth/me

# Expected: 401 Unauthorized
# Message: "Session expired"
```

**✅ Pass Criteria:**
- Valid session returns user data
- Expired session returns 401
- Error message indicates expiry

### 6.2 Test Inactivity Timeout

```bash
# Create session that was last accessed > 30 minutes ago
docker-compose exec db psql -U postgres -d plccoach -c "
INSERT INTO sessions (id, user_id, expires_at, last_accessed_at, created_at)
VALUES (
  '22222222-2222-2222-2222-222222222222',
  (SELECT id FROM users LIMIT 1),
  NOW() + INTERVAL '24 hours',
  NOW() - INTERVAL '31 minutes',
  NOW() - INTERVAL '31 minutes'
);
"

# Try to use this session
curl -i -H "Cookie: plc_session=22222222-2222-2222-2222-222222222222" \
  http://localhost:8000/auth/me

# Expected: 401 Unauthorized
# Message: "Session expired due to inactivity"
```

**✅ Pass Criteria:**
- Inactive sessions (>30 min) are rejected
- Error message indicates inactivity

### 6.3 Test Background Cleanup

```bash
# Check cleanup schedule
docker-compose exec api python -c "
from app.config import settings
print(f'Cleanup scheduled for: {settings.cleanup_schedule_hour}:00 UTC daily')
"

# Manually trigger cleanup (as admin)
curl -X POST -H "Cookie: plc_session=$ADMIN_SESSION" \
  http://localhost:8000/api/admin/cleanup-sessions | python -m json.tool

# Verify expired sessions were deleted
docker-compose exec db psql -U postgres -d plccoach -c "
SELECT COUNT(*) FROM sessions WHERE expires_at < NOW();
"
# Expected: 0 (all expired sessions deleted)
```

**✅ Pass Criteria:**
- Cleanup job is scheduled (default 2:00 AM UTC)
- Manual cleanup removes expired sessions
- Database query shows 0 expired sessions after cleanup

---

## 7. Frontend Validation

### 7.1 Build Frontend

```bash
cd /Users/reena/plccoach/frontend

# Install dependencies (if not already done)
npm install

# Build production bundle
npm run build

# Expected output:
# ✓ 144 modules transformed.
# dist/index.html                   ~0.46 kB
# dist/assets/index-*.css          ~15.59 kB
# dist/assets/index-*.js          ~295.67 kB
# ✓ built in ~658ms
```

**✅ Pass Criteria:**
- Build completes without errors
- dist/ folder created
- JavaScript bundle < 300 kB
- No TypeScript errors

### 7.2 Run Dev Server

```bash
# Start dev server
npm run dev

# Expected output:
#   VITE v7.x.x  ready in xxx ms
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
```

**✅ Pass Criteria:**
- Dev server starts without errors
- Accessible at http://localhost:5173
- Hot reload works

---

## 8. Integration Testing

### 8.1 Complete End-to-End User Flow

This simulates a complete real-world scenario:

1. **Start Fresh**
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d

   # Wait for services to be ready
   sleep 5
   ```

2. **First User Logs In (Google)**
   - Open http://localhost:5173
   - Click "Login with Google"
   - Complete OAuth
   - ✅ User created with role="educator"
   - ✅ Session created
   - ✅ Redirected to dashboard

3. **Verify Database**
   ```bash
   docker-compose exec db psql -U postgres -d plccoach -c "SELECT email, role, sso_provider FROM users;"
   # ✅ See 1 user with google provider

   docker-compose exec db psql -U postgres -d plccoach -c "SELECT COUNT(*) FROM sessions;"
   # ✅ See 1 active session
   ```

4. **User Navigates Around**
   - View profile (GET /auth/me)
   - ✅ Returns correct user data
   - Refresh page multiple times
   - ✅ Session persists

5. **User Logs Out**
   - Click logout
   - ✅ Redirected to login
   - ✅ Session deleted from database

6. **Same User Logs In Again**
   - Click "Login with Google"
   - Use same Google account
   - ✅ No duplicate user created
   - ✅ last_login timestamp updated
   - ✅ New session created

7. **Verify Database Again**
   ```bash
   docker-compose exec db psql -U postgres -d plccoach -c "SELECT COUNT(*) FROM users;"
   # ✅ Still only 1 user (not duplicated)

   docker-compose exec db psql -U postgres -d plccoach -c "SELECT email, last_login FROM users;"
   # ✅ last_login is recent
   ```

**✅ Pass Criteria:**
- Complete flow works without errors
- No duplicate users created
- Sessions properly created and deleted
- last_login timestamp updated on re-login

---

## 9. Error Handling

### 9.1 Invalid Session ID

```bash
curl -i -H "Cookie: plc_session=invalid-uuid-format" http://localhost:8000/auth/me
# Expected: 401 Unauthorized
```

### 9.2 Nonexistent Session

```bash
curl -i -H "Cookie: plc_session=99999999-9999-9999-9999-999999999999" http://localhost:8000/auth/me
# Expected: 401 Unauthorized
```

### 9.3 Missing Session Cookie

```bash
curl -i http://localhost:8000/auth/me
# Expected: 401 Unauthorized
```

### 9.4 Database Connection Failure

```bash
# Stop database
docker-compose stop db

# Try health check
curl -i http://localhost:8000/api/ready
# Expected: 503 Service Unavailable
# Message: "Database not available"

# Restart database
docker-compose start db
```

**✅ Pass Criteria:**
- All error scenarios return appropriate HTTP status codes
- Error messages are informative but not revealing sensitive info
- System recovers when database comes back online

---

## 10. Performance & Monitoring

### 10.1 Request ID Tracking

```bash
# Make request and check for request ID
curl -i http://localhost:8000/api/health | grep -i "x-request-id"

# Expected: x-request-id: <uuid>
```

### 10.2 CORS Headers

```bash
# Test CORS preflight
curl -i -X OPTIONS -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/auth/logout

# Expected headers:
# access-control-allow-origin: http://localhost:3000
# access-control-allow-credentials: true
# access-control-allow-methods: *
```

### 10.3 Check Logs

```bash
# View API logs
docker-compose logs api --tail=50

# Expected to see:
# - Structured JSON logs
# - Request ID in each log entry
# - No errors or warnings (except expected test data)
```

**✅ Pass Criteria:**
- Request IDs present in all responses
- CORS headers configured correctly
- Logs are structured and informative

---

## Summary Checklist

Use this final checklist to confirm everything is working:

### Infrastructure
- [ ] Docker containers running (api, db)
- [ ] Health endpoint returns "healthy"
- [ ] Ready endpoint shows database "connected"
- [ ] All 80 functional tests passing

### Database
- [ ] All 4 tables exist (users, sessions, conversations, messages)
- [ ] All indexes created
- [ ] Foreign keys configured
- [ ] Check constraints working

### Google OAuth
- [ ] Login flow redirects to Google
- [ ] Callback creates/updates user
- [ ] Session cookie created with HttpOnly
- [ ] Session persists across refresh
- [ ] Logout works

### Clever SSO
- [ ] Login flow redirects to Clever
- [ ] Role mapping works (district_admin → admin)
- [ ] Session management same as Google

### Role-Based Access Control
- [ ] Admin can access /admin/users
- [ ] Educator gets 403 on /admin/users
- [ ] Admin can trigger session cleanup
- [ ] Educator gets 403 on cleanup

### Session Management
- [ ] Sessions expire after 24 hours
- [ ] Inactive sessions (>30 min) rejected
- [ ] Session cleanup removes expired sessions
- [ ] Background cleanup scheduled

### Frontend
- [ ] Builds successfully (<300 KB)
- [ ] Dev server runs
- [ ] Login/logout UI works
- [ ] No TypeScript errors

### Error Handling
- [ ] Invalid session returns 401
- [ ] Missing session returns 401
- [ ] Database down returns 503
- [ ] Error messages informative

### Monitoring
- [ ] Request IDs in all responses
- [ ] CORS headers correct
- [ ] Structured logging working

---

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "connection pool exhausted"
- **Solution**: Restart containers: `docker-compose restart`

**Issue**: API shows "unhealthy" in docker-compose ps
- **Solution**: Wait 30 seconds, healthcheck interval is 10s

**Issue**: Frontend build fails
- **Solution**: `cd frontend && rm -rf node_modules && npm install`

**Issue**: OAuth redirect fails
- **Solution**: Check .env has correct GOOGLE_CLIENT_ID and CLEVER_CLIENT_ID

**Issue**: Database connection fails
- **Solution**: Ensure port 5433 is not in use: `lsof -i :5433`

---

## Next Steps

After successful validation:

1. **Document any issues found** in GitHub issues
2. **Update Epic 1 status** to "Validated"
3. **Begin Epic 2** (Core AI Coach) planning
4. **Deploy to staging** environment (Story 1.9)

---

**Validation Sign-off:**

- [ ] All automated tests passing (80/80)
- [ ] All manual validation steps completed
- [ ] No critical issues found
- [ ] Documentation updated
- [ ] Ready for production deployment

**Validated by**: ___________________
**Date**: ___________________
**Notes**: ___________________
