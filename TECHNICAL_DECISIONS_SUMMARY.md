# Technical Architecture Decisions Summary
## AI Powered PLC at Work Virtual Coach

**Organization:** Solution Tree
**Document Version:** 1.0
**Date:** 2025-11-12
**Status:** FINALIZED

---

## Quick Reference: All Technical Decisions

### Frontend & Backend Stack

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | **Frontend Framework** | **Vite + React (SPA)** | Simple architecture, fast dev experience, no SEO needed (internal tool), cheaper hosting (static files on S3) |
| 2 | **Backend Framework** | **Python FastAPI (unified)** | Single language backend, best for AI/ML integration, async support, auto-generated API docs |
| 3 | **Relational Database** | **PostgreSQL (AWS RDS)** | JSONB for flexible data, pgvector for embeddings, strong analytics support, ACID transactions |
| 4 | **Vector Database** | **pgvector (PostgreSQL extension)** | Simplest architecture (one database), zero additional cost, good performance for <1M vectors, easy backups |
| 5 | **Caching Strategy** | **PostgreSQL materialized views** | No additional service needed, good for analytics aggregations, use existing infrastructure |

### Authentication & AI

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 6 | **Authentication** | **Server-side sessions in PostgreSQL** | Instant logout/revocation, audit trail, one database (no Redis), better security than JWT for production |
| 7 | **AI Models** | **OpenAI GPT-4o + text-embedding-3-large** | Single API key, GPT-4o is 50% cheaper than GPT-4-turbo with same quality, best embeddings for retrieval |

### Infrastructure & Operations

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 8 | **Cloud Platform** | **AWS** | Enterprise-ready, best for education sector, mature services, strong compliance support |
| 9 | **Deployment** | **ECS Fargate + blue-green** | Serverless containers, auto-scaling, no server management, good for microservices |
| 10 | **Monitoring** | **CloudWatch only** | Sufficient for production, included with AWS, logs + metrics + alarms in one place |
| 11 | **Content Ingestion** | **Manual scripts → ECS task later** | MVP: manual (quarterly runs), Production: automated ECS scheduled task |
| 12 | **CI/CD** | **GitHub Actions** | Industry standard, free for private repos, simple YAML config, integrated with GitHub |
| 13 | **Error Handling** | **Retry (2x) + graceful errors** | Simple, handles transient failures, clear user feedback, can upgrade to circuit breaker later |
| 14 | **Rate Limiting** | **No limits for MVP (monitor)** | Trust users, learn patterns first, CloudWatch cost alarms, add limits only if needed |
| 15 | **Testing** | **Unit tests (critical paths)** | Test intent routing, retrieval, citations; skip UI/endpoints initially; ~40-50% coverage |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    USER (Web Browser)                        │
│                  Vite + React SPA                            │
│           (Hosted on S3 + CloudFront CDN)                    │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              Application Load Balancer (AWS)                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                 ECS Fargate (Python FastAPI)                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  API Service    │  │  AI Service     │  │  Ingestion   │ │
│  │  - Auth         │  │  - Intent route │  │  (quarterly) │ │
│  │  - Convos       │  │  - Retrieval    │  │              │ │
│  │  - Analytics    │  │  - Generation   │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└────┬────────────────────────┬────────────────────┬───────────┘
     │                        │                    │
     ▼                        ▼                    ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PostgreSQL   │    │   OpenAI API     │    │   S3 Storage    │
│   (RDS)      │    │                  │    │                 │
│              │    │  - GPT-4o        │    │  - PDFs         │
│ - Users      │    │  - text-embed-   │    │  - Exports      │
│ - Sessions   │    │    ding-3-large  │    │  - Backups      │
│ - Convos     │    │                  │    │                 │
│ - Messages   │    │  (Single API key)│    │                 │
│ - Embeddings │    │                  │    │                 │
│   (pgvector) │    └──────────────────┘    └─────────────────┘
└──────────────┘
      ▲
      │
      ▼
