# Epic 2: Core AI Coach

**Author:** Reena
**Date:** 2025-11-12
**Duration:** 4-5 weeks
**Project:** AI Powered PLC at Work Virtual Coach

---

## Epic Goal

Build the core AI coaching engine that answers educator questions with accurate, cited responses grounded in Solution Tree's PLC books, using RAG (Retrieval-Augmented Generation) architecture with intent routing, semantic search, and transparent citations.

**Business Value:** Educators get instant, expert guidance during PLC meetings with transparent citations from trusted Solution Tree content. This is the "magic" that differentiates the product.

---

## Stories

### Story 2.1: Content Ingestion Pipeline - PDF Processing

**As a** content engineer,
**I want** to extract and process text from Solution Tree PDF books,
**So that** the content can be prepared for embedding and semantic search.

**Acceptance Criteria:**

**Given** we have 15-20 Solution Tree PDF books stored in S3
**When** the content ingestion script runs
**Then** for each PDF:
- Text is extracted using PyMuPDF (or pdfplumber)
- Document structure is preserved (headings, lists, tables)
- Page numbers, headers, and footers are removed
- OCR errors are cleaned up
- Whitespace is normalized

**And** extracted content is saved with metadata:
```json
{
  "book_id": "uuid",
  "book_title": "Learning by Doing",
  "authors": ["DuFour", "DuFour", "Eaker", "Many"],
  "publication_year": 2016,
  "total_pages": 350,
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "...",
      "page_start": 15,
      "page_end": 45,
      "content": "..."
    }
  ]
}
```

**And** the processed content is stored in S3 for the next stage

**And** a processing log records success/failure for each book

**Prerequisites:** Epic 1 Story 1.1 (S3 buckets must exist)

