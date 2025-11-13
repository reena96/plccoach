# AI Powered PLC at Work Virtual Coach
## Technical Architecture Document

**Organization:** Solution Tree
**Project ID:** QS6bbY3IK5hYXLdWZ9sB_1762208994432
**Document Version:** 1.1 (FINALIZED)
**Last Updated:** 2025-11-12
**Document Owner:** Engineering Team
**Status:** ✅ All architectural decisions finalized

---

## Executive Summary: Finalized Technical Decisions

This document reflects **15 finalized architectural decisions** made during technical planning.

### Quick Reference

| Category | Decision | Choice |
|----------|----------|--------|
| **Frontend** | Framework | Vite + React (SPA) |
| **Backend** | Framework | Python FastAPI (unified) |
| **Database** | Relational | PostgreSQL (AWS RDS) |
| **Database** | Vector | pgvector (PostgreSQL extension) |
| **Caching** | Strategy | PostgreSQL materialized views |
| **Authentication** | Method | Server-side sessions in PostgreSQL |
| **AI Models** | LLM + Embeddings | OpenAI GPT-4o + text-embedding-3-large |
| **Cloud** | Platform | AWS (ECS Fargate, RDS, S3, CloudFront) |
| **Deployment** | Strategy | ECS Fargate with blue-green deployment |
| **Monitoring** | Tools | CloudWatch only (sufficient for production) |
| **Content Ingestion** | Approach | Manual scripts (MVP) → ECS scheduled task (production) |
| **CI/CD** | Pipeline | GitHub Actions |
| **Error Handling** | Strategy | Retry (2x) + graceful error messages |
| **Rate Limiting** | Policy | No limits for MVP (CloudWatch cost monitoring) |
| **Testing** | Coverage | Unit tests on critical paths (40-50% coverage) |

