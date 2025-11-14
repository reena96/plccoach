# Story 2.4: PostgreSQL pgvector Setup & Data Upload

**Epic:** Epic 2 - Core AI Coach
**Story ID:** 2-4-postgresql-pgvector-setup-data-upload
**Author:** Reena
**Created:** 2025-11-14
**Status:** backlog

---

## User Story

**As a** backend developer,
**I want** to store vector embeddings in PostgreSQL using pgvector extension,
**So that** semantic search can be performed directly in the database.

---

## Acceptance Criteria

**Given** PostgreSQL database from Epic 1
**When** pgvector setup script runs
**Then** the pgvector extension is installed: `CREATE EXTENSION IF NOT EXISTS vector;`

**And** the embeddings table is created:
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(3072),
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**And** an ivfflat index is created for fast similarity search:
```sql
CREATE INDEX ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**And** all chunk embeddings from Story 2.3 are inserted into the table

**And** metadata includes: book_title, chapter, pages, domain, authors, etc.

**And** a semantic search test query returns relevant results:
```sql
SELECT content, metadata,
       1 - (embedding <=> '[query_vector]') as similarity
FROM embeddings
ORDER BY embedding <=> '[query_vector]'
LIMIT 10;
```

**And** query performance is <500ms for top-10 similarity search

---

## Prerequisites

- Story 2.3 (embeddings must be generated)

---

## Technical Notes

- Install pgvector extension in PostgreSQL 15
- Use cosine similarity (<=>) for vector comparison
- ivfflat index: good for <1M vectors, faster than brute force
- Bulk insert embeddings in batches of 1000
- Test with sample queries from different domains
- Script location: `/scripts/content-ingestion/04_upload_to_db.py`
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #4 (pgvector choice)
- Reference: TECHNICAL_ARCHITECTURE.md Section 3.2 (Vector Database Schema)

---

## Implementation Plan

1. Create Alembic migration for embeddings table
2. Add pgvector extension installation
3. Create embeddings table with vector column
4. Create ivfflat index
5. Create upload script to read embeddings from S3
6. Implement batch upload logic
7. Add progress tracking
8. Create test queries
9. Validate query performance
10. Add comprehensive tests

---

## Testing Strategy

- Unit tests for table creation
- Integration tests for data upload
- Performance tests for similarity search
- Validation tests for data integrity

---

## Definition of Done

- [ ] pgvector extension installed
- [ ] Embeddings table created with correct schema
- [ ] ivfflat index created
- [ ] All embeddings uploaded to database
- [ ] Semantic search queries working
- [ ] Query performance <500ms
- [ ] Unit tests passing
- [ ] Validation guide created
