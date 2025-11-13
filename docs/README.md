# PLC Coach Documentation

**Project:** AI Powered PLC at Work Virtual Coach
**Organization:** Solution Tree
**Last Updated:** 2025-11-13

---

## Quick Start

👋 **New to the project?** Start here:
1. [Project Overview](01-project/project-overview.md) - What is PLC Coach?
2. [Developer Onboarding](07-handoff/developer-onboarding.md) - Set up your environment
3. [Technical Architecture](01-project/TECHNICAL_ARCHITECTURE.md) - System design
4. [Current Sprint](02-planning/sprint-status.yaml) - What we're working on

---

## Documentation Structure

Our documentation follows a numbered structure for easy navigation:

### 📋 01 - Project Documentation
High-level project documents, requirements, and architecture.

**Key Documents:**
- [Product Requirements (PRD)](01-project/PRD.md)
- [Technical Architecture](01-project/TECHNICAL_ARCHITECTURE.md)
- [Technical Decisions](01-project/TECHNICAL_DECISIONS_SUMMARY.md)

[Browse All →](01-project/)

---

### 📅 02 - Planning
Epics, user stories, and sprint tracking.

**Current Work:**
- [Epic 1: Foundation & Authentication](02-planning/epics/epic-1-foundation-authentication.md) - **IN PROGRESS**
  - [Story 1.1: Infrastructure Setup](02-planning/stories/1-1-project-infrastructure-setup.md) ✅ Complete
  - [Story 1.2: Database Schema](02-planning/stories/1-2-database-schema-creation.md) ✅ Complete
  - Story 1.3: Backend API Foundation - **NEXT**

**All Epics:**
- [Epic 2: Core AI Coach](02-planning/epics/epic-2-core-ai-coach.md)
- [Epic 3: Conversations & History](02-planning/epics/epic-3-conversations-history.md)
- [Epic 4: Analytics & Polish](02-planning/epics/epic-4-analytics-feedback-polish.md)

[Browse All →](02-planning/)

---

### 🔧 03 - Implementation Guides
Detailed technical implementation documentation.

**By Component:**
- **Database:** Schema design, migrations, ER diagrams
- **Backend:** API design, authentication, error handling
- **Frontend:** Components, state management, routing
- **Infrastructure:** AWS setup, deployment, security

[Browse All →](03-implementation/)

---

### ✅ 04 - Validation & Testing
Test plans, validation guides, and acceptance criteria verification.

**Epic 1 Validation:**
- [Story 1.1: Infrastructure Validation](04-validation/epic1/1-1-infrastructure-validation.md) ✅
- [Story 1.2: Database Schema Validation](04-validation/epic1/1-2-database-schema-validation.md) ✅

[Browse All →](04-validation/)

---

### 🚀 05 - Operations
Deployment guides, runbooks, monitoring, and troubleshooting.

**Quick Links:**
- [Deployment Guide](05-operations/runbooks/deployment.md)
- [Rollback Procedure](05-operations/runbooks/rollback.md)
- [Common Issues](05-operations/troubleshooting/common-issues.md)
- [Monitoring Setup](05-operations/monitoring/cloudwatch-setup.md)

[Browse All →](05-operations/)

---

### 📡 06 - API Documentation
REST API endpoints, authentication, and integration guides.

**Endpoints:**
- [Authentication API](06-api/authentication.md)
- [Conversations API](06-api/conversations.md)
- [Messages API](06-api/messages.md)
- [OpenAPI Specification](06-api/openapi.yaml)

[Browse All →](06-api/)

---

### 🎓 07 - Handoff & Onboarding
Knowledge transfer documents for new team members.

**Get Started:**
- [Developer Onboarding](07-handoff/developer-onboarding.md)
- [Project Setup](07-handoff/project-setup.md)
- [Architecture Walkthrough](07-handoff/architecture-walkthrough.md)

[Browse All →](07-handoff/)

---

### 📊 08 - Reports & Status
Progress reports, retrospectives, and status updates.

**Recent Reports:**
- [Implementation Readiness Report - 2025-11-12](08-reports/implementation-readiness-report-2025-11-12.md)

