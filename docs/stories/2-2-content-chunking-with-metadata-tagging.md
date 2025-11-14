# Story 2.2: Content Chunking with Metadata Tagging

**Epic:** Epic 2 - Core AI Coach
**Story ID:** 2-2-content-chunking-with-metadata-tagging
**Author:** Reena
**Created:** 2025-11-14
**Status:** backlog

---

## User Story

**As a** content engineer,
**I want** to split processed book content into semantic chunks with rich metadata,
**So that** each chunk can be embedded and retrieved independently.

---

## Acceptance Criteria

**Given** processed book content from Story 2.1
**When** the chunking script runs
**Then** content is split into chunks with:
- Target size: 500-1000 tokens per chunk
- 100-token overlap between consecutive chunks
- Semantic boundaries respected (no mid-paragraph splits)
- Related elements kept together (list items + explanations)

**And** each chunk is tagged with metadata:
```json
{
  "chunk_id": "uuid",
  "book_id": "uuid",
  "book_title": "Learning by Doing",
  "authors": ["DuFour", "DuFour", "Eaker", "Many"],
  "chapter_number": 3,
  "chapter_title": "The Four Critical Questions",
  "page_start": 45,
  "page_end": 47,
  "chunk_index": 12,
  "total_chunks_in_chapter": 45,
  "content": "The actual text content...",
  "token_count": 680,
  "primary_domain": "collaborative_teams",
  "secondary_domains": ["curriculum", "assessment"]
}
```

**And** domain classification is done either:
- Manually for initial corpus (faster for 15-20 books)
- Or using GPT-4o for automatic classification

**And** chunked content with metadata is saved to S3

**And** quality assurance checks verify:
- No chunks exceed 1000 tokens
- All chunks have required metadata fields
- Page numbers are accurate

---

## Prerequisites

- Story 2.1 (extracted content must exist)

---

## Technical Notes

- Use tiktoken library to count tokens (OpenAI tokenizer)
- Implement intelligent chunking algorithm (see TECHNICAL_ARCHITECTURE.md Section 2.5)
- For 15-20 books, manual domain tagging may be faster than automated
- Consider using section headers as context for each chunk
- Script location: `/scripts/content-ingestion/02_chunk_content.py`
- Reference: PRD Section 10.2 Step 4 (Intelligent Chunking)

---

## Implementation Plan

1. Install tiktoken dependency
2. Create chunking script with:
   - Token counting using tiktoken
   - Semantic boundary detection
   - Overlap management
   - Metadata tagging
3. Implement domain classification (manual or automated)
4. Add S3 integration
5. Add quality assurance checks
6. Create comprehensive tests
7. Process sample content
8. Validate output quality

---

## Testing Strategy

- Unit tests for chunking logic
- Unit tests for token counting
- Unit tests for metadata structure
- Integration tests for S3 interaction
- Quality validation tests

---

## Definition of Done

- [ ] Script chunks content into 500-1000 token pieces
- [ ] 100-token overlap implemented
- [ ] Semantic boundaries respected
- [ ] All metadata fields populated
- [ ] Domain classification working
- [ ] Output saved to S3
- [ ] Quality checks passing
- [ ] Unit tests passing
- [ ] Validation guide created