**Technical Notes:**
- Use PyMuPDF (fitz) or pdfplumber for extraction
- Preserve markdown-style structure (# for headings, lists, etc.)
- Handle special characters and encoding properly
- Initial corpus: Learning by Doing, Collaborative Common Assessments, Simplifying Response to Intervention, etc. (see PRD Section 10.1)
- Script location: `/scripts/content-ingestion/01_extract_pdfs.py`
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.5 (Content Ingestion Pipeline)
- Reference: PRD Section 10.2 (Content Preprocessing Pipeline)

---

### Story 2.2: Content Chunking with Metadata Tagging

**As a** content engineer,
**I want** to split processed book content into semantic chunks with rich metadata,
**So that** each chunk can be embedded and retrieved independently.

**Acceptance Criteria:**

**Given** processed book content from Story 2.1
**When** the chunking script runs
**Then** content is split into chunks with:
- Target size: 500-1000 tokens per chunk
- 100-token overlap between consecutive chunks
- Semantic boundaries respected (no mid-paragraph splits)
- Related elements kept together (list items + explanations)

**And** each chunk is tagged with metadata:
```json
{
  "chunk_id": "uuid",
  "book_id": "uuid",
  "book_title": "Learning by Doing",
  "authors": ["DuFour", "DuFour", "Eaker", "Many"],
  "chapter_number": 3,
  "chapter_title": "The Four Critical Questions",
  "page_start": 45,
  "page_end": 47,
  "chunk_index": 12,
  "total_chunks_in_chapter": 45,
  "content": "The actual text content...",
  "token_count": 680,
  "primary_domain": "collaborative_teams",
  "secondary_domains": ["curriculum", "assessment"]
}
```

**And** domain classification is done either:
- Manually for initial corpus (faster for 15-20 books)
- Or using GPT-4o for automatic classification

**And** chunked content with metadata is saved to S3

**And** quality assurance checks verify:
- No chunks exceed 1000 tokens
- All chunks have required metadata fields
- Page numbers are accurate

**Prerequisites:** Story 2.1 (extracted content must exist)

**Technical Notes:**
- Use tiktoken library to count tokens (OpenAI tokenizer)
- Implement intelligent chunking algorithm (see TECHNICAL_ARCHITECTURE.md Section 2.5)
- For 15-20 books, manual domain tagging may be faster than automated
- Consider using section headers as context for each chunk
- Script location: `/scripts/content-ingestion/02_chunk_content.py`
- Reference: PRD Section 10.2 Step 4 (Intelligent Chunking)

---

### Story 2.3: Vector Embeddings Generation

**As a** content engineer,
**I want** to generate vector embeddings for all content chunks,
**So that** semantic similarity search can be performed.

**Acceptance Criteria:**

**Given** chunked content with metadata from Story 2.2
**When** the embedding generation script runs
**Then** for each chunk:
- Text content is sent to OpenAI text-embedding-3-large API
- A 3072-dimensional vector embedding is generated
- The embedding is associated with the chunk metadata

**And** embeddings are generated in batches of 100 for efficiency

**And** the script handles rate limiting and retries on transient failures

**And** progress is logged (chunks processed / total chunks)

**And** embeddings are stored temporarily before database upload

**And** cost tracking logs the total tokens processed and API cost

**Given** 15-20 books with ~50,000-100,000 chunks total
**Then** embedding generation completes in <24 hours

**And** total cost is estimated and logged (approximately $6.50 for 50M tokens at $0.13/1M)

**Prerequisites:** Story 2.2 (chunked content must exist)

**Technical Notes:**
- OpenAI text-embedding-3-large: 3072 dimensions, $0.13/1M tokens
- Use OpenAI Python SDK with batch processing
- Implement exponential backoff for rate limit errors
- Store embeddings in numpy array format temporarily
- Monitor OpenAI API costs in real-time
- Script location: `/scripts/content-ingestion/03_generate_embeddings.py`
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.5 (Cost Tracking)

---

### Story 2.4: PostgreSQL pgvector Setup & Data Upload

**As a** backend developer,
**I want** to store vector embeddings in PostgreSQL using pgvector extension,
**So that** semantic search can be performed directly in the database.

**Acceptance Criteria:**

**Given** PostgreSQL database from Epic 1
**When** pgvector setup script runs
**Then** the pgvector extension is installed: `CREATE EXTENSION IF NOT EXISTS vector;`

**And** the embeddings table is created:
```sql
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(3072),
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**And** an ivfflat index is created for fast similarity search:
```sql
CREATE INDEX ON embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**And** all chunk embeddings from Story 2.3 are inserted into the table

**And** metadata includes: book_title, chapter, pages, domain, authors, etc.

**And** a semantic search test query returns relevant results:
```sql
SELECT content, metadata,
       1 - (embedding <=> '[query_vector]') as similarity
FROM embeddings
ORDER BY embedding <=> '[query_vector]'
LIMIT 10;
```

**And** query performance is <500ms for top-10 similarity search

**Prerequisites:** Story 2.3 (embeddings must be generated)

**Technical Notes:**
- Install pgvector extension in PostgreSQL 15
- Use cosine similarity (<=>) for vector comparison
- ivfflat index: good for <1M vectors, faster than brute force
- Bulk insert embeddings in batches of 1000
- Test with sample queries from different domains
- Script location: `/scripts/content-ingestion/04_upload_to_db.py`
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #4 (pgvector choice)
- Reference: TECHNICAL_ARCHITECTURE.md Section 3.2 (Vector Database Schema)

---

### Story 2.5: Intent Classification & Domain Routing

**As a** backend developer,
**I want** to classify user queries into knowledge domains,
**So that** retrieval can be targeted to the most relevant content areas.

**Acceptance Criteria:**

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

**Prerequisites:** Story 1.3 (backend API foundation)

**Technical Notes:**
- Implement in `/api-service/services/intent_router.py`
- Use OpenAI GPT-4o with function calling
- Cache classifications for identical queries (1 hour TTL)
- Log all classifications for quality monitoring
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.1 (Intent Classification & Routing)

---

### Story 2.6: Semantic Retrieval Service

**As a** backend developer,
**I want** to retrieve relevant content chunks based on user queries,
**So that** the AI can generate responses grounded in book content.

**Acceptance Criteria:**

**Given** a user query and classified domain(s) from Story 2.5
**When** the retrieval service executes
**Then** the following process occurs:
1. Query text is embedded using text-embedding-3-large
2. Vector similarity search is performed against pgvector
3. Metadata filtering is applied based on classified domain(s)
4. Top 7-10 most relevant chunks are retrieved
5. Chunks are deduplicated (remove overlapping page ranges)
6. Final top 7 chunks are returned

**And** each retrieved chunk includes:
- content (text)
- metadata (book, chapter, pages, domain)
- similarity_score (0-1, higher is better)

**And** retrieval completes in <500ms

**And** deduplication ensures no two chunks from the same page range

**Given** a query requires multiple domains
**Then** chunks are retrieved from all relevant domain areas

**And** results are reranked by similarity score across all domains

**Prerequisites:** Story 2.4 (pgvector must be set up), Story 2.5 (intent classification)

**Technical Notes:**
- Implement in `/api-service/services/retrieval_service.py`
- Use SQLAlchemy for database queries
- Filter by domain using JSONB metadata: `metadata->>'primary_domain' = ?`
- Implement deduplication logic (see TECHNICAL_ARCHITECTURE.md Section 4.2)
- Monitor retrieval quality with sample queries
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.2 (Retrieval Strategy)

---

### Story 2.7: Response Generation with Citations

**As a** backend developer,
**I want** to generate AI responses with transparent citations,
**So that** educators receive credible, verifiable guidance.

**Acceptance Criteria:**

**Given** a user query and retrieved chunks from Story 2.6
**When** the generation service creates a response
**Then** GPT-4o is called with:
- System prompt defining PLC coach role and rules
- Retrieved chunks formatted as context
- User query
- Temperature=0.3 (balance between creativity and consistency)
- Max tokens=1000 (~300-500 word responses)

**And** the response includes:
- Direct answer to the question (2-3 paragraphs)
- Key takeaways (bullet points)
- Citations section with format:
  ```
  📚 Sources:
  • [Book Title] by [Author(s)], Chapter [X]: [Chapter Title], pp. [XX-XX]
    "[Direct quote or key concept paraphrased]"
  ```

**And** citations are extracted and validated:
- Each citation matches a retrieved chunk
- No hallucinated citations (all must reference actual chunks)
- 95%+ of responses include at least one citation

**And** response generation completes in <3 seconds (p95 <5 seconds)

**And** token usage and cost are tracked for each response

**Given** retrieved context doesn't contain relevant information
**Then** the response honestly states: "I don't have specific information on this in the Solution Tree books I have access to."

**Prerequisites:** Story 2.6 (retrieval service must work)

**Technical Notes:**
- Implement in `/api-service/services/generation_service.py`
- Use generation prompt template from TECHNICAL_ARCHITECTURE.md Section 4.3
- Validate citations against retrieved chunks (prevent hallucination)
- Track costs: ~$0.02-0.035 per query
- Log responses for quality review
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.3 (Response Generation)
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.4 (Citation Extraction)

---

### Story 2.8: Chat API Endpoints

**As a** frontend developer,
**I want** REST API endpoints to send queries and receive responses,
**So that** users can interact with the AI coach through the UI.

**Acceptance Criteria:**

**Given** the backend services from Stories 2.5-2.7 are implemented
**When** API endpoints are created
**Then** the following endpoint exists:

**POST /api/coach/query**
- Request body:
  ```json
  {
    "query": "What are the four critical questions?",
    "conversation_id": "uuid" (optional for context)
  }
  ```
- Response:
  ```json
  {
    "response": {
      "content": "The four critical questions...",
      "citations": [
        {
          "book_title": "Learning by Doing",
          "authors": ["DuFour", "DuFour", "Eaker", "Many"],
          "chapter": 3,
          "chapter_title": "...",
          "pages": [45, 47],
          "quote": "..."
        }
      ],
      "domains": ["collaboration", "curriculum"],
      "response_time_ms": 2843
    }
  }
  ```

**And** error handling returns appropriate status codes:
- 400 Bad Request (invalid input)
- 401 Unauthorized (not logged in)
- 429 Too Many Requests (rate limit - not enforced in MVP but structure ready)
- 500 Internal Server Error (AI service failure)

**And** graceful degradation if OpenAI API fails:
- Retry 2 times with exponential backoff
- Return friendly error message if all retries fail

**And** all requests require valid session authentication

**Prerequisites:** Stories 2.5-2.7 (all AI services must be implemented)

**Technical Notes:**
- Implement in `/api-service/routers/coach.py`
- Add request validation using Pydantic models
- Implement retry logic with tenacity library
- Log all queries and responses for analytics
- Monitor response times with CloudWatch metrics
- Reference: TECHNICAL_ARCHITECTURE.md Section 5.4 (Message Endpoints)

---

### Story 2.9: Chat UI Component

**As an** educator,
**I want** a clean, intuitive chat interface,
**So that** I can easily ask questions and read responses during PLC meetings.

**Acceptance Criteria:**

**Given** I am logged in and on the chat page
**When** the page loads
**Then** I see:
- A text input field at the bottom (auto-expanding for longer questions)
- A "Send" button (also triggered by Enter key)
- An empty message area above
- Solution Tree branding in header

**Given** I type a question and click Send
**When** the request is processing
**Then** a loading indicator appears ("AI Coach is thinking...")

**And** the input field is disabled

**When** the response arrives
**Then** my question appears on the right (user message, colored background)

**And** the AI response appears on the left with:
- Assistant avatar icon
- Response text with proper formatting (paragraphs, lists)
- Citations section visually distinct (light gray box, book icon)
- Timestamp

**And** I can scroll through the conversation

**Given** the AI response includes citations
**Then** each citation displays:
- Book title (linked to Solution Tree product page if available)
- Authors, chapter, pages
- Quote or key concept

**And** citations are visually separated from the main response

**Prerequisites:** Story 2.8 (API endpoints must exist), Epic 1 Story 1.7 (frontend shell)

**Technical Notes:**
- Implement in `/frontend/src/components/chat/ChatInterface.tsx`
- Use react-markdown for rendering AI responses
- Add syntax highlighting for code blocks if needed
- Implement auto-scroll to latest message
- Handle long responses with proper line breaks
- Mobile-responsive design (full-width on mobile, max 800px on desktop)
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.1 (Frontend Application)
- Reference: PRD Section 8.1 (Core Interface Elements)

---

### Story 2.10: Example Questions & Onboarding

**As a** first-time user,
**I want** to see example questions,
**So that** I understand what the AI coach can help me with.

**Acceptance Criteria:**

**Given** I am a new user on the chat page
**When** the page loads with no messages
**Then** I see a welcome message:
- "Welcome to the PLC at Work Virtual Coach!"
- Brief explanation: "Ask me anything about Professional Learning Communities based on Solution Tree's expert guidance."

**And** I see 5-7 example questions displayed as clickable cards:
- "What are the four critical questions of a PLC?"
- "How do we create effective common formative assessments?"
- "What should we do when students don't learn?"
- "How can we build strong collaborative team norms?"
- "What is a guaranteed and viable curriculum?"
- "How do we implement response to intervention (RTI)?"
- "What makes an effective PLC leader?"

**Given** I click an example question
**Then** it populates the input field

**And** I can edit it before sending or send it as-is

**Given** I have sent at least one message
**Then** the welcome message and example questions disappear

**And** the conversation history is displayed

**Prerequisites:** Story 2.9 (chat UI must exist)

**Technical Notes:**
- Example questions should cover all 7 domains
- Store example questions in frontend config (can be updated easily)
- Dismissible welcome modal for first-time users
- Track which example questions are most clicked (analytics)
- Reference: PRD Section 8.2 (First-Time User Flow)

---

### Story 2.11: Error Handling & Edge Cases

**As a** user,
**I want** clear error messages when something goes wrong,
**So that** I know what happened and what to do next.

**Acceptance Criteria:**

**Given** the OpenAI API is unavailable
**When** I submit a query
**Then** after 2 retry attempts fail
**And** I see a friendly error message:
  "The AI coach is temporarily unavailable. Please try again in a moment."

**Given** my query is too vague
**When** intent classification determines needs_clarification=true
**Then** I receive a clarifying question instead of a full response

**And** I can refine my question and resubmit

**Given** there are no relevant chunks found for my query
**When** the retrieval service returns empty results
**Then** the response states:
  "I don't have specific information on this topic in the Solution Tree books currently available. Try rephrasing your question or asking about PLC practices, assessment, collaboration, or leadership."

**Given** my session expires while I'm typing
**When** I submit a query
**Then** I receive a 401 error

**And** I'm redirected to login with a message: "Your session expired. Please log in again."

**Given** the database connection fails
**When** any operation requires database access
**Then** the system logs the error

**And** returns a 500 error with generic message (no technical details exposed)

**And** CloudWatch alarm triggers for error rate >5%

**Prerequisites:** Story 2.10 (full chat experience must exist)

**Technical Notes:**
- Implement comprehensive error handling in all services
- Use try-except blocks with specific error types
- Log all errors to CloudWatch with context
- Never expose technical details to users
- Test failure scenarios: API down, DB unavailable, network timeout
- Reference: TECHNICAL_DECISIONS_SUMMARY.md Decision #13 (Error Handling)

---

### Story 2.12: Content Quality Assurance

**As a** product owner,
**I want** to validate that AI responses are accurate and well-cited,
**So that** educators receive trustworthy guidance.

**Acceptance Criteria:**

**Given** the core AI coach is implemented
**When** QA testing is performed
**Then** 20 test queries across all 7 domains are executed

**And** for each response:
- At least one citation is included (target: 95%+)
- Citations reference actual book content (no hallucinations)
- Response is relevant to the question
- Response length is 300-500 words
- Answer is accurate based on source material

**And** a QA report documents:
- Citation coverage rate (% responses with citations)
- Average citations per response
- Average response time
- Any hallucinations or inaccuracies found
- Domain coverage (all 7 domains tested)

**And** any issues found are documented as bugs

**And** at least 90% of test queries produce satisfactory responses

**Given** feedback indicates citation inaccuracies
**Then** the citation validation logic is improved

**Prerequisites:** All previous stories in Epic 2

**Technical Notes:**
- Create test query suite in `/tests/qa/ai-coach-test-queries.md`
- Manual review by someone familiar with PLC content
- Document test results in `/docs/qa-reports/epic-2-ai-coach-qa.md`
- Consider creating automated regression tests for top queries
- Reference: PRD Section 3 (Success Metrics)

---

## Epic Completion Criteria

- [ ] 15-20 Solution Tree books processed and embedded
- [ ] ~50,000-100,000 content chunks in pgvector database
- [ ] Intent classification correctly routes queries to domains
- [ ] Semantic retrieval returns relevant content chunks
- [ ] AI responses include transparent citations (95%+ coverage)
- [ ] Average response time <5 seconds
- [ ] Chat UI is functional and responsive
- [ ] Error handling gracefully manages failures
- [ ] QA validation shows >90% satisfactory responses

---

## Definition of Done

- All 12 stories completed and acceptance criteria met
- Content ingestion pipeline documented
- Unit tests for intent routing, retrieval, and generation
- Integration tests verify end-to-end query flow
- QA report confirms >90% response quality
- Performance benchmarks met (<5s average response time)
- All 7 knowledge domains operational
- No critical bugs or hallucination issues

---

## Dependencies & Risks

**External Dependencies:**
- OpenAI API (GPT-4o, text-embedding-3-large)
- Solution Tree PDF content access

**Risks:**
- OpenAI API costs higher than estimated (Mitigation: Monitor costs daily, implement caching)
- Citation extraction accuracy <95% (Mitigation: Improve validation logic, manual review)
- Retrieval quality insufficient (Mitigation: Tune chunk size, adjust top-k, reranking)
- Content ingestion takes longer than 24 hours (Mitigation: Parallel processing, batch optimization)

**Next Epic:** Epic 3 - Conversations & History (builds on working AI coach)