**Weekly Status:**
- Week of 2025-11-11: Epic 1 Stories 1.1, 1.2 Complete

[Browse All →](08-reports/)

---

### 📦 09 - Archive
Historical documents and deprecated designs.

[Browse All →](09-archive/)

---

## How to Find What You Need

### I'm a Developer
```
New to project?
  → 07-handoff/developer-onboarding.md
  → 01-project/TECHNICAL_ARCHITECTURE.md

Building a feature?
  → 02-planning/stories/[your-story].md
  → 03-implementation/[component]/

Deploying?
  → 05-operations/runbooks/deployment.md

Debugging?
  → 05-operations/troubleshooting/common-issues.md
```

### I'm a Product Owner
```
Requirements?
  → 01-project/PRD.md

Planning?
  → 02-planning/epics/
  → 02-planning/sprint-status.yaml

Progress?
  → 08-reports/weekly-status/
  → 04-validation/[epic]/
```

### I'm a DevOps Engineer
```
Infrastructure?
  → 03-implementation/infrastructure/
  → 05-operations/runbooks/

Monitoring?
  → 05-operations/monitoring/
  → 05-operations/troubleshooting/

Deployment?
  → 05-operations/runbooks/deployment.md
```

---

## Documentation Standards

📖 **Read this before contributing:**
- [Documentation Structure Guide](DOCUMENTATION_STRUCTURE.md) - Organization and naming conventions
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute

### Quick Rules
1. ✅ Use descriptive file names with hyphens: `my-document.md`
2. ✅ Include metadata at the top of each document
3. ✅ Link to related documents
4. ✅ Update README files when adding new docs
5. ✅ Archive deprecated docs to `09-archive/`

---

## Project Status

### Current Sprint: Epic 1 - Foundation & Authentication
**Timeline:** 2025-11-11 to 2025-11-29 (2-3 weeks)

**Completed:**
- ✅ Story 1.1: Project Infrastructure Setup
- ✅ Story 1.2: Database Schema Creation

**In Progress:**
- 🔄 Story 1.3: Backend API Service Foundation

**Upcoming:**
- ⏳ Story 1.4: Google OIDC Authentication
- ⏳ Story 1.5: Clever SSO Authentication

**Progress:** 2 of 9 stories complete (22%)

[View Detailed Status →](02-planning/sprint-status.yaml)

---

## Key Links

### External Resources
- **AWS Console:** [us-east-1](https://console.aws.amazon.com/console/home?region=us-east-1)
- **RDS Database:** plccoach-db.crws0amqe1e3.us-east-1.rds.amazonaws.com
- **GitHub Repository:** [reena96/plccoach](https://github.com/reena96/plccoach)

### Important Documents
- [PRD](01-project/PRD.md) - Product Requirements
- [Architecture](01-project/TECHNICAL_ARCHITECTURE.md) - System Design
- [Sprint Status](02-planning/sprint-status.yaml) - Current Work

---

## Getting Help

### Documentation Issues
- Missing documentation? Create an issue
- Wrong information? Submit a PR
- Can't find something? Check [DOCUMENTATION_STRUCTURE.md](DOCUMENTATION_STRUCTURE.md)

### Technical Issues
- See [Troubleshooting Guide](05-operations/troubleshooting/common-issues.md)
- Check [Runbooks](05-operations/runbooks/)
- Review [Architecture](01-project/TECHNICAL_ARCHITECTURE.md)

---

## Changelog

### 2025-11-13
- ✨ Created new documentation structure
- 📝 Defined organization standards
- 🎯 Completed Story 1.2: Database Schema Creation
- 📋 Updated validation documents

### 2025-11-12
- ✅ Completed Story 1.1: Infrastructure Setup
- 📊 Created implementation readiness report
- 🏗️ Deployed AWS infrastructure

[View Full Changelog →](CHANGELOG.md)

---

**Need to reorganize docs?** See [DOCUMENTATION_STRUCTURE.md](DOCUMENTATION_STRUCTURE.md)
