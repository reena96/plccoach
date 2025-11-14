# Story 2.1: Content Ingestion Pipeline - PDF Processing

**Epic:** Epic 2 - Core AI Coach
**Story ID:** 2-1-content-ingestion-pipeline-pdf-processing
**Author:** Reena
**Created:** 2025-11-14
**Status:** backlog

---

## User Story

**As a** content engineer,
**I want** to extract and process text from Solution Tree PDF books,
**So that** the content can be prepared for embedding and semantic search.

---

## Acceptance Criteria

**Given** we have 15-20 Solution Tree PDF books stored in S3
**When** the content ingestion script runs
**Then** for each PDF:
- Text is extracted using PyMuPDF (or pdfplumber)
- Document structure is preserved (headings, lists, tables)
- Page numbers, headers, and footers are removed
- OCR errors are cleaned up
- Whitespace is normalized

**And** extracted content is saved with metadata:
```json
{
  "book_id": "uuid",
  "book_title": "Learning by Doing",
  "authors": ["DuFour", "DuFour", "Eaker", "Many"],
  "publication_year": 2016,
  "total_pages": 350,
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "...",
      "page_start": 15,
      "page_end": 45,
      "content": "..."
    }
  ]
}
```

**And** the processed content is stored in S3 for the next stage

**And** a processing log records success/failure for each book

---

## Prerequisites

- Epic 1 Story 1.1 (S3 buckets must exist)

---

## Technical Notes

- Use PyMuPDF (fitz) or pdfplumber for extraction
- Preserve markdown-style structure (# for headings, lists, etc.)
- Handle special characters and encoding properly
- Initial corpus: Learning by Doing, Collaborative Common Assessments, Simplifying Response to Intervention, etc. (see PRD Section 10.1)
- Script location: `/scripts/content-ingestion/01_extract_pdfs.py`
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.5 (Content Ingestion Pipeline)
- Reference: PRD Section 10.2 (Content Preprocessing Pipeline)

---

## Implementation Plan

1. Set up scripts directory structure
2. Install required dependencies (PyMuPDF or pdfplumber)
3. Create PDF extraction script with:
   - S3 download functionality
   - Text extraction logic
   - Structure preservation
   - Metadata extraction
   - Output formatting
4. Add error handling and logging
5. Test with sample PDFs
6. Process full corpus
7. Verify output quality

---

## Testing Strategy

- Unit tests for text extraction functions
- Integration tests for S3 interaction
- Validation tests for metadata structure
- Manual QA of extracted content quality

---

## Definition of Done

- [ ] Script extracts text from PDFs successfully
- [ ] Document structure is preserved
- [ ] Metadata is complete and accurate
- [ ] Processed content stored in S3
- [ ] Processing logs capture all operations
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Validation guide created