**See `TECHNICAL_DECISIONS_SUMMARY.md` for detailed rationale on each decision.**

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [System Components](#2-system-components)
3. [Data Architecture](#3-data-architecture)
4. [AI/ML Architecture](#4-aiml-architecture)
5. [API Specifications](#5-api-specifications)
6. [Security Architecture](#6-security-architecture)
7. [Infrastructure & Deployment](#7-infrastructure--deployment)
8. [Data Flow Diagrams](#8-data-flow-diagrams)
9. [Scalability & Performance](#9-scalability--performance)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [Disaster Recovery](#11-disaster-recovery)
12. [Technology Stack Summary](#12-technology-stack-summary)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser (Vite + React SPA)                                 │
│  - Desktop, Tablet, Mobile responsive                           │
│  - HTTPS/TLS 1.3 encryption                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CDN & LOAD BALANCER                        │
├─────────────────────────────────────────────────────────────────┤
│  AWS CloudFront (CDN) + Application Load Balancer               │
│  - SSL/TLS termination                                          │
│  - DDoS protection (AWS Shield)                                 │
│  - Rate limiting                                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Kong / AWS API Gateway                                         │
│  - Authentication verification                                  │
│  - Request routing                                              │
│  - Rate limiting per user                                       │
│  - Request/response logging                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Auth Service    │  │  API Service     │  │  AI Service  │ │
│  │  (Node.js)       │  │  (Python FastAPI)│  │  (Python)    │ │
│  │                  │  │                  │  │              │ │
│  │ - Google OIDC    │  │ - Conversations  │  │ - Intent     │ │
│  │ - Clever SSO     │  │ - User mgmt      │  │   routing    │ │
│  │ - Session mgmt   │  │ - Analytics      │  │ - Retrieval  │ │
│  │ - JIT provision  │  │ - Feedback       │  │ - Generation │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                                                                 │
└────┬────────────────────────┬────────────────────────┬─────────┘
     │                        │                        │
     ▼                        ▼                        ▼
┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  PostgreSQL │    │  Vector Database │    │   OpenAI API     │
│     (RDS)   │    │  (Pinecone/      │    │                  │
│             │    │   Weaviate)      │    │  - GPT-4-turbo   │
│ - Users     │    │                  │    │  - Embeddings    │
│ - Convos    │    │  - 7 Domain      │    │    (3-large)     │
│ - Messages  │    │    Indexes       │    │                  │
│ - Analytics │    │  - Book chunks   │    │                  │
└─────────────┘    └──────────────────┘    └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE & MONITORING                         │
├─────────────────────────────────────────────────────────────────┤
│  AWS S3                    │  AWS CloudWatch                    │
│  - Original PDFs           │  - Logs                            │
│  - Processed content       │  - Metrics                         │
│  - Export files            │  - Alarms                          │
│  - Backups                 │  - Dashboards                      │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Architectural Principles

1. **Separation of Concerns**: Each service has a single, well-defined responsibility
2. **Stateless Services**: Application layer services are stateless for horizontal scaling
3. **API-First Design**: All services communicate via well-defined REST APIs
4. **Eventual Consistency**: Analytics data can be slightly delayed for performance
5. **Defense in Depth**: Multiple layers of security (network, application, data)
6. **Observability**: Comprehensive logging, metrics, and tracing
7. **Cost Optimization**: Cache aggressively, monitor OpenAI API usage

### 1.3 Design Patterns

- **Microservices**: Separate auth, API, and AI services
- **Gateway Pattern**: Single entry point via API Gateway
- **Repository Pattern**: Data access abstraction
- **Circuit Breaker**: Protect against OpenAI API failures
- **Retry with Backoff**: Handle transient failures
- **Cache-Aside**: Redis for frequently accessed data

---

## 2. System Components

### 2.1 Frontend Application

**Technology**: Vite 5 with React 18 (SPA)

**Decision Rationale:** Chosen over Next.js because this is an internal, authenticated tool with no SEO requirements. Vite provides faster development experience, simpler architecture, and cheaper hosting (static files on S3).

**Key Features**:
- Client-Side Rendering (CSR) for interactive chat
- Optimistic UI updates for fast perceived performance
- Lightning-fast HMR (Hot Module Replacement)
- Static build output hosted on S3 + CloudFront

**Directory Structure**:
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Chat.tsx
│   │   ├── History.tsx
│   │   └── Analytics.tsx
│   ├── components/
│   │   ├── auth/
│   │   ├── chat/
│   │   ├── conversation/
│   │   └── shared/
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── auth.ts
│   │   └── utils.ts
│   ├── App.tsx
│   └── main.tsx
├── public/
├── index.html
└── vite.config.ts
├── components/
│   ├── chat/
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   └── Citation.tsx
│   ├── conversation/
│   │   ├── ConversationList.tsx
│   │   └── ConversationCard.tsx
│   └── shared/
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Layout.tsx
├── lib/
│   ├── api-client.ts
│   ├── auth.ts
│   └── utils.ts
└── styles/
    └── globals.css
```

**State Management**:
- React Context for global state (user, auth)
- React Query (@tanstack/react-query) for server state (API data fetching, caching)
- Local state (useState) for UI interactions

**Key Libraries**:
- `react-router-dom` - Client-side routing
- `@tanstack/react-query` - Data fetching and caching
- `axios` - HTTP client
- `tailwindcss` - Styling
- `zod` - Runtime type validation
- `react-markdown` - Render AI responses

**Build & Deploy**:
```bash
# Development
npm run dev  # Vite dev server with HMR

# Production build
npm run build  # Creates dist/ folder with static files

# Deploy to S3
aws s3 sync dist/ s3://plc-coach-frontend/
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

---

### 2.2 Backend Services

**Technology**: Python 3.11+ with FastAPI (unified backend)

**Decision Rationale:** Single language backend simplifies codebase. Python dominates AI/ML ecosystem (OpenAI, LangChain). FastAPI provides excellent async support, auto-generated docs, and has mature OAuth libraries.

**Services Architecture**:
```
api-service/  (Single FastAPI application)
├── routers/
│   ├── auth.py       # Authentication endpoints
│   ├── conversations.py
│   ├── messages.py
│   ├── coach.py      # AI query endpoints
│   ├── analytics.py
│   └── admin.py
├── services/
│   ├── auth_service.py
│   ├── conversation_service.py
│   ├── ai_service.py
│   └── analytics_service.py
├── models/
│   ├── user.py
│   ├── session.py
│   ├── conversation.py
│   └── message.py
├── database.py
├── main.py
└── config.py
```

### 2.2.1 Authentication Module

**Responsibilities**:
- OAuth 2.0 / OIDC flow management (Google, Clever)
- JIT (Just-In-Time) user provisioning
- Server-side session management in PostgreSQL
- Session validation and refresh
- Role assignment

**Endpoints**:
```
POST   /auth/google          - Initiate Google OIDC
POST   /auth/clever          - Initiate Clever SSO
GET    /auth/callback        - OAuth callback handler
POST   /auth/refresh         - Refresh access token
POST   /auth/logout          - Invalidate session
GET    /auth/me              - Get current user info
```

**Authentication Flow**:
```
User -> Frontend -> Auth Service -> Google/Clever
                                        │
                                        ▼
                                   OAuth Callback
                                        │
                                        ▼
                          Auth Service checks user in DB
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
                    User exists                   New user
                    Update last_login             Create user (JIT)
                         │                             │
                         └──────────────┬──────────────┘
                                        ▼
                              Generate JWT token
                                        │
                                        ▼
                           Return token to frontend
                                        │
                                        ▼
                            Store in httpOnly cookie
```

**Session Management (Server-Side in PostgreSQL)**:

**Decision Rationale:** Server-side sessions chosen over JWT for production security. Enables instant logout/revocation, audit trails, and role changes take effect immediately. Session lookup adds ~5ms per request (negligible with indexed queries).

**Session Table**:
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP,
    created_at TIMESTAMP,
    last_accessed_at TIMESTAMP
);
CREATE INDEX idx_sessions_id ON sessions(id) WHERE expires_at > NOW();
```

**Session Flow**:
```python
# Create session after OAuth
session = create_session(user_id, expires_in=timedelta(hours=24))
response.set_cookie("session_id", session.id, httponly=True, secure=True)

# Validate session (middleware)
async def get_current_user(session_id: str = Cookie(None)):
    session = await db.get_session(session_id)  # ~5ms indexed query
    if not session or session.expired:
        raise Unauthorized()
    return session.user
```

**Session Properties**:
- Session ID stored in httpOnly, secure cookies
- Session expiry: 24 hours
- Auto-refresh on activity
- Instant logout (delete session from DB)

---

### 2.3 API Service

**Technology**: Python FastAPI

**Responsibilities**:
- User management
- Conversation CRUD operations
- Message persistence
- Feedback collection
- Analytics aggregation
- Exports

**Key Modules**:
```
api-service/
├── main.py
├── routers/
│   ├── users.py
│   ├── conversations.py
│   ├── messages.py
│   ├── analytics.py
│   └── admin.py
├── models/
│   ├── user.py
│   ├── conversation.py
│   ├── message.py
│   └── feedback.py
├── services/
│   ├── conversation_service.py
│   ├── analytics_service.py
│   └── export_service.py
├── database.py
└── dependencies.py
```

**FastAPI Features Used**:
- Automatic OpenAPI documentation
- Pydantic models for request/response validation
- Dependency injection for auth, database
- Background tasks for async operations (exports)
- WebSocket support for real-time updates (optional)

---

### 2.4 AI Service

**Technology**: Python with LangChain

**Responsibilities**:
- Intent classification and domain routing
- Vector search and retrieval
- Context assembly
- Response generation via OpenAI
- Citation extraction
- Cost tracking

**Key Modules**:
```
ai-service/
├── main.py
├── routers/
│   └── coach.py
├── services/
│   ├── intent_router.py
│   ├── retrieval_service.py
│   ├── generation_service.py
│   └── citation_service.py
├── prompts/
│   ├── intent_classification.py
│   ├── generation_template.py
│   └── clarification.py
├── models/
│   ├── query.py
│   └── response.py
└── config.py
```

**LangChain Components**:
- `ChatOpenAI` for GPT-4-turbo
- `OpenAIEmbeddings` for query embedding
- `VectorStore` abstraction for retrieval
- `PromptTemplate` for structured prompts
- Custom chains for intent → retrieve → generate

---

### 2.5 Content Ingestion Pipeline

**Technology**: Python scripts (run offline)

**Responsibilities**:
- PDF extraction
- Text cleaning and preprocessing
- Intelligent chunking
- Metadata tagging
- Embedding generation
- Vector database upload

**Pipeline Stages**:
```
PDF Files (S3)
     │
     ▼
[1. Extract]  - PyMuPDF, extract text + structure
     │
     ▼
[2. Clean]    - Remove headers/footers, fix OCR
     │
     ▼
[3. Structure] - Preserve headings, lists, tables
     │
     ▼
[4. Chunk]    - 500-1000 tokens, 100 overlap
     │
     ▼
[5. Metadata] - Tag with book, chapter, domain
     │
     ▼
[6. Embed]    - OpenAI text-embedding-3-large
     │
     ▼
[7. Upload]   - Pinecone/Weaviate indexes
     │
     ▼
Vector DB (7 domain indexes)
```

**Chunking Algorithm**:
```python
def chunk_content(content, metadata):
    """
    Intelligent chunking that respects semantic boundaries.
    """
    chunks = []
    current_chunk = ""
    current_tokens = 0

    for paragraph in content.paragraphs:
        para_tokens = count_tokens(paragraph)

        if current_tokens + para_tokens > MAX_CHUNK_SIZE:
            # Save current chunk with overlap
            chunks.append({
                "content": current_chunk,
                "metadata": metadata,
                "tokens": current_tokens
            })

            # Start new chunk with overlap from previous
            overlap = get_last_n_tokens(current_chunk, OVERLAP_SIZE)
            current_chunk = overlap + paragraph
            current_tokens = OVERLAP_SIZE + para_tokens
        else:
            current_chunk += paragraph
            current_tokens += para_tokens

    # Add final chunk
    if current_chunk:
        chunks.append({
            "content": current_chunk,
            "metadata": metadata,
            "tokens": current_tokens
        })

    return chunks
```

---

## 3. Data Architecture

### 3.1 Database Schema (PostgreSQL)

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'educator',
    -- 'educator', 'coach', 'admin'

    organization_id UUID,
    organization_name VARCHAR(255),

    sso_provider VARCHAR(50) NOT NULL,
    -- 'google', 'clever'
    sso_id VARCHAR(255) NOT NULL,
    sso_metadata JSONB,

    profile_picture_url TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,

    UNIQUE(sso_provider, sso_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_role ON users(role);
```

#### Conversations Table
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(500),
    -- Auto-generated from first message or user-provided

    status VARCHAR(50) DEFAULT 'active',
    -- 'active', 'archived'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- For sharing
    share_token VARCHAR(255) UNIQUE,
    share_enabled BOOLEAN DEFAULT FALSE,
    share_expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);
CREATE INDEX idx_conversations_share ON conversations(share_token)
    WHERE share_enabled = TRUE;
```

#### Messages Table
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    role VARCHAR(50) NOT NULL,
    -- 'user', 'assistant'

    content TEXT NOT NULL,

    -- For assistant messages
    citations JSONB,
    -- Array of {book_title, authors, chapter, pages, quote}

    domains VARCHAR(100)[],
    -- Which domains were queried

    retrieval_metadata JSONB,
    -- Store chunk IDs, scores for debugging

    -- Feedback
    feedback_score INTEGER,
    -- +1 (thumbs up), -1 (thumbs down)

    feedback_reasons TEXT[],
    -- ['inaccurate', 'incomplete', 'not_relevant', 'missing_citations', 'other']

    feedback_comment TEXT,

    feedback_at TIMESTAMP WITH TIME ZONE,

    -- Cost tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_feedback ON messages(feedback_score)
    WHERE feedback_score IS NOT NULL;
```

#### Organizations Table (Optional)
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),
    -- 'school', 'district', 'other'

    subscription_tier VARCHAR(50) DEFAULT 'free',
    -- 'free', 'basic', 'premium', 'enterprise'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Limits
    monthly_message_limit INTEGER,
    monthly_message_count INTEGER DEFAULT 0,
    last_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Analytics Events Table (Optional - for detailed tracking)
```sql
CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),

    event_type VARCHAR(100) NOT NULL,
    -- 'message_sent', 'conversation_created', 'feedback_submitted', etc.

    event_data JSONB,

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_analytics_events_user ON analytics_events(user_id, timestamp);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type, timestamp);
```

### 3.2 Vector Database Schema

**Platform Choice**: Pinecone (managed) OR Weaviate (self-hosted)

#### Pinecone Index Structure

**7 Separate Indexes** (one per domain):
- `plc-assessment`
- `plc-collaboration`
- `plc-leadership`
- `plc-curriculum`
- `plc-data-analysis`
- `plc-school-culture`
- `plc-student-learning`

**Index Configuration**:
```python
# Pinecone setup
index_config = {
    "dimension": 3072,  # text-embedding-3-large
    "metric": "cosine",
    "pod_type": "p1.x1",  # Start small, scale up
}
```

**Metadata Schema** (per vector):
```json
{
  "book_id": "uuid",
  "book_title": "Learning by Doing",
  "authors": ["DuFour", "DuFour", "Eaker", "Many"],
  "publication_year": 2016,

  "chapter_number": 3,
  "chapter_title": "The Four Critical Questions",
  "page_start": 45,
  "page_end": 47,

  "chunk_index": 12,
  "total_chunks": 45,

  "primary_domain": "collaborative_teams",
  "secondary_domains": ["curriculum", "assessment"],

  "content": "The actual text content of the chunk...",
  "content_length": 850,
  "token_count": 680
}
```

**Query Example**:
```python
# Query with metadata filtering
results = index.query(
    vector=query_embedding,
    top_k=10,
    include_metadata=True,
    filter={
        "primary_domain": {"$eq": "assessment"},
        "publication_year": {"$gte": 2015}
    }
)
```

### 3.3 Data Retention Policy

| Data Type | Retention Period | Archival Strategy |
|-----------|------------------|-------------------|
| Active conversations | Indefinite | PostgreSQL |
| Archived conversations | 2 years | Move to S3 after 1 year |
| Messages | Indefinite | Part of conversation |
| Analytics events | 1 year | Aggregate to monthly summaries |
| Vector embeddings | Indefinite | Vector DB |
| Original PDFs | Indefinite | S3 Standard |
| Logs | 90 days | CloudWatch → S3 |
| Backups | 30 days | S3 with lifecycle policy |

---

## 4. AI/ML Architecture

### 4.1 Intent Classification & Routing

**Purpose**: Determine which domain(s) to query based on user question

**Approach**: Use GPT-4-turbo with function calling

**Function Definition**:
```json
{
  "name": "route_query",
  "description": "Classify user query into one or more PLC knowledge domains",
  "parameters": {
    "type": "object",
    "properties": {
      "primary_domain": {
        "type": "string",
        "enum": [
          "assessment",
          "collaboration",
          "leadership",
          "curriculum",
          "data_analysis",
          "school_culture",
          "student_learning"
        ]
      },
      "secondary_domains": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["assessment", "collaboration", "leadership", "curriculum",
                   "data_analysis", "school_culture", "student_learning"]
        }
      },
      "needs_clarification": {
        "type": "boolean",
        "description": "True if query is too vague to route confidently"
      },
      "clarification_question": {
        "type": "string",
        "description": "Question to ask user if needs_clarification is true"
      }
    },
    "required": ["primary_domain"]
  }
}
```

**Intent Classification Prompt**:
```python
INTENT_PROMPT = """
You are an expert in Professional Learning Communities (PLCs) at Work.
Your task is to classify the user's question into one or more knowledge domains.

Domains:
1. assessment - Formative/summative assessments, grading, rubrics
2. collaboration - Team structures, norms, meetings, protocols
3. leadership - Principal/admin guidance, change management
4. curriculum - Guaranteed viable curriculum, essential standards
5. data_analysis - RTI, interventions, data-driven decisions
6. school_culture - PLC implementation, culture shifts
7. student_learning - Student-centered practices, engagement

User question: {question}

Classification rules:
- Choose the PRIMARY domain that best matches the question
- Add SECONDARY domains if question spans multiple areas
- Set needs_clarification=true if question is too vague
- Be specific and confident in your classification
"""
```

**Routing Logic**:
```python
async def route_query(user_query: str) -> RoutingDecision:
    """
    Classify query and determine which indexes to search.
    """
    response = await openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": INTENT_PROMPT},
            {"role": "user", "content": user_query}
        ],
        functions=[ROUTE_FUNCTION],
        function_call={"name": "route_query"},
        temperature=0.1  # Low temperature for consistent routing
    )

    routing = json.loads(response.choices[0].message.function_call.arguments)

    if routing.get("needs_clarification"):
        return ClarificationNeeded(
            question=routing["clarification_question"]
        )

    # Determine which indexes to search
    domains_to_search = [routing["primary_domain"]]
    if routing.get("secondary_domains"):
        domains_to_search.extend(routing["secondary_domains"])

    return RoutingDecision(
        domains=domains_to_search,
        primary=routing["primary_domain"]
    )
```

### 4.2 Retrieval Strategy

**Goal**: Find the most relevant content chunks for the user's question

**Process**:
```
User Query
    │
    ▼
[1. Generate Query Embedding]
    │ OpenAI text-embedding-3-large
    ▼
Query Vector (3072-dim)
    │
    ▼
[2. Search Domain Indexes]
    │ Parallel search across routed domains
    ▼
Top-K Results per Domain
    │ k=10 per domain
    ▼
[3. Rerank & Deduplicate]
    │ Remove near-duplicates
    │ Score by semantic similarity
    ▼
Top 5-7 Chunks
    │
    ▼
[4. Assemble Context]
    │ Format with metadata
    ▼
Context for Generation
```

**Retrieval Implementation**:
```python
async def retrieve_context(
    query: str,
    domains: List[str],
    top_k: int = 10
) -> List[Chunk]:
    """
    Retrieve relevant chunks from vector database.
    """
    # Generate query embedding
    query_embedding = await get_embedding(query)

    # Search each domain in parallel
    search_tasks = [
        search_domain_index(domain, query_embedding, top_k)
        for domain in domains
    ]

    results = await asyncio.gather(*search_tasks)

    # Flatten results
    all_chunks = []
    for domain_results in results:
        all_chunks.extend(domain_results)

    # Rerank by similarity score
    all_chunks.sort(key=lambda x: x.score, reverse=True)

    # Deduplicate (remove chunks from same page range)
    deduped = deduplicate_chunks(all_chunks)

    # Return top 5-7
    return deduped[:7]


def deduplicate_chunks(chunks: List[Chunk]) -> List[Chunk]:
    """
    Remove near-duplicate chunks (e.g., overlapping page ranges).
    """
    seen_ranges = set()
    deduped = []

    for chunk in chunks:
        page_range = (
            chunk.metadata["book_id"],
            chunk.metadata["page_start"],
            chunk.metadata["page_end"]
        )

        if page_range not in seen_ranges:
            deduped.append(chunk)
            seen_ranges.add(page_range)

    return deduped
```

### 4.3 Response Generation

**Goal**: Generate accurate, well-cited responses using retrieved context

**Generation Prompt Template**:
```python
GENERATION_PROMPT = """
You are an expert PLC coach specializing in Professional Learning Communities at Work.
Your role is to provide practical, evidence-based guidance to educators.

CRITICAL RULES:
1. Base ALL responses on the provided context from Solution Tree books
2. Include specific citations with book title, author, chapter, and page numbers
3. If context doesn't contain relevant information, say so honestly
4. Keep responses concise (300-500 words)
5. Use accessible language appropriate for K-12 educators
6. Structure responses clearly with bullet points or numbered lists when appropriate

CONTEXT FROM SOLUTION TREE BOOKS:
{retrieved_chunks}

CONVERSATION HISTORY:
{conversation_history}

USER QUESTION: {user_query}

Provide your response following this structure:
1. Direct answer to the question (2-3 paragraphs)
2. Key takeaways (bullet points)
3. Citations section

Citations should follow this format:
📚 Sources:
• [Book Title] by [Author(s)], Chapter [X]: [Chapter Title], pp. [XX-XX]
  "[Direct quote or key concept paraphrased]"
"""
```

**Generation Implementation**:
```python
async def generate_response(
    user_query: str,
    retrieved_chunks: List[Chunk],
    conversation_history: List[Message]
) -> Response:
    """
    Generate response using GPT-4-turbo with retrieved context.
    """
    # Format retrieved chunks for context
    context = format_chunks_for_prompt(retrieved_chunks)

    # Format conversation history (last 10 messages)
    history = format_conversation_history(conversation_history[-10:])

    # Generate response
    response = await openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": GENERATION_PROMPT.format(
                    retrieved_chunks=context,
                    conversation_history=history,
                    user_query=user_query
                )
            }
        ],
        temperature=0.3,  # Low but not zero for natural language
        max_tokens=1000,
        presence_penalty=0.1,
        frequency_penalty=0.1
    )

    response_text = response.choices[0].message.content

    # Extract citations from response
    citations = extract_citations(response_text, retrieved_chunks)

    # Track cost
    cost = calculate_cost(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens
    )

    return Response(
        content=response_text,
        citations=citations,
        domains=[chunk.metadata["primary_domain"] for chunk in retrieved_chunks],
        cost=cost,
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens
    )
```

### 4.4 Citation Extraction

**Goal**: Parse citations from AI response and link to source chunks

```python
def extract_citations(
    response_text: str,
    retrieved_chunks: List[Chunk]
) -> List[Citation]:
    """
    Extract structured citations from response text.
    """
    citations = []

    # Parse citation section (after "📚 Sources:" or similar)
    citation_section = extract_citation_section(response_text)

    # Match each citation line to source chunk
    for line in citation_section.split("•"):
        if not line.strip():
            continue

        # Parse citation format: [Book] by [Authors], Chapter X: [Title], pp. XX-XX
        parsed = parse_citation_line(line)

        if parsed:
            # Find matching chunk
            matching_chunk = find_matching_chunk(parsed, retrieved_chunks)

            citations.append(Citation(
                book_title=parsed["book_title"],
                authors=parsed["authors"],
                chapter=parsed["chapter"],
                chapter_title=parsed["chapter_title"],
                pages=parsed["pages"],
                quote=parsed.get("quote", ""),
                chunk_id=matching_chunk.id if matching_chunk else None
            ))

    return citations


def validate_citations(
    citations: List[Citation],
    retrieved_chunks: List[Chunk]
) -> bool:
    """
    Validate that all citations reference actual retrieved chunks.
    Prevents hallucinated citations.
    """
    for citation in citations:
        if not citation.chunk_id:
            # Citation doesn't match any retrieved chunk
            logger.warning(f"Unmatched citation: {citation.book_title}")
            return False

    return True
```

### 4.5 Cost Tracking

**OpenAI Pricing (as of 2025)**:
- GPT-4-turbo: $10/1M input tokens, $30/1M output tokens
- text-embedding-3-large: $0.13/1M tokens

```python
def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost of OpenAI API call.
    """
    input_cost = (input_tokens / 1_000_000) * 10.00
    output_cost = (output_tokens / 1_000_000) * 30.00
    return input_cost + output_cost


# Store cost per message for tracking
async def track_cost(message_id: str, cost: float):
    """
    Store cost data for analytics.
    """
    await db.execute(
        "UPDATE messages SET cost_usd = $1 WHERE id = $2",
        cost, message_id
    )
```

**Estimated Costs**:
- Average query: ~2000 input tokens (context + history) + ~500 output tokens
- Cost per query: ~$0.035
- 1000 queries/day = ~$35/day = ~$1,050/month
- With 500 active users: ~$2/user/month in API costs

---

## 5. API Specifications

### 5.1 RESTful API Conventions

**Base URL**: `https://api.plccoach.solutiontree.com/v1`

**Authentication**: JWT Bearer token in Authorization header
```
Authorization: Bearer <jwt_token>
```

**Response Format**: JSON
```json
{
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2025-11-12T10:30:00Z",
    "version": "1.0"
  }
}
```

**Error Format**:
```json
{
  "data": null,
  "error": {
    "code": "INVALID_INPUT",
    "message": "User-friendly error message",
    "details": { ... }
  },
  "meta": { ... }
}
```

**HTTP Status Codes**:
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid auth
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### 5.2 Authentication Endpoints

#### POST /auth/google
Initiate Google OIDC flow.

**Request**:
```json
{
  "redirect_uri": "https://app.plccoach.com/callback"
}
```

**Response**:
```json
{
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
  }
}
```

#### POST /auth/clever
Initiate Clever SSO flow.

**Request**:
```json
{
  "redirect_uri": "https://app.plccoach.com/callback"
}
```

**Response**:
```json
{
  "data": {
    "auth_url": "https://clever.com/oauth/authorize?..."
  }
}
```

#### GET /auth/callback
OAuth callback handler (not called by client directly).

**Query Parameters**:
- `code` - Authorization code from provider
- `state` - CSRF token

**Response** (redirect):
```
302 Redirect to https://app.plccoach.com/dashboard
Set-Cookie: access_token=...; httpOnly; secure; sameSite=strict
Set-Cookie: refresh_token=...; httpOnly; secure; sameSite=strict
```

#### POST /auth/refresh
Refresh access token.

**Request**: None (uses refresh_token from cookie)

**Response**:
```json
{
  "data": {
    "access_token": "new_jwt_token",
    "expires_in": 3600
  }
}
```

#### POST /auth/logout
Invalidate session.

**Response**:
```json
{
  "data": {
    "message": "Logged out successfully"
  }
}
```

#### GET /auth/me
Get current user info.

**Response**:
```json
{
  "data": {
    "id": "user-uuid",
    "email": "jane@school.edu",
    "name": "Jane Doe",
    "role": "educator",
    "organization": {
      "id": "org-uuid",
      "name": "Lincoln Elementary"
    },
    "created_at": "2025-01-15T10:00:00Z",
    "last_login": "2025-11-12T09:00:00Z"
  }
}
```

### 5.3 Conversation Endpoints

#### GET /conversations
List user's conversations.

**Query Parameters**:
- `limit` (default: 20, max: 100)
- `offset` (default: 0)
- `status` (filter: active, archived)
- `search` (search in title/content)

**Response**:
```json
{
  "data": {
    "conversations": [
      {
        "id": "conv-uuid",
        "title": "Common Formative Assessments",
        "status": "active",
        "message_count": 8,
        "last_message_at": "2025-11-12T09:45:00Z",
        "created_at": "2025-11-12T09:00:00Z",
        "preview": "What are the key characteristics of..."
      }
    ],
    "total": 42,
    "limit": 20,
    "offset": 0
  }
}
```

#### POST /conversations
Create new conversation.

**Request**:
```json
{
  "title": "Optional initial title"
}
```

**Response**:
```json
{
  "data": {
    "id": "conv-uuid",
    "title": null,
    "status": "active",
    "created_at": "2025-11-12T10:00:00Z"
  }
}
```

#### GET /conversations/:id
Get conversation details with messages.

**Response**:
```json
{
  "data": {
    "id": "conv-uuid",
    "title": "Common Formative Assessments",
    "status": "active",
    "created_at": "2025-11-12T09:00:00Z",
    "updated_at": "2025-11-12T09:45:00Z",
    "messages": [
      {
        "id": "msg-uuid",
        "role": "user",
        "content": "What are the key characteristics of CFAs?",
        "created_at": "2025-11-12T09:00:00Z"
      },
      {
        "id": "msg-uuid-2",
        "role": "assistant",
        "content": "Common formative assessments...",
        "citations": [
          {
            "book_title": "Collaborative Common Assessments",
            "authors": ["Erkens"],
            "chapter": 2,
            "chapter_title": "Designing Quality Assessments",
            "pages": [34, 36],
            "quote": "CFAs are team-developed..."
          }
        ],
        "domains": ["assessment"],
        "feedback_score": 1,
        "created_at": "2025-11-12T09:00:15Z"
      }
    ]
  }
}
```

#### PATCH /conversations/:id
Update conversation (rename, archive).

**Request**:
```json
{
  "title": "New title",
  "status": "archived"
}
```

**Response**:
```json
{
  "data": {
    "id": "conv-uuid",
    "title": "New title",
    "status": "archived",
    "updated_at": "2025-11-12T10:00:00Z"
  }
}
```

#### DELETE /conversations/:id
Delete conversation.

**Response**:
```json
{
  "data": {
    "message": "Conversation deleted successfully"
  }
}
```

#### POST /conversations/:id/share
Generate shareable link.

**Request**:
```json
{
  "expires_in_days": 7
}
```

**Response**:
```json
{
  "data": {
    "share_url": "https://app.plccoach.com/shared/abc123xyz",
    "expires_at": "2025-11-19T10:00:00Z"
  }
}
```

### 5.4 Message Endpoints

#### POST /conversations/:id/messages
Send message to AI coach.

**Request**:
```json
{
  "content": "What are the four critical questions?"
}
```

**Response** (streaming or complete):
```json
{
  "data": {
    "id": "msg-uuid",
    "role": "assistant",
    "content": "The four critical questions...",
    "citations": [...],
    "domains": ["collaboration", "curriculum"],
    "created_at": "2025-11-12T10:00:15Z"
  }
}
```

**Streaming Response** (SSE):
```
event: message_start
data: {"id": "msg-uuid"}

event: content_delta
data: {"delta": "The four"}

event: content_delta
data: {"delta": " critical"}

event: message_complete
data: {"citations": [...], "domains": [...]}
```

#### POST /messages/:id/feedback
Submit feedback on AI response.

**Request**:
```json
{
  "score": 1,
  "reasons": ["accurate", "helpful"],
  "comment": "Great citation!"
}
```

**Response**:
```json
{
  "data": {
    "message": "Feedback submitted successfully"
  }
}
```

### 5.5 Analytics Endpoints

#### GET /analytics/overview
Get dashboard overview metrics.

**Query Parameters**:
- `start_date` (ISO 8601 date)
- `end_date` (ISO 8601 date)
- `team_id` (coaches only - filter by team)

**Response**:
```json
{
  "data": {
    "total_conversations": 156,
    "total_messages": 1042,
    "active_users": 42,
    "avg_satisfaction": 4.6,
    "top_domains": [
      {"domain": "assessment", "count": 312},
      {"domain": "collaboration", "count": 245}
    ],
    "daily_usage": [
      {"date": "2025-11-01", "messages": 45},
      {"date": "2025-11-02", "messages": 52}
    ]
  }
}
```

#### GET /analytics/topics
Get topic distribution.

**Response**:
```json
{
  "data": {
    "topics": [
      {
        "domain": "assessment",
        "percentage": 35,
        "count": 365,
        "top_keywords": ["formative", "grading", "rubrics"]
      }
    ]
  }
}
```

#### GET /analytics/export
Export data as CSV.

**Query Parameters**:
- `type` (conversations, messages, feedback)
- `start_date`
- `end_date`

**Response**:
```json
{
  "data": {
    "download_url": "https://s3.amazonaws.com/exports/export-123.csv",
    "expires_at": "2025-11-12T11:00:00Z"
  }
}
```

### 5.6 Admin Endpoints

#### GET /admin/users
List all users (admin only).

**Query Parameters**:
- `limit`, `offset`
- `role` (filter)
- `organization_id` (filter)

**Response**:
```json
{
  "data": {
    "users": [...],
    "total": 500
  }
}
```

#### PATCH /admin/users/:id
Update user role (admin only).

**Request**:
```json
{
  "role": "coach"
}
```

**Response**:
```json
{
  "data": {
    "id": "user-uuid",
    "role": "coach",
    "updated_at": "2025-11-12T10:00:00Z"
  }
}
```

#### GET /admin/feedback
View all feedback (admin only).

**Response**:
```json
{
  "data": {
    "feedback": [
      {
        "message_id": "msg-uuid",
        "score": -1,
        "reasons": ["inaccurate"],
        "comment": "Citation was wrong",
        "user_id": "user-uuid",
        "created_at": "2025-11-12T09:30:00Z"
      }
    ]
  }
}
```

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security                                  │
├─────────────────────────────────────────────────────────────┤
│  - AWS VPC with private subnets                             │
│  - Security Groups (firewall rules)                         │
│  - AWS Shield (DDoS protection)                             │
│  - WAF (Web Application Firewall)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Transport Security                                │
├─────────────────────────────────────────────────────────────┤
│  - TLS 1.3 for all connections                              │
│  - SSL certificates via AWS Certificate Manager            │
│  - HTTPS only (HSTS headers)                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Application Security                              │
├─────────────────────────────────────────────────────────────┤
│  - JWT authentication                                       │
│  - Role-based access control (RBAC)                         │
│  - Input validation (Pydantic, Zod)                         │
│  - Rate limiting (100 req/hour per user)                    │
│  - CSRF protection                                          │
│  - XSS prevention (React escaping)                          │
│  - SQL injection prevention (parameterized queries)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Data Security                                     │
├─────────────────────────────────────────────────────────────┤
│  - Encryption at rest (AWS KMS)                             │
│  - Encryption in transit (TLS)                              │
│  - Database credentials in Secrets Manager                  │
│  - No PII in logs                                           │
│  - Regular backups                                          │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Authentication & Authorization

**JWT Token Structure**:
```json
{
  "header": {
    "alg": "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "name": "Jane Doe",
    "role": "educator",
    "org_id": "org-uuid",
    "iat": 1699999999,
    "exp": 1700003599
  },
  "signature": "..."
}
```

**Token Signing**:
- Algorithm: RS256 (asymmetric)
- Private key stored in AWS Secrets Manager
- Public key distributed to services for verification
- Rotation: Keys rotated every 90 days

**Authorization Middleware**:
```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(required_role: str):
    """
    Decorator to enforce role-based access control.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in get_allowed_roles(required_role):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def get_allowed_roles(required_role: str) -> List[str]:
    """
    Role hierarchy: admin > coach > educator
    """
    hierarchy = {
        "educator": ["educator", "coach", "admin"],
        "coach": ["coach", "admin"],
        "admin": ["admin"]
    }
    return hierarchy.get(required_role, [])


# Usage
@router.get("/analytics/teams")
@require_role("coach")
async def get_team_analytics(current_user: User):
    # Only coaches and admins can access
    ...
```

### 6.3 Rate Limiting

**Strategy**: Token bucket algorithm

**Limits**:
- **Per user**: 100 requests/hour (general API)
- **AI coach queries**: 50 queries/hour per user
- **Exports**: 10 per day per user
- **Admin endpoints**: 1000 requests/hour

**Implementation**:
```python
from fastapi import Request, HTTPException
from redis import Redis
import time

redis_client = Redis(host="redis.cache.amazonaws.com")

async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware using Redis.
    """
    user_id = request.state.user_id
    endpoint = request.url.path

    # Create rate limit key
    key = f"rate_limit:{user_id}:{endpoint}"

    # Get current count
    current = redis_client.get(key)

    if current is None:
        # First request in window
        redis_client.setex(key, 3600, 1)
    else:
        current = int(current)
        if current >= get_limit_for_endpoint(endpoint):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": "3600"}
            )
        redis_client.incr(key)

    response = await call_next(request)
    return response
```

### 6.4 Data Privacy & Compliance

**FERPA Compliance**:
- No student data collected or stored
- User conversations are private by default
- Admins cannot view individual conversations without explicit sharing

**Data Access Controls**:
```python
async def can_access_conversation(user: User, conversation_id: str) -> bool:
    """
    Check if user can access a conversation.
    """
    conversation = await db.get_conversation(conversation_id)

    # Owner can always access
    if conversation.user_id == user.id:
        return True

    # Check if shared
    if conversation.share_enabled:
        return True

    # Admins cannot access without sharing (privacy)
    return False
```

**Audit Logging**:
```python
async def log_data_access(
    user_id: str,
    resource_type: str,
    resource_id: str,
    action: str
):
    """
    Log all access to sensitive data.
    """
    await db.insert_audit_log({
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "timestamp": datetime.utcnow(),
        "ip_address": get_client_ip()
    })
```

### 6.5 Secrets Management

**AWS Secrets Manager** for:
- Database credentials
- OpenAI API keys
- JWT signing keys
- OAuth client secrets
- Vector DB credentials

**Access Pattern**:
```python
import boto3
from functools import lru_cache

secrets_client = boto3.client("secretsmanager", region_name="us-east-1")

@lru_cache(maxsize=10)
def get_secret(secret_name: str) -> dict:
    """
    Retrieve secret from AWS Secrets Manager.
    Cached for 5 minutes to reduce API calls.
    """
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# Usage
openai_key = get_secret("prod/openai/api-key")["key"]
```

---

## 7. Infrastructure & Deployment

### 7.1 AWS Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   AWS CLOUD (us-east-1)                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              VPC (10.0.0.0/16)                     │   │
│  │                                                    │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  Public Subnet (10.0.1.0/24)                │  │   │
│  │  │  - Application Load Balancer (ALB)          │  │   │
│  │  │  - NAT Gateway                              │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │                                                    │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  Private Subnet 1 (10.0.10.0/24)            │  │   │
│  │  │  - ECS Fargate (App Containers)             │  │   │
│  │  │    - Auth Service                           │  │   │
│  │  │    - API Service                            │  │   │
│  │  │    - AI Service                             │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │                                                    │   │
│  │  ┌─────────────────────────────────────────────┐  │   │
│  │  │  Private Subnet 2 (10.0.20.0/24)            │  │   │
│  │  │  - RDS PostgreSQL (Multi-AZ)                │  │   │
│  │  │  - ElastiCache Redis (Optional)             │  │   │
│  │  └─────────────────────────────────────────────┘  │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  S3 Buckets                                        │   │
│  │  - plc-coach-content (PDFs, processed chunks)      │   │
│  │  - plc-coach-exports (CSV exports)                 │   │
│  │  - plc-coach-backups (DB backups)                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CloudFront (CDN)                                  │   │
│  │  - Frontend assets                                 │   │
│  │  - Static content caching                          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CloudWatch                                        │   │
│  │  - Logs                                            │   │
│  │  - Metrics                                         │   │
│  │  - Alarms                                          │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘

External Services:
- OpenAI API (api.openai.com)
- Pinecone/Weaviate (vector database)
- Google OAuth (accounts.google.com)
- Clever SSO (clever.com)
```

### 7.2 Container Configuration

**ECS Task Definition** (simplified):
```yaml
version: '3.8'

services:
  auth-service:
    image: plc-coach/auth-service:latest
    cpu: 512
    memory: 1024
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - CLEVER_CLIENT_ID=${CLEVER_CLIENT_ID}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      retries: 3

  api-service:
    image: plc-coach/api-service:latest
    cpu: 1024
    memory: 2048
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3

  ai-service:
    image: plc-coach/ai-service:latest
    cpu: 2048
    memory: 4096
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### 7.3 Auto-Scaling Configuration

**Target Tracking Scaling**:
```yaml
scaling:
  target_cpu_utilization: 70
  target_memory_utilization: 80
  min_capacity: 2  # Always 2 for HA
  max_capacity: 10 # Scale to 10 during peak

  scale_up:
    cooldown: 60s

  scale_down:
    cooldown: 300s  # Wait 5 min before scaling down
```

**Predictive Scaling** (optional):
- Scale up before school hours (7am-4pm local time)
- Scale down during nights/weekends
- Historical usage patterns

### 7.4 CI/CD Pipeline

**GitHub Actions Workflow**:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          npm test
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker build -t plc-coach/api-service:${{ github.sha }} ./api-service
          docker build -t plc-coach/ai-service:${{ github.sha }} ./ai-service
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin
          docker push plc-coach/api-service:${{ github.sha }}
          docker push plc-coach/ai-service:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster plc-coach-prod --service api-service \
            --force-new-deployment
```

### 7.5 Database Migration Strategy

**Tool**: Alembic (Python) or Knex (Node.js)

**Migration Process**:
```bash
# Generate migration
alembic revision --autogenerate -m "Add feedback columns"

# Review migration file
# migrations/versions/001_add_feedback_columns.py

# Apply to staging
alembic upgrade head --config staging.ini

# Test on staging
pytest tests/integration/

# Apply to production (blue-green deployment)
alembic upgrade head --config production.ini
```

**Rollback Plan**:
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123
```

---

## 8. Data Flow Diagrams

### 8.1 User Query Flow

```
User asks question
      │
      ▼
[Frontend React Component]
      │
      ▼
POST /conversations/:id/messages
{"content": "What are the 4 critical questions?"}
      │
      ▼
[API Gateway]
  - Verify JWT
  - Check rate limit
      │
      ▼
[API Service]
  - Validate input
  - Load conversation history
      │
      ▼
[AI Service] Intent Routing
  - Embed query → OpenAI Embeddings API
  - Classify intent → GPT-4-turbo function calling
  - Result: domains = ["collaboration", "curriculum"]
      │
      ▼
[AI Service] Retrieval
  - Query Pinecone indexes in parallel
    - plc-collaboration (top 10)
    - plc-curriculum (top 10)
  - Rerank and deduplicate
  - Select top 7 chunks
      │
      ▼
[AI Service] Generation
  - Assemble context from chunks
  - Format conversation history
  - Call GPT-4-turbo with context
  - Response: "The four critical questions are..."
      │
      ▼
[AI Service] Citation Extraction
  - Parse citations from response
  - Match to source chunks
  - Validate all citations grounded
      │
      ▼
[API Service] Persistence
  - Save user message to DB
  - Save assistant message to DB
  - Save citations as JSONB
  - Track tokens and cost
      │
      ▼
[API Gateway]
  - Return response to frontend
      │
      ▼
[Frontend]
  - Display response
  - Render citations
  - Show feedback buttons
```

### 8.2 Authentication Flow

```
User clicks "Login with Google"
      │
      ▼
[Frontend] → POST /auth/google
      │
      ▼
[Auth Service]
  - Generate state token (CSRF)
  - Build OAuth URL
  - Return auth_url
      │
      ▼
[Frontend] → Redirect to Google
      │
      ▼
[Google OAuth]
  - User authenticates
  - Consent screen
  - Redirect to callback with code
      │
      ▼
[Auth Service] → GET /auth/callback?code=...
  - Verify state token
  - Exchange code for access token
  - Fetch user info from Google
      │
      ▼
[Auth Service] JIT Provisioning
  - Check if user exists (by email)
      │
      ├──▶ User exists:
      │    - Update last_login
      │
      └──▶ New user:
           - Create user record
           - Assign "educator" role
      │
      ▼
[Auth Service] Token Generation
  - Generate JWT (access token)
  - Generate refresh token
  - Set httpOnly cookies
      │
      ▼
[Frontend] Redirect to /dashboard
  - Access token in cookie
  - User authenticated
```

### 8.3 Content Ingestion Flow

```
[Solution Tree Content Team]
  - Upload PDFs to S3
      │
      ▼
[Ingestion Pipeline Trigger]
  - Lambda function or scheduled job
      │
      ▼
[Step 1: Extract]
  - Download PDF from S3
  - Extract text with PyMuPDF
  - Preserve structure (headings, lists)
      │
      ▼
[Step 2: Clean]
  - Remove headers, footers, page numbers
  - Fix OCR errors
  - Normalize whitespace
      │
      ▼
[Step 3: Chunk]
  - Split into 500-1000 token chunks
  - 100-token overlap
  - Respect semantic boundaries
      │
      ▼
[Step 4: Tag Metadata]
  - Book title, author, chapter, pages
  - Domain classification (manual or AI)
  - Store chunk ID, index
      │
      ▼
[Step 5: Generate Embeddings]
  - Call OpenAI Embeddings API
  - Batch process (100 chunks at a time)
  - Generate 3072-dim vectors
      │
      ▼
[Step 6: Upload to Vector DB]
  - Determine domain(s) for each chunk
  - Upload to Pinecone indexes
  - Store metadata with vector
      │
      ▼
[Step 7: QA]
  - Run test queries
  - Validate retrieval quality
  - Check citation accuracy
      │
      ▼
[Production]
  - Content live in system
  - Available for queries
```

---

## 9. Scalability & Performance

### 9.1 Performance Targets

| Metric | Target | Current (Est.) |
|--------|--------|----------------|
| API response time (p50) | <500ms | ~300ms |
| API response time (p95) | <2s | ~1s |
| AI response time (p50) | <3s | ~2.5s |
| AI response time (p95) | <8s | ~5s |
| Concurrent users | 100+ | N/A |
| Database query time | <100ms | ~50ms |
| Vector search time | <500ms | ~300ms |

### 9.2 Caching Strategy

**Multi-Layer Caching**:

1. **CDN Caching** (CloudFront)
   - Frontend assets: 1 year
   - API responses (read-only): 5 minutes

2. **Application Caching** (Redis)
   - User profiles: 1 hour
   - Conversation lists: 5 minutes
   - Popular queries: 1 hour (cache AI responses for identical questions)

3. **Database Query Caching**
   - Read replicas for analytics queries
   - Materialized views for aggregations

**Cache Invalidation**:
```python
async def invalidate_user_cache(user_id: str):
    """
    Invalidate all cache entries for a user.
    """
    cache_keys = [
        f"user:{user_id}",
        f"conversations:{user_id}:*",
        f"analytics:{user_id}:*"
    ]

    for pattern in cache_keys:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
```

### 9.3 Database Optimization

**Indexing Strategy**:
```sql
-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(organization_id);
CREATE INDEX idx_users_sso ON users(sso_provider, sso_id);

-- Conversations
CREATE INDEX idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
CREATE INDEX idx_conversations_status ON conversations(user_id, status) WHERE status = 'active';

-- Messages
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_feedback ON messages(created_at) WHERE feedback_score IS NOT NULL;

-- Analytics
CREATE INDEX idx_analytics_events_user_time ON analytics_events(user_id, timestamp DESC);
CREATE INDEX idx_analytics_events_type_time ON analytics_events(event_type, timestamp DESC);
```

**Connection Pooling**:
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,        # 20 connections per service instance
    max_overflow=10,     # Up to 30 during peak
    pool_pre_ping=True,  # Check connection health
    pool_recycle=3600    # Recycle connections every hour
)
```

**Read Replicas**:
- Primary: Write operations (conversations, messages)
- Replica: Read operations (analytics, exports)
- Lag tolerance: <5 seconds

### 9.4 OpenAI API Optimization

**Cost Reduction Strategies**:

1. **Aggressive Prompt Compression**
   - Summarize conversation history beyond 5 turns
   - Remove redundant context

2. **Response Caching**
   - Cache identical queries for 1 hour
   - 30% cache hit rate = 30% cost savings

3. **Batch Embeddings**
   - Process embeddings in batches of 100
   - Reduce API overhead

4. **Model Selection**
   - Use GPT-3.5-turbo for simple factual queries
   - Use GPT-4-turbo only for complex reasoning

**Cost Monitoring**:
```python
class OpenAICostTracker:
    def __init__(self):
        self.costs = defaultdict(float)

    def track_call(self, user_id: str, input_tokens: int, output_tokens: int):
        cost = calculate_cost(input_tokens, output_tokens)
        self.costs[user_id] += cost

        # Alert if user exceeds daily budget
        if self.costs[user_id] > 5.00:  # $5/day per user
            logger.warning(f"User {user_id} exceeded daily cost budget")
```

---

## 10. Monitoring & Observability

### 10.1 Logging Strategy

**Structured Logging** (JSON format):
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "ai_response_generated",
    user_id=user_id,
    conversation_id=conversation_id,
    domains=domains,
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    cost_usd=cost,
    response_time_ms=response_time,
    citations_count=len(citations)
)
```

**Log Levels**:
- **DEBUG**: Detailed debugging info (disabled in prod)
- **INFO**: Normal operations (user actions, API calls)
- **WARNING**: Unexpected but handled issues (retry, fallback)
- **ERROR**: Errors requiring attention (API failures, exceptions)
- **CRITICAL**: System failures (database down, auth broken)

**CloudWatch Log Groups**:
- `/ecs/plc-coach/auth-service`
- `/ecs/plc-coach/api-service`
- `/ecs/plc-coach/ai-service`
- `/lambda/content-ingestion`

### 10.2 Metrics & Dashboards

**Key Metrics** (CloudWatch Custom Metrics):

**Performance**:
- `api.response_time` (p50, p95, p99)
- `ai.generation_time` (p50, p95, p99)
- `database.query_time`
- `vector_search.query_time`

**Usage**:
- `api.requests_per_minute`
- `ai.queries_per_minute`
- `users.active_count`
- `conversations.created_per_hour`

**Quality**:
- `ai.feedback_positive_rate`
- `ai.feedback_negative_rate`
- `ai.citations_per_response`
- `ai.retrieval_chunks_count`

**Cost**:
- `openai.cost_per_hour`
- `openai.tokens_per_query`
- `database.cost_per_day`

**Dashboard Layout** (CloudWatch):
```
┌─────────────────────────────────────────────────────────┐
│  System Health Dashboard                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Response Time]    [Error Rate]     [Active Users]    │
│     2.3s (p95)        0.2%              142            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Requests per Minute (last 24h)                  │  │
│  │  [Line chart showing API traffic]                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  AI Response Quality (last 7 days)               │  │
│  │  Positive: 87%  |  Negative: 13%                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  OpenAI Cost (last 30 days)                      │  │
│  │  Total: $1,245  |  Per User: $2.14               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 10.3 Alerting

**CloudWatch Alarms**:

**Critical Alerts** (PagerDuty):
- Error rate >5% for 5 minutes
- API p95 response time >10s for 5 minutes
- Database connection failures
- OpenAI API 500 errors >10% for 5 minutes

**Warning Alerts** (Slack):
- Error rate >2% for 10 minutes
- AI feedback negative rate >30% for 1 hour
- OpenAI cost >$100/hour
- Disk usage >80%

**Info Alerts** (Slack):
- New user signups spike (>50/hour)
- Unusual usage pattern detected
- Content ingestion completed

**Alert Configuration**:
```yaml
alarms:
  - name: HighErrorRate
    metric: api.errors
    statistic: Sum
    period: 300  # 5 minutes
    threshold: 50  # >50 errors
    comparison: GreaterThanThreshold
    actions:
      - sns:critical-alerts

  - name: SlowAPIResponse
    metric: api.response_time
    statistic: p95
    period: 300
    threshold: 10000  # 10 seconds
    comparison: GreaterThanThreshold
    actions:
      - sns:critical-alerts
```

### 10.4 Distributed Tracing

**AWS X-Ray Integration**:
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = FastAPI()
XRayMiddleware(app, xray_recorder)

@xray_recorder.capture("generate_ai_response")
async def generate_response(query: str):
    # Trace spans automatically created
    xray_recorder.begin_subsegment("intent_routing")
    domains = await route_query(query)
    xray_recorder.end_subsegment()

    xray_recorder.begin_subsegment("retrieval")
    chunks = await retrieve_context(query, domains)
    xray_recorder.end_subsegment()

    xray_recorder.begin_subsegment("generation")
    response = await generate(query, chunks)
    xray_recorder.end_subsegment()

    return response
```

**Trace Visualization**:
```
Request: POST /conversations/123/messages
  │
  ├─ Auth Verification (50ms)
  ├─ Load Conversation (120ms)
  │  └─ Database Query (115ms)
  ├─ Generate AI Response (2.8s)
  │  ├─ Intent Routing (450ms)
  │  │  └─ OpenAI API Call (420ms)
  │  ├─ Retrieval (380ms)
  │  │  └─ Pinecone Query (350ms)
  │  └─ Generation (1.9s)
  │     └─ OpenAI API Call (1.85s)
  └─ Save Message (90ms)
     └─ Database Insert (85ms)

Total: 3.06s
```

---

## 11. Disaster Recovery

### 11.1 Backup Strategy

**Database Backups**:
- **Automated snapshots**: Every 24 hours
- **Retention**: 30 days
- **Manual snapshots**: Before major deployments
- **Transaction logs**: Continuous (PITR enabled)
- **Storage**: S3 with versioning

**Vector Database Backups**:
- **Pinecone**: Built-in backups (managed service)
- **Weaviate**: Export to S3 weekly
- **Reconstruction**: Can rebuild from S3 content in 24 hours

**S3 Content Backups**:
- **Versioning**: Enabled
- **Cross-region replication**: us-east-1 → us-west-2
- **Lifecycle policy**: Glacier after 90 days

### 11.2 Recovery Procedures

**RTO (Recovery Time Objective)**: 4 hours
**RPO (Recovery Point Objective)**: 1 hour

**Recovery Scenarios**:

1. **Database Failure**:
   ```
   - Multi-AZ deployment provides automatic failover (~1 minute)
   - If complete failure, restore from snapshot
   - Restoration time: ~30 minutes for 100GB database
   ```

2. **Application Failure**:
   ```
   - Auto-scaling launches new containers
   - Health checks route traffic to healthy instances
   - Recovery time: ~2 minutes
   ```

3. **Region Failure** (DR):
   ```
   - Failover to us-west-2 region
   - Update Route 53 DNS to point to DR region
   - Restore database from cross-region snapshot
   - Recovery time: ~2-4 hours
   ```

### 11.3 Disaster Recovery Runbook

**Step 1: Assess**
- Determine scope of failure
- Check CloudWatch dashboards
- Review error logs

**Step 2: Notify**
- Alert engineering team (PagerDuty)
- Update status page
- Notify key stakeholders

**Step 3: Mitigate**
- Route traffic to healthy resources
- Scale up capacity if needed
- Enable read-only mode if necessary

**Step 4: Recover**
- Restore from backups
- Verify data integrity
- Run smoke tests

**Step 5: Communicate**
- Update status page (resolved)
- Post-mortem within 48 hours
- Document lessons learned

---

## 12. Technology Stack Summary

### Frontend
- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Styling**: Tailwind CSS
- **State Management**: React Context + React Query
- **HTTP Client**: Axios
- **Validation**: Zod
- **Markdown**: react-markdown

### Backend
- **Auth Service**: Node.js + Express
- **API Service**: Python + FastAPI
- **AI Service**: Python + LangChain
- **Runtime**: Docker containers on ECS Fargate

### Databases
- **Primary DB**: PostgreSQL 15 (AWS RDS)
- **Vector DB**: Pinecone OR Weaviate
- **Cache**: Redis (AWS ElastiCache) - optional

### AI/ML
- **LLM**: OpenAI GPT-4-turbo
- **Embeddings**: OpenAI text-embedding-3-large
- **RAG Framework**: LangChain

### Infrastructure
- **Cloud Provider**: AWS
- **Compute**: ECS Fargate
- **Load Balancer**: Application Load Balancer
- **CDN**: CloudFront
- **Storage**: S3
- **Monitoring**: CloudWatch
- **Secrets**: AWS Secrets Manager
- **DNS**: Route 53

### DevOps
- **CI/CD**: GitHub Actions
- **IaC**: Terraform OR CloudFormation
- **Container Registry**: Amazon ECR
- **Version Control**: Git + GitHub

### Security
- **Authentication**: OAuth 2.0 / OIDC
- **Authorization**: JWT + RBAC
- **Secrets**: AWS Secrets Manager
- **Encryption**: TLS 1.3, AWS KMS
- **WAF**: AWS WAF + Shield

---

## Appendix

### A. Database Migration Scripts

See `migrations/` directory for all Alembic migration files.

### B. API Postman Collection

Available at: `docs/api/PLC_Coach_API.postman_collection.json`

### C. Deployment Checklist

See `docs/deployment/DEPLOYMENT_CHECKLIST.md`

### D. Monitoring Runbooks

See `docs/monitoring/RUNBOOKS.md`

---

**End of Technical Architecture Document**

*For questions or clarifications, contact the Engineering Team.*
