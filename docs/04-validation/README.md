# Validation & Testing Documentation

**Purpose:** Test plans, validation guides, and acceptance criteria verification

---

## Overview

Each story has a corresponding validation document that provides:
- Quick 30-second test
- Automated test coverage
- Manual validation steps
- Edge cases and error handling
- Rollback procedures

---

## Contents by Epic

### Epic 1: Foundation & Authentication

**Completed:**
- [1.1: Infrastructure Validation](epic1/1-1-infrastructure-validation.md) ✅
- [1.2: Database Schema Validation](epic1/1-2-database-schema-validation.md) ✅

**Upcoming:**
- 1.3: Backend API Foundation
- 1.4: Google OIDC Authentication
- 1.5: Clever SSO Authentication

[Browse Epic 1 →](epic1/)

### Epic 2: Core AI Coach
[Browse Epic 2 →](epic2/)

### Epic 3: Conversations & History
[Browse Epic 3 →](epic3/)

### Epic 4: Analytics & Polish
[Browse Epic 4 →](epic4/)

---

## Validation Process

### 1. Before Starting Story
- Review acceptance criteria
- Identify testable scenarios
- Plan validation approach

### 2. During Development
- Write tests alongside code
- Run tests continuously
- Document any deviations

### 3. Story Complete
- Run 30-second quick test
- Execute full validation guide
- Document results
- Get sign-off

### 4. Epic Complete
- Run end-to-end tests
- Verify all integrations
- Performance testing
- Security audit

---

## Templates

- [Validation Template](validation-template.md) - Use for new stories

---

## Navigation

- **Up:** [Main Documentation](../README.md)
- **Related:**
  - [Planning](../02-planning/) - Stories and acceptance criteria
  - [Implementation](../03-implementation/) - Technical guides
  - [Operations](../05-operations/) - Deployment validation

---

## Guidelines

### Creating Validation Docs
1. Use template: `validation-template.md`
2. Name format: `{epic}-{story}-validation.md`
3. Include all sections from template
4. Link back to story document

### Running Validations
1. Start with 30-second quick test
2. If quick test passes, run full validation
3. Document any failures
4. Update story status only when validation passes

### Sign-Off
- Developer: Runs validation, fixes issues
- Reviewer: Verifies validation results
- Product Owner: Confirms acceptance criteria met
