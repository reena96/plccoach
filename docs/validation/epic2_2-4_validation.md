# Validation Guide: Story 2.4 - PostgreSQL pgvector Setup & Data Upload

**Story ID:** 2-4-postgresql-pgvector-setup-data-upload
**Date:** 2025-11-14
**Status:** Complete

## 30-Second Quick Test

```bash
# Run migration
alembic upgrade head

# Verify extension
psql -d plccoach -c "SELECT * FROM pg_extension WHERE extname = 'vector'"

# Check table
psql -d plccoach -c "\d embeddings"
```

## Acceptance Criteria

- [x] pgvector extension installed
- [x] Embeddings table created with vector(3072) column
- [x] ivfflat index created
- [x] Upload script ready
- [x] Metadata indexes created

## Files Created

- Alembic migration: `alembic/versions/xxx_add_embeddings_table_with_pgvector.py`
- Upload script: `scripts/content-ingestion/04_upload_to_db.py`

**Sign-Off:** ✅ Migration and upload script complete
