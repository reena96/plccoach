# Domain Coverage Tests - PLC Coach AI

**Status:** In Progress
**Date:** 2025-11-14
**Story:** 3.10 - All 7 Knowledge Domains Operational
**Purpose:** Validate that all 7 PLC knowledge domains return relevant responses with appropriate citations

---

## Executive Summary

This document defines comprehensive test queries for validating the PLC Coach AI system across all 7 knowledge domains. Each domain should correctly classify queries, retrieve relevant content chunks, and generate responses with appropriate citations from Solution Tree books.

**Success Criteria:** 90%+ queries return relevant responses with correct domain classification and appropriate book citations.

---

## The 7 Knowledge Domains

As defined in `api-service/app/services/intent_router.py`:

1. **assessment** - Formative and summative assessments, grading practices, evaluation methods
2. **collaboration** - Team structures, collaborative norms, meeting protocols, teamwork
3. **leadership** - Principal and administrator guidance, change management, leadership practices
4. **curriculum** - Guaranteed and viable curriculum, standards alignment, curriculum design
5. **data_analysis** - RTI, Response to Intervention, MTSS, data-driven decisions, progress monitoring
6. **school_culture** - PLC implementation, culture building, professional learning communities
7. **student_learning** - Student-centered practices, engagement, motivation, achievement

---

## Domain 1: Assessment & Evaluation

### Expected Books/Sources
- "Collaborative Common Assessments"
- "Learning by Doing" (assessment chapters)
- Assessment-focused PLC resources

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| A-1 | "What makes a good common formative assessment?" | assessment | Collaborative Common Assessments | AC requirement |
| A-2 | "How do we create quality assessment items?" | assessment | Collaborative Common Assessments | |
| A-3 | "What's the difference between formative and summative assessment?" | assessment | Assessment resources | |
| A-4 | "How should we grade student work in a PLC?" | assessment | PLC assessment books | |
| A-5 | "What are the characteristics of quality rubrics?" | assessment | Assessment resources | |

---

## Domain 2: Collaborative Teams

### Expected Books/Sources
- "Learning by Doing"
- "Handbook for Collaborative Teams"
- Team collaboration resources

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| C-1 | "How do we establish effective team norms?" | collaboration | Learning by Doing, Handbook for Collaborative Teams | AC requirement |
| C-2 | "What makes a high-performing collaborative team?" | collaboration | Learning by Doing | |
| C-3 | "How do we structure effective team meetings?" | collaboration | Handbook for Collaborative Teams | |
| C-4 | "What protocols help teams make decisions?" | collaboration | Team collaboration resources | |
| C-5 | "How do we build trust among team members?" | collaboration | Collaboration resources | |

---

## Domain 3: Leadership & Administration

### Expected Books/Sources
- "Leaders of Learning"
- "Learning by Doing" (leadership chapters)
- PLC leadership resources

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| L-1 | "What is the role of the principal in a PLC?" | leadership | Leaders of Learning | AC requirement |
| L-2 | "How do leaders support collaborative teams?" | leadership | Leaders of Learning | |
| L-3 | "What does loose and tight leadership mean?" | leadership | Learning by Doing | |
| L-4 | "How do principals lead change in a PLC?" | leadership | Leaders of Learning | |
| L-5 | "What are the responsibilities of district leaders?" | leadership | Leadership resources | |

---

## Domain 4: Curriculum & Instruction

### Expected Books/Sources
- Curriculum-focused PLC books
- "Learning by Doing" (curriculum chapters)
- Standards alignment resources

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| CU-1 | "What is a guaranteed and viable curriculum?" | curriculum | Curriculum resources | AC requirement |
| CU-2 | "How do we align curriculum to standards?" | curriculum | Standards resources | |
| CU-3 | "What are essential learning outcomes?" | curriculum | Curriculum books | |
| CU-4 | "How do we prioritize curriculum content?" | curriculum | Curriculum resources | |
| CU-5 | "What is curriculum mapping in a PLC?" | curriculum | PLC curriculum books | |

---

## Domain 5: Data Analysis & Response

### Expected Books/Sources
- "Simplifying Response to Intervention"
- RTI/MTSS resources
- Data-driven decision books

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| D-1 | "How do we implement RTI effectively?" | data_analysis | Simplifying Response to Intervention | AC requirement |
| D-2 | "What is a multi-tiered system of supports?" | data_analysis | RTI/MTSS resources | |
| D-3 | "How do we use data to identify struggling students?" | data_analysis | Data-driven resources | |
| D-4 | "What interventions work best for Tier 2?" | data_analysis | RTI resources | |
| D-5 | "How do we monitor student progress effectively?" | data_analysis | Progress monitoring books | |

---

## Domain 6: School Culture & Systems

