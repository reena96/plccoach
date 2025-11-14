# Validation Guide: Story 3.10 - All 7 Knowledge Domains Operational

**Story:** 3.10 - All 7 Knowledge Domains Operational
**Epic:** 3 - Conversations & History
**Status:** Implementation Complete - Awaiting Manual Validation
**Date:** 2025-11-14

---

## 30-Second Quick Test

```bash
# Start API service
cd api-service && ./run-local.sh

# In another terminal, run validation
python scripts/validate_domains.py --verbose

# Expected: 90%+ pass rate across all 7 domains
```

---

## What Was Implemented

### 1. Domain Test Suite Document ✅
**File:** `docs/testing/domain-coverage-tests.md`

- Comprehensive test plan with 39 test queries
- 35 domain-specific queries (5 per domain)
- 4 cross-domain queries
- 4 clarification test queries
- Expected books and citations documented

### 2. Automated Validation Script ✅
**File:** `scripts/validate_domains.py`

- Executable Python script for domain validation
- Tests all 7 domains automatically
- Validates intent classification accuracy
- Checks retrieval returns correct books
- Verifies clarification prompts for vague queries
- Generates JSON results report
- Command-line interface with verbose mode

### 3. Testing Infrastructure ✅
**Directory:** `docs/testing/`

- Organized location for all test documentation
- Results can be saved to `domain-validation-results.json`
- Ready for CI/CD integration

---

## Automated Test Results

### Test Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Domain Test Suite | 39 queries defined | ✅ Complete |
| Validation Script | Automated execution | ✅ Complete |
| Intent Classification Tests | All 7 domains | ✅ Ready |
| Retrieval Accuracy Tests | Cross-domain + clarification | ✅ Ready |
| Results Reporting | JSON + console output | ✅ Complete |

### Automated Tests Status

**Note:** Automated tests cannot run in development environment without:
- Running API service (Docker + PostgreSQL)
- Content ingested into database (Epic 2 completion required)
- OpenAI API key configured

**Tests are ready to run when system is operational.**

---

## Manual Validation Steps

### Prerequisites
1. API service running (`docker-compose up` or `./api-service/run-local.sh`)
2. Database populated with PLC content (Epic 2 complete)
3. OpenAI API key configured in environment
4. Python 3.9+ with requests library

### Step 1: Run Automated Validation

```bash
# Basic validation (all 39 queries)
python scripts/validate_domains.py

# Verbose mode (shows books cited, confidence scores)
python scripts/validate_domains.py --verbose

# Custom API URL
python scripts/validate_domains.py --api-url http://localhost:8000

# Save results to custom location
python scripts/validate_domains.py --output results.json
```

### Step 2: Review Results

Check the output for:
- **Overall pass rate** (target: ≥ 90%)
- **Per-domain accuracy** (each domain should have ≥ 80% accuracy)
- **Book citations** (verify expected books appear in results)
- **Confidence scores** (should be > 0.7 for clear queries)
- **Clarification triggers** (vague queries should trigger clarification)

### Step 3: Manual Spot Checks

Test via web UI or API:

```bash
# Test Assessment domain
curl -X POST http://localhost:8000/api/coach/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What makes a good common formative assessment?"}'

# Expected: primary_domain="assessment", books include "Collaborative Common Assessments"
```

**Manual test queries:**
1. Assessment: "What makes a good common formative assessment?"
2. Collaboration: "How do we establish effective team norms?"
3. Leadership: "What is the role of the principal in a PLC?"
4. Curriculum: "What is a guaranteed and viable curriculum?"
5. Data Analysis: "How do we implement RTI effectively?"
6. School Culture: "How do we shift to a PLC culture?"
7. Student Learning: "How do we increase student engagement?"

### Step 4: Cross-Domain Testing

```bash
curl -X POST http://localhost:8000/api/coach/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do assessments connect to RTI?"}'

# Expected: primary_domain="assessment", secondary_domains=["data_analysis"]
```

### Step 5: Clarification Testing

```bash
curl -X POST http://localhost:8000/api/coach/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about PLCs"}'

# Expected: needs_clarification=true, clarification_question provided
```

---

## Edge Cases and Error Handling

### Edge Case 1: Empty Database
**Scenario:** No content ingested
**Expected:** Service should return error or low-confidence response
**Test:** Run validation before content ingestion

### Edge Case 2: Missing Domain Content
**Scenario:** One domain has no books/chunks
**Expected:** Classification works but retrieval returns empty
**Test:** Check per-domain content coverage

### Edge Case 3: API Service Down
**Scenario:** Service not running
**Expected:** Validation script shows connection errors
**Test:** Run script without starting service

### Edge Case 4: Invalid Queries
**Scenario:** Empty query, very long query (>1000 chars)
**Expected:** Graceful handling with appropriate error messages
**Test:** Add edge cases to validation script

---

## Acceptance Criteria Verification

| AC # | Criteria | Verification Method | Status |
|------|----------|---------------------|--------|
| 1 | Domain coverage testing performed | Run validation script | ⏳ Awaiting |
| 2 | All 7 domains return relevant responses | Check per-domain pass rates | ⏳ Awaiting |
| 2 | Expected books cited per domain | Verify books in results | ⏳ Awaiting |
| 3 | Cross-domain queries work | Test 4 cross-domain queries | ⏳ Awaiting |
| 4 | Clarification for vague queries | Test 4 vague queries | ⏳ Awaiting |

**Legend:** ✅ Verified | ⏳ Awaiting Manual Test | ❌ Failed

---

## Rollback Plan

**N/A** - This story only adds validation infrastructure (tests + scripts). No production code changes. Safe to proceed with no rollback needed.

---

## Known Limitations

1. **Manual Execution Required:** Validation script requires running API service
2. **Content Dependency:** Results depend on quality of ingested content (Epic 2)
3. **No CI Integration Yet:** Script not yet integrated into CI/CD pipeline (future work)
4. **Book Detection:** Script checks for book titles in metadata but doesn't verify relevance

---

## Content Gaps Analysis

**To be filled after running validation:**

### Expected Format

```
Domain: assessment
- Books found: 3
- Coverage: Good
- Gaps: Need more assessment item design resources

Domain: curriculum
- Books found: 2
- Coverage: Weak
- Gaps: Missing standards alignment books
```

---

## Next Steps for Future Enhancements

1. **CI/CD Integration:** Add validation script to GitHub Actions
2. **Regression Testing:** Run validation after content updates
3. **Performance Metrics:** Track retrieval speed per domain
4. **Content Additions:** Ingest additional books for weak domains
5. **User Feedback:** Collect real educator feedback on domain accuracy

---

## Files Modified/Created

### Created
- `docs/testing/domain-coverage-tests.md` - Test suite documentation
- `scripts/validate_domains.py` - Automated validation script
- `docs/validation/epic3_3-10_validation.md` - This validation guide

### Modified
- `docs/scrum/stories/3-10-all-7-knowledge-domains-operational.md` - Updated with implementation notes

---

## Success Criteria

✅ **Story Complete When:**
- [x] Test suite document created with 39 queries
- [x] Validation script implemented and executable
- [x] Validation guide created
- [ ] Manual validation performed (awaiting system operational)
- [ ] 90%+ pass rate achieved
- [ ] Content gaps documented

**Status:** Implementation complete. Awaiting manual validation when API service is running with ingested content.

---

## Validation Sign-Off

**Developer:** Claude (Automated)
**Date:** 2025-11-14
**Manual Validation:** Pending
**Production Ready:** Yes (validation infrastructure only)
