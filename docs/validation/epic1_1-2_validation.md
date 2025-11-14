# Story 1.2 Validation Guide: Database Schema Creation

**Story:** 1.2 - Database Schema Creation
**Epic:** 1 - Foundation & Authentication
**Status:** Ready for Validation
**Date:** 2025-11-13

---

## 30-Second Quick Test

```bash
# 1. Set up local test database
docker run -d --name plccoach-db-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=plccoach \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# 2. Apply migrations
cd api-service
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/plccoach"
alembic upgrade head

# 3. Verify success
alembic current
# Should show: 001_initial_schema (head)

# 4. Test rollback
alembic downgrade base
alembic upgrade head
```

**Expected Result:** All commands succeed, migrations apply and rollback cleanly.

---

## Automated Test Results

### Unit Tests

```bash
cd api-service
pytest tests/migrations/test_initial_schema.py -v
```

**Coverage:**
- ✅ All tables created (users, sessions, conversations, messages)
- ✅ pgvector extension installed
- ✅ Table structures validated (columns, types, constraints)
- ✅ Indexes created (email, sessions, conversations, messages)
- ✅ Foreign key constraints working
- ✅ CASCADE delete behavior verified
- ✅ JSONB citations field validated
- ✅ Check constraints on role enums
- ✅ Migration rollback successful

**Test Count:** 11 tests
**Expected Pass Rate:** 100%

**Note:** Tests require local PostgreSQL with pgvector. If database not available, tests will be skipped with clear message.

### Integration Tests

```bash
# Run all tests with coverage
pytest --cov=. --cov-report=term-missing
```

**Expected Coverage:** >90% for database models and migration files

---

## Manual Validation Steps

### 1. Local PostgreSQL Validation

#### Setup
```bash
# Start PostgreSQL with pgvector
docker run -d --name plccoach-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=plccoach \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# Configure environment
cd api-service
cp .env.example .env
# Edit .env: DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/plccoach
```

#### Apply Migrations
```bash
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema, Initial database schema
```

#### Verify Tables
```bash
psql postgresql://postgres:postgres@localhost:5432/plccoach

# In psql:
\dt
```

**Expected Tables:**
```
 public | alembic_version | table | postgres
 public | conversations   | table | postgres
 public | messages        | table | postgres
 public | sessions        | table | postgres
 public | users           | table | postgres
```

#### Verify pgvector Extension
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

**Expected:** One row showing vector extension installed

#### Verify Indexes
```sql
SELECT indexname FROM pg_indexes
WHERE tablename IN ('users', 'sessions', 'conversations', 'messages')
ORDER BY tablename, indexname;
```

**Expected Indexes:**
- conversations_pkey
- idx_conversations_share_token
- idx_conversations_user
- messages_pkey
- idx_messages_conversation
- sessions_pkey
- idx_sessions_user_id
- users_pkey
- idx_users_email
- uq_users_email

#### Test CASCADE Delete
```sql
-- Create test data
INSERT INTO users (id, email, name, role)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'test@example.com', 'Test User', 'educator');

INSERT INTO sessions (id, user_id, expires_at)
VALUES ('b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', NOW() + INTERVAL '1 day');

-- Verify session exists
SELECT * FROM sessions WHERE user_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- Delete user (should CASCADE delete session)
DELETE FROM users WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- Verify session was deleted
SELECT * FROM sessions WHERE id = 'b0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
```

**Expected:** Session automatically deleted when user deleted

#### Test Rollback
```bash
alembic downgrade base
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running downgrade 001_initial_schema -> , Initial database schema
```

**Verify:**
```bash
psql postgresql://postgres:postgres@localhost:5432/plccoach -c "\dt"
```

**Expected:** No tables except alembic_version

---

### 2. RDS PostgreSQL Validation (Production)

**Prerequisites:**
- AWS credentials configured
- VPN/bastion access to RDS if required
- Database already deployed from Story 1.1

#### Retrieve Database Credentials
```bash
aws secretsmanager get-secret-value \
  --secret-id plccoach-db-password \
  --query SecretString \
  --output text | jq .
```

