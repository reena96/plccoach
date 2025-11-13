# PLC Coach Database Migrations

This directory contains documentation and procedures for database migrations using Alembic.

## Migration Commands

### Apply Migrations

```bash
# Apply all pending migrations
cd api-service
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Apply next migration only
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration template
alembic revision -m "description of changes"
```

## Rollback Procedure

### Prerequisites
1. Ensure you have a recent database backup
2. Verify current migration revision: `alembic current`
3. Review the downgrade() function in the migration file

### Steps to Rollback

1. **Identify Target Revision**
   ```bash
   alembic history --verbose
   ```

2. **Test Rollback on Non-Production First**
   ```bash
   # On dev/staging environment
   alembic downgrade <target_revision>
   ```

3. **Verify Database State**
   - Check that tables/columns are correctly removed/restored
   - Verify data integrity
   - Test application functionality

4. **Execute Production Rollback** (if dev/staging successful)
   ```bash
   # Create backup first!
   pg_dump -U username -d plccoach > backup_before_rollback.sql

   # Execute rollback
   alembic downgrade <target_revision>

   # Verify
   alembic current
   ```

5. **Monitor Application**
   - Check application logs
   - Monitor error rates
   - Verify critical user flows

### Rollback Safety Rules

1. **Always backup before rollback**
   - Automated backups may not be recent enough
   - Manual backup provides immediate restore point

2. **Never rollback if data loss will occur**
   - Review downgrade() function carefully
   - If migration added columns with data, ensure data is preserved or acceptable to lose

3. **Test rollback in non-production first**
   - Use staging environment
   - Restore production data snapshot to staging if needed

4. **Coordinate with team**
   - Inform team of rollback plan
   - Ensure no concurrent deployments
   - Schedule during low-traffic period

### Emergency Rollback

If application is broken and immediate rollback needed:

```bash
# 1. Quick backup (runs in background, don't wait)
nohup pg_dump -U username -d plccoach > emergency_backup.sql &

# 2. Rollback immediately
alembic downgrade -1

# 3. Restart application
# (deployment-specific restart command)

# 4. Monitor logs
tail -f /var/log/application.log
```

## Migration File Structure

Each migration file contains:

- **revision**: Unique identifier for this migration
- **down_revision**: Parent migration (forms dependency chain)
- **upgrade()**: SQL/operations to apply migration
- **downgrade()**: SQL/operations to rollback migration

## Initial Schema Migration (001_initial_schema)

**File**: `alembic/versions/20251113_0100_001_initial_schema.py`

**Creates**:
- Users table with email, role, SSO fields
- Sessions table with expiration tracking
- Conversations table with sharing capabilities
- Messages table with JSONB citations and cost tracking
- pgvector extension for AI embeddings
- Performance indexes on all foreign keys

**Rollback Impact**:
- Drops all tables (data loss!)
- Drops pgvector extension
- Drops all indexes

**Rollback Safe**: Only if no data exists or data is backed up

## Testing Migrations

### Local Testing

```bash
# 1. Set up local PostgreSQL
docker run -d \
  --name plccoach-db-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=plccoach \
  -p 5432:5432 \
  pgvector/pgvector:pg15

# 2. Set environment variable
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/plccoach"

# 3. Apply migrations
alembic upgrade head

# 4. Test rollback
alembic downgrade base

# 5. Reapply
alembic upgrade head
```

### RDS Testing

```bash
# Requires AWS credentials and VPN/bastion access to RDS

# 1. Get database credentials from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id plccoach-db-password \
  --query SecretString \
  --output text

# 2. Apply migrations (will auto-retrieve from Secrets Manager)
alembic upgrade head
```

## Troubleshooting

### Migration Fails Midway

```bash
# Check current state
alembic current

# If migration partially applied, Alembic may be in inconsistent state
# Option 1: Fix the migration file and re-run
alembic upgrade head

# Option 2: Manually mark as complete if you fixed it manually in psql
alembic stamp <revision_id>
```

### Conflicting Migrations

```bash
# If two migrations have same down_revision (branching)
alembic merge <rev1> <rev2> -m "merge branches"
```

### pgvector Extension Fails

```bash
# If pgvector installation fails, install manually first:
psql -U username -d plccoach -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Then rerun migration
alembic upgrade head
```

## Best Practices

1. **Always test migrations**
   - Test on local database first
   - Test on dev/staging environment
   - Never apply untested migrations to production

2. **Write reversible migrations**
   - Always implement downgrade() function
   - Test rollback procedure
   - Document data loss implications

3. **Use transactions**
   - Alembic migrations run in transactions by default
   - Failed migrations automatically rollback
   - For long-running migrations, consider manual transaction control

4. **Version control**
   - Commit migration files to git
   - Never edit applied migrations
   - Create new migration for fixes

5. **Monitor migration performance**
   - Large table migrations may lock tables
   - Consider online schema change tools for large tables
   - Schedule during maintenance windows if needed

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Migration Best Practices](https://www.postgresql.org/docs/current/ddl-alter.html)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
