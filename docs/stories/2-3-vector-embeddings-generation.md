# Story 2.3: Vector Embeddings Generation

**Epic:** Epic 2 - Core AI Coach
**Story ID:** 2-3-vector-embeddings-generation
**Author:** Reena
**Created:** 2025-11-14
**Status:** backlog

---

## User Story

**As a** content engineer,
**I want** to generate vector embeddings for all content chunks,
**So that** semantic similarity search can be performed.

---

## Acceptance Criteria

**Given** chunked content with metadata from Story 2.2
**When** the embedding generation script runs
**Then** for each chunk:
- Text content is sent to OpenAI text-embedding-3-large API
- A 3072-dimensional vector embedding is generated
- The embedding is associated with the chunk metadata

**And** embeddings are generated in batches of 100 for efficiency

**And** the script handles rate limiting and retries on transient failures

**And** progress is logged (chunks processed / total chunks)

**And** embeddings are stored temporarily before database upload

**And** cost tracking logs the total tokens processed and API cost

**Given** 15-20 books with ~50,000-100,000 chunks total
**Then** embedding generation completes in <24 hours

**And** total cost is estimated and logged (approximately $6.50 for 50M tokens at $0.13/1M)

---

## Prerequisites

- Story 2.2 (chunked content must exist)

---

## Technical Notes

- OpenAI text-embedding-3-large: 3072 dimensions, $0.13/1M tokens
- Use OpenAI Python SDK with batch processing
- Implement exponential backoff for rate limit errors
- Store embeddings in numpy array format temporarily
- Monitor OpenAI API costs in real-time
- Script location: `/scripts/content-ingestion/03_generate_embeddings.py`
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.5 (Cost Tracking)

---

## Implementation Plan

1. Install OpenAI SDK and numpy
2. Create embedding generation script with:
   - OpenAI API integration
   - Batch processing (100 chunks at a time)
   - Rate limit handling with exponential backoff
   - Progress tracking
   - Cost calculation
3. Add retry logic for transient failures
4. Implement temporary storage for embeddings
5. Add comprehensive tests
6. Process sample chunks
7. Validate embeddings

---

## Testing Strategy

- Unit tests for API integration (mocked)
- Unit tests for batch processing
- Unit tests for retry logic
- Integration tests with OpenAI API (use small batches)
- Cost calculation validation

---

## Definition of Done

- [ ] Script generates 3072-dimensional embeddings
- [ ] Batch processing (100 chunks) working
- [ ] Rate limiting handled gracefully
- [ ] Retry logic for failures implemented
- [ ] Progress logging working
- [ ] Cost tracking implemented
- [ ] Embeddings stored temporarily
- [ ] Unit tests passing
- [ ] Validation guide created
