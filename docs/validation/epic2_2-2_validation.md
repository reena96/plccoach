# Validation Guide: Story 2.2 - Content Chunking with Metadata Tagging

**Story ID:** 2-2-content-chunking-with-metadata-tagging
**Epic:** Epic 2 - Core AI Coach
**Date:** 2025-11-14
**Status:** Complete

---

## 30-Second Quick Test

```bash
# Verify script exists and is executable
ls -la scripts/content-ingestion/02_chunk_content.py

# Run unit tests
source venv/bin/activate
pytest tests/content-ingestion/test_chunking.py -v

# Expected: 30 passed tests
```

**Expected Result:** All tests pass

---

## Automated Test Results

### Unit Tests

**Command:**
```bash
source venv/bin/activate
pytest tests/content-ingestion/test_chunking.py -v --cov=scripts/content-ingestion/02_chunk_content.py
```

**Results:**
- ✅ Total Tests: 30
- ✅ Passed: 30
- ✅ Failed: 0
- ✅ Coverage: 70% (good for chunking logic)

**Test Categories:**
1. **Content Chunking (8 tests)**
   - Token counting
   - Semantic boundary detection
   - Multiple chunk creation
   - Max token enforcement
   - Overlap verification

2. **Metadata Creation (3 tests)**
   - Full metadata structure
   - Domain classification integration
   - Required fields validation

3. **Quality Validation (4 tests)**
   - Valid chunk validation
   - Missing field detection
   - Token limit enforcement
   - Zero token detection

4. **Domain Classification (6 tests)**
   - Assessment domain
   - Collaboration domain
   - Book title context
   - Default domain
   - Secondary domains
   - Empty text handling

5. **Pipeline Orchestration (5 tests)**
   - Pipeline initialization
   - File listing
   - Book data download
   - Error handling

6. **Metadata Structure (4 tests)**
   - Required fields compliance
   - Token count range
   - UUID validation
   - Domain validity

---

## Manual Validation Steps

### Prerequisites
```bash
# 1. Ensure AWS credentials are configured
aws configure list

# 2. Verify S3 bucket and Story 2.1 output exists
aws s3 ls s3://plccoach-content/processed/

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r scripts/content-ingestion/requirements.txt
```

### Test with Sample Content

**Step 1: Verify Story 2.1 output exists**
```bash
# List processed books from Story 2.1
aws s3 ls s3://plccoach-content/processed/ | grep .json
```

**Step 2: Run chunking script**
```bash
cd api-service
python scripts/content-ingestion/02_chunk_content.py \
  --bucket plccoach-content \
  --input-prefix processed/ \
  --output-prefix chunked/
```

**Expected Output:**
```
INFO - Starting content chunking pipeline
INFO - Found X book files in plccoach-content/processed/
INFO - Downloaded book data: [Book Title]
INFO - Uploaded Y chunks for [book].json to chunked/[book]_chunked.json
INFO - Pipeline complete: X successful, 0 failed
INFO - Log uploaded to chunked/logs/chunking_log_*.json
```

**Step 3: Verify chunked output**
```bash
# Download and inspect chunked output
aws s3 cp s3://plccoach-content/chunked/sample_chunked.json .
cat sample_chunked.json | jq
```

**Expected JSON Structure:**
```json
{
  "book_id": "uuid",
  "book_title": "Book Title",
  "total_chunks": 150,
  "chunks": [
    {
      "chunk_id": "uuid",
      "book_id": "uuid",
      "book_title": "Book Title",
      "authors": ["Author 1", "Author 2"],
      "chapter_number": 1,
      "chapter_title": "Introduction",
      "page_start": 1,
      "page_end": 10,
      "chunk_index": 0,
      "total_chunks_in_chapter": 15,
      "content": "Chunked text content...",
      "token_count": 750,
      "primary_domain": "collaboration",
      "secondary_domains": ["assessment"],
      "created_at": "2025-11-14T..."
    }
  ],
  "chunking_date": "2025-11-14T...",
  "source_file": "sample.json"
}
```

**Step 4: Validate chunk properties**
```bash
# Check token counts are in range
cat sample_chunked.json | jq '.chunks[].token_count' | sort -n

# Expected: All values between 500-1000

# Check all chunks have required fields
cat sample_chunked.json | jq '.chunks[0] | keys'

# Expected: All required fields present
```

**Step 5: Verify processing log**
```bash
# Check local log
cat content_chunking.log

# Check S3 log
aws s3 ls s3://plccoach-content/chunked/logs/
aws s3 cp s3://plccoach-content/chunked/logs/chunking_log_*.json .
cat chunking_log_*.json | jq
```

---

## Edge Cases & Error Handling

### Test 1: Small Chapter (< 500 tokens)
```bash
# Create a book with very short chapter
# Upload to S3 and process
```
**Expected:** Single chunk created even if < 500 tokens

### Test 2: Very Long Chapter (> 10,000 tokens)
```bash
# Process a book with very long chapters
```
**Expected:** Multiple chunks created, all within 500-1000 token range