┌──────────────────┐
│   CloudWatch     │
│  - Logs          │
│  - Metrics       │
│  - Alarms        │
│  - Dashboards    │
└──────────────────┘
```

---

## Technology Stack Summary

### Frontend
- **Framework:** Vite 5 + React 18
- **Styling:** Tailwind CSS
- **State:** React Context + React Query
- **HTTP:** Axios
- **Validation:** Zod
- **Hosting:** AWS S3 + CloudFront

### Backend
- **Framework:** Python 3.11+ with FastAPI
- **ASGI Server:** Uvicorn
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **AI/ML:** LangChain, OpenAI SDK
- **Testing:** pytest, pytest-asyncio

### Infrastructure
- **Cloud:** AWS (us-east-1)
- **Compute:** ECS Fargate
- **Database:** RDS PostgreSQL 15
- **Storage:** S3
- **CDN:** CloudFront
- **Load Balancer:** Application Load Balancer
- **Monitoring:** CloudWatch
- **Secrets:** AWS Secrets Manager
- **CI/CD:** GitHub Actions

### External Services
- **AI:** OpenAI API (GPT-4o, text-embedding-3-large)
- **Auth:** Google OIDC, Clever SSO
- **Alerts:** Slack webhooks (optional)

---

## Database Schema (Key Tables)

### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    role VARCHAR DEFAULT 'educator',  -- educator, coach, admin
    organization_id UUID,
    sso_provider VARCHAR,
    sso_id VARCHAR,
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
```

### Sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    created_at TIMESTAMP,
    last_accessed_at TIMESTAMP
);
```

### Conversations
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR,
    status VARCHAR DEFAULT 'active',  -- active, archived
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Messages
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR,  -- user, assistant
    content TEXT,
    citations JSONB,
    domains VARCHAR[],
    feedback_score INT,  -- +1 or -1
    feedback_reasons TEXT[],
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL(10, 6),
    created_at TIMESTAMP
);
```

### Embeddings (pgvector)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    content TEXT,
    embedding vector(3072),  -- text-embedding-3-large
    metadata JSONB,  -- book_title, chapter, pages, domain, etc.
    created_at TIMESTAMP
);

CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## AI Pipeline Architecture

### Query Flow
```
User Question
    │
    ▼
[1. Embed Query]  OpenAI text-embedding-3-large
    │
    ▼
[2. Intent Classification]  GPT-4o function calling
    │  → Determine domain(s): assessment, collaboration, etc.
    ▼
[3. Retrieval]  pgvector semantic search
    │  → Top 7 chunks from relevant domains
    ▼
[4. Context Assembly]
    │  → Format chunks with metadata
    ▼
[5. Generation]  GPT-4o with context
    │  → Generate response with citations
    ▼
[6. Citation Extraction]
    │  → Parse and validate citations
    ▼
[7. Store Message]  PostgreSQL
    │  → Save user + assistant messages
    ▼
Response to User
```

### 7 Knowledge Domains
1. **Assessment & Evaluation** - formative/summative assessments, grading
2. **Collaborative Teams** - team structures, norms, meeting protocols
3. **Leadership & Administration** - principal guidance, change management
4. **Curriculum & Instruction** - guaranteed viable curriculum, instructional strategies
5. **Data Analysis & Response** - RTI, interventions, data-driven decisions
6. **School Culture & Systems** - PLC implementation, cultural shifts
7. **Student Learning & Engagement** - student-centered practices

---

## Cost Estimates

### Monthly Costs (500 active users)

| Service | Usage | Cost/Month |
|---------|-------|------------|
| **OpenAI API** | 150K queries × $0.02 | ~$3,000 |
| **ECS Fargate** | 2-10 tasks, ~720 hours | ~$100 |
| **RDS PostgreSQL** | db.t3.medium, Multi-AZ | ~$150 |
| **S3 + CloudFront** | Static files, CDN | ~$20 |
| **Load Balancer** | ALB | ~$20 |
| **CloudWatch** | Logs + metrics | ~$30 |
| **Secrets Manager** | 5 secrets | ~$2 |
| **Data Transfer** | Egress | ~$30 |
| **TOTAL** | | **~$3,350/month** |

**Per User Cost:** ~$6.70/month

### Annual Costs
- **Infrastructure:** ~$4,200/year
- **OpenAI API:** ~$36,000/year
- **Total:** ~$40,000/year for 500 users

**Cost Optimization:**
- Cache frequent queries (30% savings potential)
- Use materialized views for analytics (reduce DB load)
- Monitor and optimize token usage

---

## Security & Compliance

### Security Layers
1. **Network:** VPC, Security Groups, AWS Shield
2. **Transport:** TLS 1.3, HTTPS only, HSTS
3. **Application:** Session-based auth, RBAC, input validation, rate monitoring
4. **Data:** Encryption at rest (AWS KMS), encryption in transit