**Expected Output:**
```json
{
  "username": "plccoach_admin",
  "password": "<32-character-password>",
  "engine": "postgres",
  "host": "plccoach-db.<region>.rds.amazonaws.com",
  "port": 5432,
  "dbname": "plccoach"
}
```

#### Apply Migrations to RDS
```bash
cd api-service

# Set AWS region (migrations will auto-fetch credentials)
export AWS_REGION=us-east-1
export DB_SECRET_NAME=plccoach-db-password

# Apply migrations
alembic upgrade head
```

**Expected:** Same output as local, migrations apply successfully

#### Verify RDS Schema
```bash
# Connect to RDS (using credentials from Secrets Manager)
psql postgresql://plccoach_admin:<password>@<rds-endpoint>:5432/plccoach

# Verify tables
\dt

# Verify pgvector
SELECT * FROM pg_extension WHERE extname = 'vector';

# Check migration version
SELECT * FROM alembic_version;
```

**Expected:** All tables created, pgvector installed, version shows 001_initial_schema

---

## Edge Cases and Error Handling

### Test 1: Invalid Role Constraint

```sql
-- Should FAIL with check constraint violation
INSERT INTO users (id, email, name, role)
VALUES (gen_random_uuid(), 'invalid@example.com', 'Invalid', 'superuser');
```

**Expected:** Error: `violates check constraint "check_user_role"`

### Test 2: Duplicate Email

```sql
-- Create user
INSERT INTO users (id, email, name, role)
VALUES (gen_random_uuid(), 'duplicate@example.com', 'User 1', 'educator');

-- Try to create another with same email (should FAIL)
INSERT INTO users (id, email, name, role)
VALUES (gen_random_uuid(), 'duplicate@example.com', 'User 2', 'educator');
```

**Expected:** Error: `violates unique constraint "uq_users_email"`

### Test 3: JSONB Citations

```sql
-- Insert message with complex JSONB
INSERT INTO users (id, email, name, role)
VALUES ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'jsonb@example.com', 'JSONB Test', 'educator');

INSERT INTO conversations (id, user_id, title)
VALUES ('d0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'c0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Test Conv');

INSERT INTO messages (id, conversation_id, role, content, citations)
VALUES (
  gen_random_uuid(),
  'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'assistant',
  'Test response',
  '{"sources": [{"title": "Source 1", "url": "https://example.com", "relevance": 0.95}], "confidence": 0.92}'::jsonb
);

-- Query JSONB field
SELECT citations->'confidence' as confidence,
       jsonb_array_length(citations->'sources') as source_count
FROM messages
WHERE conversation_id = 'd0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
```

**Expected:** Returns confidence: 0.92, source_count: 1

### Test 4: Partial Index on Sessions

```sql
-- Insert expired session
INSERT INTO users (id, email, name, role)
VALUES ('e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'session@example.com', 'Session Test', 'educator');

INSERT INTO sessions (id, user_id, expires_at)
VALUES (
  'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'e0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  NOW() - INTERVAL '1 hour'  -- Already expired
);

-- Check if partial index is being used
EXPLAIN SELECT * FROM sessions WHERE id = 'f0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
```

**Expected:** Should NOT use idx_sessions_id index (session is expired, outside partial index condition)

---

## Rollback Plan

### When to Rollback

- Migration fails partway through
- Application cannot connect to database after migration
- Data integrity issues discovered
- Performance degradation

### Rollback Procedure

1. **Backup Current State**
   ```bash
   pg_dump -U plccoach_admin -h <rds-endpoint> -d plccoach > backup_before_rollback.sql
   ```

2. **Rollback Migration**
   ```bash
   alembic downgrade -1  # Rollback one migration
   # or
   alembic downgrade base  # Rollback all migrations
   ```

3. **Verify Rollback**
   ```bash
   alembic current
   psql -h <rds-endpoint> -U plccoach_admin -d plccoach -c "\dt"
   ```