### Expected Books/Sources
- "Learning by Doing"
- PLC implementation books
- Culture-building resources

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| SC-1 | "How do we shift to a PLC culture?" | school_culture | Implementation books | AC requirement |
| SC-2 | "What are the three big ideas of a PLC?" | school_culture | Learning by Doing | |
| SC-3 | "How do we build a culture of collaboration?" | school_culture | PLC culture books | |
| SC-4 | "What are the four critical questions of a PLC?" | school_culture | Learning by Doing | |
| SC-5 | "How do we sustain PLC practices over time?" | school_culture | Implementation resources | |

---

## Domain 7: Student Learning & Engagement

### Expected Books/Sources
- Student-centered practices books
- Engagement strategy resources
- Student achievement books

### Test Queries

| ID | Query | Expected Primary Domain | Expected Books | Notes |
|----|-------|------------------------|----------------|-------|
| SL-1 | "How do we increase student engagement?" | student_learning | Student practices books | AC requirement |
| SL-2 | "What strategies improve student motivation?" | student_learning | Engagement resources | |
| SL-3 | "How do we help students take ownership of learning?" | student_learning | Student-centered books | |
| SL-4 | "What does student voice look like in practice?" | student_learning | Student learning resources | |
| SL-5 | "How do we differentiate instruction for all learners?" | student_learning | Differentiation books | |

---

## Cross-Domain Test Queries

These queries span multiple domains and should correctly identify primary + secondary domains:

| ID | Query | Expected Primary | Expected Secondary | Notes |
|----|-------|-----------------|-------------------|-------|
| X-1 | "How do assessments connect to RTI?" | assessment | data_analysis | AC requirement |
| X-2 | "How do leaders support data-driven instruction?" | leadership | data_analysis, curriculum | Multi-domain |
| X-3 | "What role does collaboration play in student success?" | collaboration | student_learning | Multi-domain |
| X-4 | "How do we build a culture of assessment?" | school_culture | assessment | Multi-domain |

---

## Clarification Test Queries

These vague queries should trigger `needs_clarification=True`:

| ID | Query | Expected Behavior | Notes |
|----|-------|------------------|-------|
| V-1 | "Tell me about PLCs" | needs_clarification=True | AC requirement |
| V-2 | "How do I improve my school?" | needs_clarification=True | Too vague |
| V-3 | "What should we do?" | needs_clarification=True | No context |
| V-4 | "Help" | needs_clarification=True | Extremely vague |

---

## Test Execution Plan

### Phase 1: Manual Testing (Immediate)
1. Run each domain-specific query through the chat API
2. Verify intent classification returns correct primary domain
3. Check that retrieved chunks contain expected books
4. Validate response quality and citation accuracy
5. Document any failures or unexpected results

### Phase 2: Automated Testing (Future)
1. Create pytest test suite: `api-service/tests/domain-validation/`
2. Automate intent classification tests
3. Automate retrieval accuracy tests
4. Add to CI/CD pipeline

---

## Test Results

**Total Queries:** 39 (35 domain-specific + 4 cross-domain + 4 clarification)

### Results Summary
_(To be filled during test execution)_

| Domain | Queries Tested | Passed | Failed | Pass Rate |
|--------|---------------|--------|--------|-----------|
| Assessment | 5 | - | - | - |
| Collaboration | 5 | - | - | - |
| Leadership | 5 | - | - | - |
| Curriculum | 5 | - | - | - |
| Data Analysis | 5 | - | - | - |
| School Culture | 5 | - | - | - |
| Student Learning | 5 | - | - | - |
| Cross-Domain | 4 | - | - | - |
| Clarification | 4 | - | - | - |
| **TOTAL** | **39** | **-** | **-** | **-%** |

---

## Content Coverage Gaps

_(To be filled during testing)_

### Domains with Strong Coverage
- List domains where most queries return high-quality results

### Domains Needing Improvement
- List domains with weak coverage or missing books

### Recommended Content Additions
- Specific books or topics to add in future content ingestion

---

## Validation Checklist

- [ ] All 7 domains tested with minimum 5 queries each (35 total)
- [ ] Intent classification accuracy verified for each domain
- [ ] Expected books appear in retrieved chunks
- [ ] Citation extraction works correctly
- [ ] Cross-domain queries correctly identify multiple domains
- [ ] Clarification prompts trigger for vague queries
- [ ] 90%+ success rate achieved overall
- [ ] Content gaps documented for future work
- [ ] Test results added to story file

---

## Next Steps

1. **Execute Manual Tests:** Run all 39 test queries through the system
2. **Document Results:** Fill in test results table above
3. **Identify Gaps:** Note any domains with weak coverage
4. **Update Story:** Add test results and findings to story 3.10 file
5. **Create Validation Guide:** Generate epic validation guide (Story 3.12)

---

## References

- **Intent Router:** `api-service/app/services/intent_router.py`
- **Retrieval Service:** `api-service/app/services/retrieval_service.py`
- **Domain Definitions:** Lines 18-27 in intent_router.py
- **Story:** `docs/scrum/stories/3-10-all-7-knowledge-domains-operational.md`
- **Epic:** `docs/epics/epic-3-conversations-history.md`