### Authentication Flow
```
User → Google/Clever OAuth
    ↓
Callback with code
    ↓
Exchange code for user info
    ↓
Check if user exists (by email)
    ↓
Create/update user (JIT provisioning)
    ↓
Create session in PostgreSQL
    ↓
Return session cookie (httpOnly, secure)
    ↓
User authenticated
```

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| **Educator** | Ask questions, view own conversations, share conversations, provide feedback |
| **Coach** | All educator permissions + view team analytics, export team data |
| **Admin** | All coach permissions + view system-wide analytics, manage user roles, access all reports |

### Compliance
- **FERPA:** No student data collected or stored
- **Data Privacy:** User conversations private by default
- **Audit Logging:** All data access logged

---

## Monitoring & Alerts

### CloudWatch Metrics (Custom)
- `api.response_time` (p50, p95, p99)
- `ai.generation_time`
- `database.query_time`
- `openai.cost_per_hour`
- `users.active_count`
- `feedback.positive_rate`

### Critical Alarms (→ PagerDuty/Slack)
- Error rate >5% for 5 minutes
- API p95 response time >10 seconds
- Database connection failures
- OpenAI API errors >10%

### Warning Alarms (→ Slack)
- Error rate >2% for 10 minutes
- Negative feedback >30% for 1 hour
- OpenAI cost >$100/hour
- Daily costs >$150

### Cost Monitoring
- Alert if daily OpenAI costs >$100
- Alert if any user costs >$10/day
- Alert if monthly costs >$3,000
- Weekly review of top 10 users

---

## Deployment Strategy

### Blue-Green Deployment
```
1. Build new version (green)
2. Deploy to ECS (green tasks start)
3. Run health checks
4. Shift 10% traffic to green
5. Monitor for 5 minutes
6. Shift 100% traffic to green
7. Keep blue running for 1 hour (rollback ready)
8. Terminate blue tasks
```

### CI/CD Pipeline (GitHub Actions)
```
Push to main branch
    ↓
Run unit tests (pytest)
    ↓
Build Docker images
    ↓
Push to AWS ECR
    ↓
Deploy to ECS Fargate
    ↓
Send Slack notification
```

### Rollback Procedure
```bash
# Instant rollback (switch to previous task definition)
aws ecs update-service \
  --cluster plc-coach-prod \
  --service api-service \
  --task-definition api-service:42  # previous version

# Recovery time: ~2 minutes
```

---

## Content Ingestion Strategy

### Phase 1 (MVP): Manual
```bash
# Engineer runs quarterly
python scripts/ingest_content.py \
  --s3-bucket plc-coach-content \
  --database-url $DATABASE_URL \
  --openai-key $OPENAI_API_KEY

# Takes 2-4 hours, runs in background
```

### Phase 2 (Production): Automated
```
EventBridge Schedule (quarterly: Jan, Apr, Jul, Oct)
    ↓
Triggers ECS Fargate Task
    ↓
Downloads PDFs from S3
    ↓
Processes with Python script:
    - Extract text (PyMuPDF)
    - Clean and chunk (500-1000 tokens)
    - Generate embeddings (OpenAI API)
    - Store in PostgreSQL (pgvector)
    ↓
Send Slack notification
    ↓
CloudWatch logs for debugging
```

**Cost per quarterly run:** ~$3.50 (embeddings + compute)

---

## Testing Strategy

### What to Test (Unit Tests)
✅ **Intent routing** - Classify queries to correct domains
✅ **Retrieval** - Return relevant chunks from pgvector
✅ **Citation extraction** - Parse citations from responses
✅ **Session management** - Create/retrieve sessions

### What to Skip (for MVP)
❌ UI components (manual testing)
❌ API endpoint routing (manual testing)
❌ Database migrations (manual testing)
❌ Authentication flows (manual testing)

### Test Coverage Target
- **Critical paths:** 80%+ coverage
- **Overall codebase:** 40-50% coverage
- **CI/CD:** Tests must pass before deploy

```yaml
# GitHub Actions
- name: Run tests
  run: |
    pytest tests/ --cov=src --cov-report=term-missing
    # Only deploy if tests pass
```

---

## Error Handling

### OpenAI API Failures
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def call_openai(messages):
    return await openai.ChatCompletion.create(...)

