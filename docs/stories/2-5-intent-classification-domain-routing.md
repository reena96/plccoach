# Story 2.5: Intent Classification & Domain Routing

**Epic:** Epic 2 - Core AI Coach
**Story ID:** 2-5-intent-classification-domain-routing
**Created:** 2025-11-14
**Status:** backlog

## User Story

**As a** backend developer,
**I want** to classify user queries into knowledge domains,
**So that** retrieval can be targeted to the most relevant content areas.

## Acceptance Criteria

**Given** a user submits a query
**When** the intent classification service processes it
**Then** GPT-4o function calling is used to classify the query into:
- Primary domain (required): one of 7 domains
- Secondary domains (optional): array of additional relevant domains
- needs_clarification (boolean): true if query is too vague

**And** the 7 domains are:
1. assessment - formative/summative assessments, grading
2. collaboration - team structures, norms, protocols
3. leadership - principal/admin guidance, change management
4. curriculum - guaranteed viable curriculum, standards
5. data_analysis - RTI, interventions, MTSS
6. school_culture - PLC implementation, culture shifts
7. student_learning - student-centered practices

**Given** a clear query like "What are common formative assessments?"
**Then** classification returns:
```json
{
  "primary_domain": "assessment",
  "secondary_domains": ["collaboration"],
  "needs_clarification": false
}
```

**Given** a vague query like "How do I do PLCs?"
**Then** classification returns:
```json
{
  "primary_domain": "collaboration",
  "secondary_domains": [],
  "needs_clarification": true,
  "clarification_question": "Are you asking about establishing team norms, structuring meetings, or implementing the PLC process?"
}
```

**And** the classification uses temperature=0.1 for consistency

**And** the function calling schema is defined per TECHNICAL_ARCHITECTURE.md Section 4.1

## Prerequisites

- Story 1.3 (backend API foundation)

## Technical Notes

- Implement in `/app/services/intent_router.py`
- Use OpenAI GPT-4o with function calling
- Cache classifications for identical queries (1 hour TTL)
- Log all classifications for quality monitoring

## Definition of Done

- [ ] Intent router service implemented
- [ ] 7 domains classified correctly
- [ ] Vague query detection working
- [ ] Function calling schema defined
- [ ] Caching implemented
- [ ] Unit tests passing
- [ ] Validation guide created