### Test 3: Chapter with Lists and Code Blocks
**Expected:** List items kept together, semantic boundaries respected

### Test 4: Empty Chapter
**Expected:** No chunks created for empty chapters

### Test 5: Missing Input File
```bash
python scripts/content-ingestion/02_chunk_content.py \
  --bucket plccoach-content \
  --input-prefix nonexistent/
```
**Expected:** Warning logged, no errors

---

## Quality Assurance Checks

### Token Count Validation
```bash
# Verify no chunks exceed 1000 tokens
cat sample_chunked.json | jq '.chunks[] | select(.token_count > 1000)'

# Expected: Empty (no results)
```

### Metadata Completeness
```bash
# Check all chunks have required fields
for field in chunk_id book_id book_title authors chapter_number chapter_title page_start page_end chunk_index total_chunks_in_chapter content token_count; do
  echo "Checking $field..."
  cat sample_chunked.json | jq ".chunks[] | select(.${field} == null)"
done

# Expected: All empty (all fields present)
```

### Overlap Verification
```bash
# Check that consecutive chunks have some overlap
# (Manual inspection of content)
cat sample_chunked.json | jq '.chunks[0:2][].content | .[0:100]'
```

### Domain Classification
```bash
# Check domains are from valid set
cat sample_chunked.json | jq '.chunks[].primary_domain' | sort | uniq

# Expected: Only valid domains (assessment, collaboration, leadership, curriculum, data_analysis, school_culture, student_learning, null)
```

---

## Rollback Plan

### If chunking fails:
1. **Check logs:** `content_chunking.log` and S3 logs
2. **Verify Story 2.1 output:** Ensure processed book JSON files are valid
3. **Check dependencies:** `pip list | grep tiktoken`
4. **Revert script if needed:**
   ```bash
   git checkout main -- scripts/content-ingestion/02_chunk_content.py
   ```

### If chunks are invalid:
1. **Delete bad outputs:**
   ```bash
   aws s3 rm s3://plccoach-content/chunked/ --recursive
   ```
2. **Fix script and re-run**
3. **Re-validate with tests**

---

## Acceptance Criteria Checklist

- [x] **AC#1: Chunking Algorithm**
  - [x] Target size: 500-1000 tokens per chunk
  - [x] 100-token overlap between chunks
  - [x] Semantic boundaries respected
  - [x] Related elements kept together

- [x] **AC#2: Metadata Tagging**
  - [x] All required metadata fields present
  - [x] UUID generation for chunk_id
  - [x] Accurate token counting
  - [x] Page number tracking from source

- [x] **AC#3: Domain Classification**
  - [x] SimpleDomainClassifier implemented
  - [x] 7 domains supported
  - [x] Primary and secondary domain logic
  - [x] Keyword-based classification

- [x] **AC#4: Quality Assurance**
  - [x] No chunks exceed 1000 tokens
  - [x] All chunks have required metadata fields
  - [x] Page numbers accurate
  - [x] Output saved to S3

---

## Files Created/Modified

### New Files
- `scripts/content-ingestion/02_chunk_content.py` - Main chunking script (600+ lines)
- `tests/content-ingestion/test_chunking.py` - Unit tests (30 tests)
- `docs/stories/2-2-content-chunking-with-metadata-tagging.md` - Story file
- `docs/stories/2-2-content-chunking-with-metadata-tagging.context.xml` - Context file

### Modified Files
- `scripts/content-ingestion/requirements.txt` - Added tiktoken
- `scripts/content-ingestion/README.md` - Updated with Stage 2 info
- `docs/scrum/sprint-status.yaml` - Updated story status

---

## Performance Metrics

**Test Execution Time:** < 2 seconds (all tests)

**Expected Production Performance:**
- Single book (350 pages, ~150 chunks): 5-10 seconds
- Batch of 15-20 books: < 5 minutes
- Token counting: ~1000 tokens/ms

**Storage Requirements:**
- Input: ~2MB per book (Story 2.1 output)
- Output: ~3MB per book (chunked with metadata)
- Compression ratio: ~1.5x (due to metadata overhead)

---

## Known Limitations

1. **Domain Classification:** Simple rule-based classifier may not be 100% accurate. Consider GPT-4o classification for production.
2. **Semantic Boundaries:** Works well for standard text but may have issues with tables, diagrams, or complex formatting.
3. **Token Counting:** Uses cl100k_base encoding (GPT-4). May differ slightly from other tokenizers.

---

## Next Steps

✅ Story 2.2 Complete

**Dependencies:**
- Story 2.1 output (processed book JSON files)

**Next Story:** 2.3 - Vector Embeddings Generation
- Use Story 2.2 outputs as inputs
- Generate 3072-dimensional embeddings for each chunk
- Use OpenAI text-embedding-3-large API

---

## Sign-Off

**Developer:** Claude Code
**Date:** 2025-11-14
**Status:** ✅ All acceptance criteria met
**Tests:** ✅ 30/30 passing
**Coverage:** ✅ 70% (chunking script)
**Ready for:** Story 2.3 implementation
