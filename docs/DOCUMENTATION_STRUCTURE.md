# PLC Coach Documentation Structure

**Last Updated:** 2025-11-13
**Maintained By:** Development Team
**Purpose:** Define and maintain a clear, intuitive documentation structure for the PLC Coach project

---

## Overview

This document defines the canonical documentation structure for the PLC Coach project. All documentation must follow this structure to ensure consistency and ease of navigation.

---

## Directory Structure

```
docs/
├── README.md                          # Documentation index and navigation guide
├── DOCUMENTATION_STRUCTURE.md         # This file - documentation organization guide
│
├── 01-project/                        # Project-level documentation
│   ├── PRD.md                         # Product Requirements Document
│   ├── TECHNICAL_ARCHITECTURE.md      # System architecture and design
│   ├── TECHNICAL_DECISIONS_SUMMARY.md # Key technical decisions and rationale
│   └── project-overview.md            # High-level project summary
│
├── 02-planning/                       # Sprint and epic planning
│   ├── epics/
│   │   ├── epic-1-foundation-authentication.md
│   │   ├── epic-2-core-ai-coach.md
│   │   ├── epic-3-conversations-history.md
│   │   └── epic-4-analytics-feedback-polish.md
│   ├── stories/
│   │   ├── 1-1-project-infrastructure-setup.md
│   │   ├── 1-2-database-schema-creation.md
│   │   ├── 1-3-backend-api-foundation.md
│   │   └── ... (organized by epic.story)
│   └── sprint-status.yaml             # Current sprint tracking
│
├── 03-implementation/                 # Implementation guides and decisions
│   ├── database/
│   │   ├── schema-design.md
│   │   ├── migrations-guide.md
│   │   └── er-diagram.png
│   ├── backend/
│   │   ├── api-design.md
│   │   ├── authentication.md
│   │   └── error-handling.md
│   ├── frontend/
│   │   ├── component-structure.md
│   │   └── state-management.md
│   └── infrastructure/
│       ├── aws-setup.md
│       ├── deployment-guide.md
│       └── security-configuration.md
│
├── 04-validation/                     # Testing and validation
│   ├── epic1/
│   │   ├── 1-1-infrastructure-validation.md
│   │   └── 1-2-database-schema-validation.md
│   ├── epic2/
│   ├── epic3/
│   ├── epic4/
│   └── validation-template.md         # Template for new validation docs
│
├── 05-operations/                     # Operational documentation
│   ├── runbooks/
│   │   ├── deployment.md
│   │   ├── rollback.md
│   │   ├── database-maintenance.md
│   │   └── incident-response.md
│   ├── monitoring/
│   │   ├── cloudwatch-setup.md
│   │   └── alerting-guide.md
│   └── troubleshooting/
│       ├── common-issues.md
│       └── debug-guide.md
│
├── 06-api/                            # API documentation
│   ├── openapi.yaml                   # OpenAPI specification
│   ├── authentication.md              # Auth endpoints
│   ├── conversations.md               # Conversation endpoints
│   └── messages.md                    # Message endpoints
│
├── 07-handoff/                        # Knowledge transfer and onboarding
│   ├── developer-onboarding.md
│   ├── project-setup.md
│   └── architecture-walkthrough.md
│
├── 08-reports/                        # Status reports and assessments
│   ├── implementation-readiness-report-2025-11-12.md
│   ├── weekly-status/
│   └── retrospectives/
│
└── 09-archive/                        # Deprecated or historical docs
    └── old-designs/
```

---

## File Naming Conventions

### General Rules
- Use lowercase with hyphens: `my-document-name.md`
- Be descriptive but concise
- Include dates for time-sensitive docs: `YYYY-MM-DD-description.md`
- Use prefixes for numbered sequences: `01-first-step.md`, `02-second-step.md`

### Story and Epic Files
- **Epics:** `epic-{number}-{brief-name}.md`
  - Example: `epic-1-foundation-authentication.md`
- **Stories:** `{epic}-{story}-{brief-name}.md`
  - Example: `1-2-database-schema-creation.md`
- **Validation:** `{epic}-{story}-validation.md`
  - Example: `1-2-database-schema-validation.md`

### Date-Based Files
- **Format:** `YYYY-MM-DD-description.md`
- **Example:** `2025-11-13-sprint-retrospective.md`

---

## Document Templates

### Story Template Location
`docs/02-planning/templates/story-template.md`

### Validation Template Location
`docs/04-validation/validation-template.md`

### Runbook Template Location
`docs/05-operations/runbooks/runbook-template.md`

---

## Migration Plan

### Phase 1: Create New Structure (Immediate)
```bash
# Create new directory structure
mkdir -p docs/{01-project,02-planning/{epics,stories},03-implementation/{database,backend,frontend,infrastructure},04-validation/{epic1,epic2,epic3,epic4},05-operations/{runbooks,monitoring,troubleshooting},06-api,07-handoff,08-reports/{weekly-status,retrospectives},09-archive}

# Create index files
touch docs/{01-project,02-planning,03-implementation,04-validation,05-operations,06-api,07-handoff,08-reports}/README.md
```

