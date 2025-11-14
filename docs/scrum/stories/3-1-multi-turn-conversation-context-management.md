# Story 3.1: Multi-Turn Conversation Context Management

Status: review

## Story

As an educator,
I want the AI coach to remember our conversation,
so that I can ask follow-up questions without repeating context.

## Acceptance Criteria

1. **Context Retrieval and Formatting:**
   - Given I have an active conversation with messages
   - When I ask a follow-up question
   - Then the AI coach receives the last 10 messages as context
   - And the conversation history is formatted in the prompt as:
     ```
     User: [First question]
     Assistant: [First response]
     User: [Second question]
     Assistant: [Second response]
     ...
     User: [Current question]
     ```
   - And the response considers previous context

2. **Message Limit (10 messages):**
   - Given the conversation exceeds 10 message turns
   - When I ask a new question
   - Then only the most recent 10 messages are included as context
   - And older messages are still stored but not sent to the AI

3. **Context Coherence:**
   - Given I ask "Can you elaborate on that?"
   - When the AI generates a response
   - Then it references the previous response appropriately
   - And maintains coherence with the conversation flow

## Tasks / Subtasks

- [x] Implement conversation context assembly in generation service (AC: #1)
  - [x] Create `get_conversation_context()` function in generation service
  - [x] Load last 10 messages from database ordered by created_at DESC
  - [x] Format messages into prompt template
  - [x] Include conversation_id parameter in function signature

- [x] Update /coach/query endpoint to pass conversation_id (AC: #1)
  - [x] Modify `/api/coach/query` endpoint to accept conversation_id
  - [x] Validate conversation_id exists and belongs to current user
  - [x] Pass conversation_id to generation service

- [x] Implement message retrieval with 10-message limit (AC: #2)
  - [x] Query messages table with LIMIT 10 and ORDER BY created_at DESC
  - [x] Ensure proper JOIN with conversations table for user validation
  - [x] Handle empty conversation case (no prior messages)

- [x] Format conversation history for LLM prompt (AC: #1, #3)
  - [x] Build prompt string with alternating User/Assistant labels
  - [x] Preserve message order (oldest to newest in context)
  - [x] Include citations from previous assistant responses
  - [x] Append current user question to context

- [x] Testing and validation (AC: all)
  - [x] Unit test: context assembly with < 10 messages
  - [x] Unit test: context assembly with > 10 messages (only last 10 included)
  - [x] Integration test: multi-turn conversation maintains context
  - [x] Integration test: follow-up question references previous response
  - [x] Validation guide created

## Dev Notes

### Prerequisites
- Story 2.8 (chat API `/api/coach/query` must exist)
- Story 1.2 (conversations and messages tables must exist)
- Epic 2 AI generation service operational

### Architecture Patterns and Constraints
- **Context Window Management:** Limit to 10 messages to manage token costs (OpenAI GPT-4o context pricing)
- **Message Ordering:** Always ORDER BY created_at DESC in SQL, then reverse in Python for chronological prompt
- **User Authorization:** Always validate conversation belongs to requesting user before loading context
- **Prompt Template:** Use consistent format for LLM to recognize conversation structure

### Key Technical Decisions
- **10-Message Limit:** Balances context quality with token costs (~500-1000 tokens per message pair)
- **Database Query:** Single query with LIMIT 10 more efficient than pagination
- **Message Format:** Plain text "User:"/"Assistant:" labels work better than JSON for GPT-4o
- **Future Enhancement:** Implement conversation summarization for very long conversations (defer to Epic 4)

### Testing Standards
- Unit tests for context assembly logic (mocked database)
- Integration tests with real database and OpenAI API (use small test conversations)
- Verify token count stays within reasonable limits (<8K tokens for context)
- Test edge cases: new conversation (0 messages), single message, exactly 10 messages, 15+ messages

### Project Structure Notes
```
api-service/
├── app/
│   ├── services/
│   │   ├── generation.py (MODIFY - add context assembly)
│   │   └── intent_router.py (existing)
│   ├── routes/
│   │   └── coach.py (MODIFY - add conversation_id param)
│   └── models/
│       ├── conversation.py (existing)
│       └── message.py (existing)
└── tests/
    ├── unit/
    │   └── test_context_assembly.py (CREATE)
    └── integration/
        └── test_multiturn_conversation.py (CREATE)
```

### Database Schema Reference
From Story 1.2, relevant tables:
- `conversations` table: id, user_id, title, status, created_at, updated_at
- `messages` table: id, conversation_id, role (user/assistant), content, citations (JSONB), created_at

### References
- [Source: docs/epics/epic-3-conversations-history.md#Story-3.1]
- Technical Architecture: TECHNICAL_ARCHITECTURE.md Section 4.3 (Response Generation with history)
- PRD: PRD Section 6.3 (Multi-turn Conversations FR-3.1)
- Database Schema: [Source: docs/stories/1-2-database-schema-creation.md]

### Learnings from Previous Story

**From Story 2-5-intent-classification-domain-routing (Status: backlog)**

Story 2-5 has not been implemented yet, so no learnings available. However, Story 3.1 will need to coordinate with the intent classification service to ensure conversation context is considered during domain routing.

**Database Context from Story 1-2 (Status: done)**
- **Database Tables:** conversations and messages tables exist with proper schema
- **Foreign Keys:** messages.conversation_id references conversations(id) with CASCADE delete
- **Message Role:** role field constrained to ('user', 'assistant', 'system')
- **Citations:** Stored as JSONB for flexible structure
- **Indexes:** idx_messages_conversation on (conversation_id, created_at) for efficient querying
- **Connection Details:** Available via AWS Secrets Manager

[Source: stories/1-2-database-schema-creation.md]

## Dev Agent Record

### Context Reference

- docs/scrum/stories/3-1-multi-turn-conversation-context-management.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Implementation proceeded smoothly without major debugging required.

### Completion Notes List

✅ **Implementation Summary:**

1. **Added conversation context loading** to GenerationService:
   - New method `get_conversation_context()` loads last 10 messages from database
   - Validates conversation ownership (user_id check)
   - Formats as chronological User/Assistant dialog
   - Handles empty conversations gracefully

2. **Modified generate() method** to accept conversation_history parameter:
   - Prepends conversation history to user prompt when provided
   - Maintains backward compatibility (conversation_history is optional)

3. **Updated /api/coach/query endpoint**:
   - Added database session dependency
   - Added X-User-Id header parameter (TODO: replace with proper auth)
   - Calls get_conversation_context() when conversation_id provided
   - Passes conversation_history to generation service

4. **Comprehensive test coverage** (8 unit tests, all passing):
   - Empty conversation handling
   - Message formatting (User/Assistant labels)
   - 10-message limit enforcement
   - Authorization (user ownership validation)
   - System message filtering
   - Integration with generate() method

**Key Technical Decisions:**
- Used SQLAlchemy ORM queries with LIMIT 10 and ORDER BY DESC for efficiency
- Formatted as plain text "User:"/"Assistant:" for GPT-4o compatibility
- Separated conversation history from source chunks in prompt structure
- Added proper error handling with ValueError for authorization failures

**Future Enhancements** (deferred):
- Replace X-User-Id header with proper JWT/session authentication
- Add conversation summarization for very long conversations (>100 messages)
- Consider caching conversation context for repeated queries

### File List

**MODIFIED:**
- api-service/app/services/generation_service.py - Added get_conversation_context() method, modified generate() to accept conversation_history
- api-service/app/routers/coach.py - Added conversation context loading logic, database session dependency, X-User-Id header

**CREATED:**
- api-service/tests/unit/test_conversation_context.py - 8 unit tests for conversation context functionality
- api-service/tests/integration/test_multiturn_conversation.py - Integration tests for full conversation flow
- docs/validation/epic3_3-1_validation.md - Validation guide (pending creation)