4. **Restart Application**
   - ECS tasks will auto-restart
   - Monitor logs for database connection errors

### Rollback Impact

**Rolling back 001_initial_schema:**
- ❌ Drops all tables (DATA LOSS!)
- ❌ Drops pgvector extension
- ❌ Drops all indexes
- ✅ Database returns to empty state
- ✅ Can reapply migrations

**Data Loss:** Yes - all user data, sessions, conversations, messages deleted

**Safe to Rollback:** Only if no production data exists or you have a backup

---

## Acceptance Criteria Checklist

- [x] **AC 1:** Database tables created
  - [x] users table with all required columns
  - [x] sessions table with all required columns
  - [x] conversations table with all required columns
  - [x] messages table with JSONB citations column

- [x] **AC 2:** pgvector extension installed
  - [x] CREATE EXTENSION IF NOT EXISTS vector in migration
  - [x] Extension visible in pg_extension table
  - [x] Ready for vector embeddings in future epics

- [x] **AC 3:** Indexes created for performance
  - [x] idx_users_email on users(email)
  - [x] idx_sessions_id partial index (WHERE expires_at > NOW())
  - [x] idx_conversations_user on conversations(user_id)
  - [x] idx_messages_conversation on messages(conversation_id, created_at)
  - [x] idx_conversations_share_token on conversations(share_token)

- [x] **AC 4:** Alembic migration system configured
  - [x] Alembic.ini configured
  - [x] env.py retrieves credentials from Secrets Manager
  - [x] Initial migration script creates all tables
  - [x] Rollback procedure documented in migrations/README.md
  - [x] Migration tested locally and ready for RDS

---

## Known Limitations

1. **Manual RDS Deployment Required**
   - Migrations require AWS credentials
   - Cannot be fully automated in CI/CD without credentials
   - User must run `alembic upgrade head` manually or via deployment script

2. **Test Database Setup**
   - Automated tests require local PostgreSQL with pgvector
   - Tests will skip if database not available
   - CI/CD pipeline needs PostgreSQL service container

3. **pgvector Version**
   - Using pgvector 0.2.4 (latest as of implementation)
   - Future versions may require migration updates
   - Extension installed but not yet used (waiting for Epic 2)

---

## Next Steps After Validation

1. **Deploy to RDS:**
   ```bash
   cd api-service
   export AWS_REGION=us-east-1
   alembic upgrade head
   ```

2. **Verify Deployment:**
   - Connect to RDS and verify tables
   - Check migration version
   - Test basic queries

3. **Mark Story Complete:**
   - All acceptance criteria met
   - Tests passing
   - Documentation complete
   - Ready for Story 1.3 (Backend API Foundation)

4. **Proceed to Story 1.3:**
   - Database models already defined
   - Connection pooling configured
   - Ready to build FastAPI application

---

## Troubleshooting

### Issue: "boto3 not installed"

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: "Cannot connect to PostgreSQL"

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep plccoach-db

# Restart if needed
docker start plccoach-db

# Verify connection
psql postgresql://postgres:postgres@localhost:5432/plccoach -c "SELECT 1"
```

### Issue: "pgvector extension not found"

**Solution:**
```bash
# Use pgvector/pgvector image, not standard postgres
docker run -d --name plccoach-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=plccoach \
  -p 5432:5432 \
  pgvector/pgvector:pg15  # <-- Important!
```

### Issue: "Migration fails with version conflict"

**Solution:**
```bash
# Check current version
alembic current

# Reset to base if needed
alembic downgrade base

# Reapply
alembic upgrade head
```

---

## Validation Sign-Off

- [ ] 30-second quick test passed
- [ ] Automated tests passed (100% pass rate)
- [ ] Local PostgreSQL validation completed
- [ ] RDS deployment completed (production)
- [ ] Edge cases tested
- [ ] Rollback procedure verified
- [ ] All acceptance criteria met
- [ ] Documentation reviewed

**Validated By:** _________________
**Date:** _________________
**Issues Found:** _________________
**Status:** ☐ Approved ☐ Changes Requested ☐ Blocked
