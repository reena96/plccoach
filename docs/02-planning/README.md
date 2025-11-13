# Planning Documentation

**Purpose:** Sprint planning, epics, user stories, and sprint tracking

---

## Current Sprint

**Sprint Status:** [sprint-status.yaml](sprint-status.yaml)

**Active Epic:** Epic 1 - Foundation & Authentication
**Progress:** 2 of 9 stories complete (22%)

---

## Contents

### Epics
High-level feature groupings spanning 2-4 weeks each.

- [Epic 1: Foundation & Authentication](epics/epic-1-foundation-authentication.md) - **IN PROGRESS**
- [Epic 2: Core AI Coach](epics/epic-2-core-ai-coach.md)
- [Epic 3: Conversations & History](epics/epic-3-conversations-history.md)
- [Epic 4: Analytics & Polish](epics/epic-4-analytics-feedback-polish.md)

[Browse All Epics →](epics/)

### Stories
User stories with acceptance criteria, organized by epic.

**Epic 1 Stories:**
- [1.1: Project Infrastructure Setup](stories/1-1-project-infrastructure-setup.md) ✅
- [1.2: Database Schema Creation](stories/1-2-database-schema-creation.md) ✅
- 1.3: Backend API Service Foundation - **NEXT**
- 1.4-1.9: Authentication and deployment stories

[Browse All Stories →](stories/)

### Templates
- [Story Template](templates/story-template.md)
- [Epic Template](templates/epic-template.md)

---

## Navigation

- **Up:** [Main Documentation](../README.md)
- **Related:**
  - [Validation](../04-validation/) - Test acceptance criteria
  - [Implementation](../03-implementation/) - Technical guides
  - [Reports](../08-reports/) - Progress tracking

---

## Guidelines

### Creating New Epics
1. Use template: `templates/epic-template.md`
2. Name format: `epic-{number}-{brief-name}.md`
3. Include: Goal, stories, completion criteria, dependencies

### Creating New Stories
1. Use template: `templates/story-template.md`
2. Name format: `{epic}-{story}-{brief-name}.md`
3. Include: User story, acceptance criteria, technical notes
4. Link to parent epic

### Sprint Tracking
- Update `sprint-status.yaml` daily
- Mark stories complete when all ACs met
- Create validation doc before marking complete