# If all retries fail:
return {
    "error": "AI coach temporarily unavailable. Please try again in a moment."
}
```

### Database Failures
- Multi-AZ RDS (automatic failover in ~1 minute)
- Connection pooling with retries
- Graceful degradation (read-only mode if write fails)

### Service Failures
- Health checks every 30 seconds
- Auto-restart unhealthy containers
- Alert if >2 restarts in 10 minutes

---

## Disaster Recovery

### Backup Strategy
- **Database:** Automated snapshots daily, 30-day retention, PITR enabled
- **Embeddings:** Can rebuild from S3 PDFs in 24 hours
- **S3 Content:** Versioning enabled, cross-region replication

### Recovery Objectives
- **RTO (Recovery Time):** 4 hours
- **RPO (Recovery Point):** 1 hour
- **Multi-AZ:** Automatic failover for database

### Recovery Procedures
1. **Database failure:** Multi-AZ auto-failover (~1 min)
2. **Application failure:** ECS auto-scaling launches new containers (~2 min)
3. **Region failure:** Failover to us-west-2 DR region (~2-4 hours)

---

## Scalability Considerations

### Current Capacity (MVP Configuration)
- **Users:** 100-1,000 concurrent
- **Requests:** ~500 requests/minute
- **Database:** db.t3.medium handles ~100 connections
- **Vector search:** <100ms for <1M vectors

### Scaling Triggers
| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU usage | >70% for 5 min | Scale up ECS tasks |
| Database connections | >80 of 100 | Upgrade RDS instance |
| Response time p95 | >5 seconds | Add caching (Redis) |
| Vectors | >1M | Migrate to Pinecone |

### Future Scaling Options
- **Horizontal:** Add more ECS tasks (2 → 10)
- **Vertical:** Upgrade RDS (t3.medium → t3.large)
- **Caching:** Add Redis/ElastiCache
- **Vector DB:** Migrate to Pinecone if >1M vectors
- **CDN:** Already using CloudFront (global)

---

## Next Steps: Implementation Order

### Epic 1: Foundation (Weeks 1-3)
1. Set up AWS infrastructure (VPC, RDS, S3, ECS)
2. Implement Google/Clever SSO with session management
3. Basic React frontend with authentication
4. Health checks and monitoring

### Epic 2: Core AI Coach (Weeks 4-8)
1. Content ingestion pipeline (manual scripts)
2. Process 15-20 books → pgvector
3. Implement intent routing (GPT-4o)
4. Implement retrieval (pgvector search)
5. Implement generation with citations
6. Basic chat UI

### Epic 3: Conversations & History (Weeks 9-11)
1. Multi-turn conversation context
2. Conversation persistence and history
3. Conversation sidebar UI
4. Share conversation feature

### Epic 4: Polish & Analytics (Weeks 12-14)
1. Feedback mechanism (thumbs up/down)
2. Analytics dashboards (role-based)
3. Performance optimization
4. Security audit
5. Production readiness

**Total Timeline:** 10-14 weeks to MVP

---

## Key Contacts & Resources

### Documentation
- PRD: `PRD_Solution_Tree_PLC_Coach_Detailed.md`
- Technical Architecture: `TECHNICAL_ARCHITECTURE.md`
- This Summary: `TECHNICAL_DECISIONS_SUMMARY.md`

### External Documentation
- OpenAI API: https://platform.openai.com/docs
- FastAPI: https://fastapi.tiangolo.com
- pgvector: https://github.com/pgvector/pgvector
- React Query: https://tanstack.com/query
- AWS ECS: https://docs.aws.amazon.com/ecs

### Decision Log
All 15 technical decisions were made on 2025-11-12 in collaboration with stakeholders.

---

## Appendix: Decision Rationale Quick Reference

**Why Vite over Next.js?**
Internal tool, no SEO needed, simpler architecture, faster dev experience

**Why FastAPI over Node.js?**
Single language backend, better AI/ML ecosystem integration, async support

**Why pgvector over Pinecone?**
Simpler (one database), cheaper ($0 vs $70/month), good enough for <1M vectors

**Why server sessions over JWT?**
Production security (instant revocation), audit trail, simpler with PostgreSQL

**Why no rate limits for MVP?**
Trust users, learn patterns, CloudWatch monitors costs, can add in 30 min if needed

**Why manual ingestion for MVP?**
Quarterly updates = 4 times/year, automate when it becomes painful, learn process first

**Why CloudWatch only?**
Sufficient for production, included with AWS, no additional service to manage

**Why unit tests not E2E?**
Test critical paths (AI logic), skip UI initially, balance speed vs. coverage

---

**End of Document**

*For questions or updates, contact the Engineering Team.*