### Phase 2: Move Existing Files (Current Sprint)
```bash
# Move project docs
mv docs/TECHNICAL_ARCHITECTURE.md docs/01-project/
mv docs/TECHNICAL_DECISIONS_SUMMARY.md docs/01-project/
mv docs/PRD.md docs/01-project/

# Move epics (keep current location for now, symlink to new)
cp -r docs/epics/* docs/02-planning/epics/

# Move stories
cp -r docs/stories/* docs/02-planning/stories/

# Move sprint tracking
mv docs/scrum/sprint-status.yaml docs/02-planning/

# Move infrastructure docs
mv docs/infrastructure.md docs/03-implementation/infrastructure/aws-setup.md

# Move validation docs
mv docs/validation/epic1_1-1_validation.md docs/04-validation/epic1/1-1-infrastructure-validation.md
mv docs/validation/epic1_1-2_validation.md docs/04-validation/epic1/1-2-database-schema-validation.md

# Move reports
mv docs/implementation-readiness-report-2025-11-12.md docs/08-reports/
```

### Phase 3: Update References (Next Sprint)
- Update all internal documentation links
- Update README files with new paths
- Create symbolic links for backward compatibility
- Update CI/CD scripts that reference doc paths

### Phase 4: Cleanup (After Epic 1)
- Remove old directory structure
- Remove symbolic links
- Archive deprecated docs to `09-archive/`

---

## Documentation Standards

### Markdown Format
- Use ATX-style headers (`#` not `===`)
- Include a YAML frontmatter for metadata:
  ```yaml
  ---
  title: Document Title
  author: Author Name
  date: 2025-11-13
  epic: 1
  story: 1.2
  status: in-progress | completed | archived
  ---
  ```

### Required Sections
All documents should include:
1. **Title** (H1)
2. **Metadata** (date, author, status)
3. **Purpose/Overview**
4. **Content** (varies by document type)
5. **Related Documents** (links to dependencies)
6. **Changelog** (for living documents)

### Cross-References
- Use relative paths: `[Epic 1](../02-planning/epics/epic-1-foundation-authentication.md)`
- Include section anchors: `[Database Schema](#database-schema)`
- Keep a link index at the bottom of key documents

---

## README Files

Each major directory should have a README.md with:

### Template
```markdown
# {Directory Name}

**Purpose:** Brief description of what this directory contains

## Contents

- **file-name.md** - Brief description
- **subdirectory/** - Brief description

## Navigation

- **Up:** [Parent Directory](../README.md)
- **Related:** [Other Relevant Section](../other-section/README.md)

## Guidelines

Specific guidelines for documents in this directory
```

---

## Maintenance

### Responsibilities
- **Product Owner:** Maintains planning docs (epics, stories)
- **Tech Lead:** Maintains implementation and architecture docs
- **DevOps:** Maintains operations and runbooks
- **Team:** All validation docs and reports

### Review Cycle
- **Weekly:** Update sprint-status.yaml
- **Sprint End:** Create retrospective report
- **Epic Complete:** Archive completed validation docs
- **Release:** Update all operational docs

### Deprecated Documents
When a document becomes outdated:
1. Add `[DEPRECATED]` to the title
2. Add deprecation notice at top with link to replacement
3. Move to `09-archive/` after one sprint
4. Update all references to point to new document

---

## Quick Navigation

### For Developers
1. **Getting Started:** `07-handoff/developer-onboarding.md`
2. **Architecture:** `01-project/TECHNICAL_ARCHITECTURE.md`
3. **Current Sprint:** `02-planning/sprint-status.yaml`
4. **API Docs:** `06-api/`

### For Product
1. **PRD:** `01-project/PRD.md`
2. **Epics:** `02-planning/epics/`
3. **Stories:** `02-planning/stories/`
4. **Progress:** `08-reports/weekly-status/`

### For DevOps
1. **Deployment:** `05-operations/runbooks/deployment.md`
2. **Infrastructure:** `03-implementation/infrastructure/`
3. **Monitoring:** `05-operations/monitoring/`
4. **Troubleshooting:** `05-operations/troubleshooting/`

---

## Implementation Status

### Current Structure (Before Reorganization)
```
docs/
├── epics/                  # ✅ Exists
├── stories/                # ✅ Exists
├── validation/             # ✅ Exists
├── scrum/                  # ✅ Exists
├── technical/              # ⚠️ Empty
├── handoff/                # ⚠️ Empty
├── infrastructure.md       # ✅ Exists
└── various reports         # ✅ Scattered
```

### New Structure (After Reorganization)
```
docs/
├── 01-project/            # 🔄 To be created
├── 02-planning/           # 🔄 Consolidates epics, stories, scrum
├── 03-implementation/     # 🔄 New - detailed guides
├── 04-validation/         # 🔄 Reorganize by epic
├── 05-operations/         # 🔄 New - runbooks
├── 06-api/                # 🔄 New - API docs
├── 07-handoff/            # 🔄 Populate with onboarding
├── 08-reports/            # 🔄 Consolidate reports
└── 09-archive/            # 🔄 New - historical docs
```

**Status Legend:**
- ✅ Exists and populated
- ⚠️ Exists but empty
- 🔄 Needs to be created or reorganized

---

## Changelog

### 2025-11-13
- Initial documentation structure defined
- Created reorganization plan
- Established naming conventions and standards
- Defined maintenance responsibilities

---

## Related Documents

- **Main README:** `../README.md`
- **Contributing Guide:** `../CONTRIBUTING.md` (to be created)
- **Development Setup:** `07-handoff/project-setup.md` (to be created)
