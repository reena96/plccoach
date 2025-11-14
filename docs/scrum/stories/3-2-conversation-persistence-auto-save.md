# Story 3.2: Conversation Persistence & Auto-Save

Status: review

## Story

As an educator,
I want my conversations saved automatically,
so that I don't lose my coaching sessions if I close the browser.

## Acceptance Criteria

1. **Auto-Save Messages:**
   - Given I am in a chat conversation
   - When I send a message
   - Then both my message and the AI response are immediately saved to the database
   - And if no conversation_id exists, a new conversation record is created
   - And the conversation is associated with my user_id

2. **Session Persistence:**
   - Given I close the browser and return later
   - When I access the chat page
   - Then I can continue from where I left off
   - And all previous messages are loaded and displayed

3. **Auto-Generated Title:**
   - Given a conversation is created
   - When the first message is sent
   - Then the conversation title is auto-generated from the first user question (first 50 characters)
   - And the title can be edited later by the user

4. **Timestamp Updates:**
   - Given I send multiple messages in quick succession
   - When each message is processed
   - Then the conversation updated_at timestamp is refreshed
   - And the conversation appears at the top of my history list

## Tasks / Subtasks

- [x] Create conversation on first message (AC: #1)
  - [x] Add logic to /coach/query to create conversation if conversation_id is None
  - [x] Generate new UUID for conversation
  - [x] Associate with user_id from request
  - [x] Return conversation_id in response for subsequent messages

- [x] Save user message to database (AC: #1)
  - [x] Create Message record with role='user'
  - [x] Set conversation_id and content
  - [x] Save immediately after receiving request

- [x] Save assistant response to database (AC: #1)
  - [x] Create Message record with role='assistant'
  - [x] Include citations in JSONB field
  - [x] Save after generation completes
  - [x] Use database transaction for atomicity

- [x] Auto-generate conversation title (AC: #3)
  - [x] Extract first 50 characters from first user message
  - [x] Add "..." if truncated
  - [x] Set as conversation.title on creation
  - [x] Ensure title is editable (field nullable)

- [x] Update conversation timestamps (AC: #4)
  - [x] Update conversations.updated_at on every new message
  - [x] Ensure ORDER BY updated_at DESC for conversation list
  - [x] Test with multiple rapid messages

- [x] Testing and validation (AC: all)
  - [x] Unit test: conversation creation logic
  - [x] Unit test: title generation (< 50 chars, > 50 chars)
  - [x] Integration test: message save atomicity
  - [x] Integration test: timestamp updates correctly
  - [x] Validation guide created

## Dev Notes

### Prerequisites
- Story 1.2 (conversations and messages tables must exist)
- Story 3.1 (chat API context management complete)

### Architecture Patterns and Constraints
- **Database Transactions:** Use atomic transactions for message pairs (user + assistant)
- **Conversation Creation:** Create on-demand when conversation_id is None
- **Title Generation:** First 50 characters of first user message, append "..." if truncated
- **Timestamp Management:** Update conversations.updated_at on every message save
- **No Manual Save:** Everything is automatic, no user action required

### Key Technical Decisions
- **Atomic Saves:** Wrap user message + assistant message + conversation update in single transaction
- **UUID Generation:** Generate conversation_id server-side on first message
- **Title Truncation:** Simple string slicing `content[:50] + "..."` for titles over 50 chars
- **Updated_at Behavior:** SQLAlchemy's `onupdate=datetime.utcnow` handles timestamp refresh
- **Frontend State:** Return conversation_id in response so frontend can track it

### Testing Standards
- Unit tests for conversation creation logic (mocked database)
- Unit tests for title generation (various message lengths)
- Integration tests with real database transactions
- Test edge cases: concurrent messages, very long messages, empty titles

### Project Structure Notes
```
api-service/
├── app/
│   ├── routers/
│   │   └── coach.py (MODIFY - add conversation/message persistence)
│   └── models/
│       ├── conversation.py (existing)
│       └── message.py (existing)
└── tests/
    ├── unit/
    │   └── test_conversation_persistence.py (CREATE)
    └── integration/
        └── test_message_autosave.py (CREATE)
```

### Database Schema Reference
From Story 1.2:
- `conversations` table: id, user_id, title, status, created_at, updated_at
- `messages` table: id, conversation_id, role, content, citations (JSONB), created_at
- Both tables have proper indexes and foreign key constraints

### References
- [Source: docs/epics/epic-3-conversations-history.md#Story-3.2]
- PRD: PRD Section 6.3 (Multi-turn Conversations FR-3.5)
- Database Schema: [Source: docs/stories/1-2-database-schema-creation.md]

### Learnings from Previous Story

**From Story 3-1-multi-turn-conversation-context-management (Status: review)**

- **Database Session Pattern**: Use `db: Session = Depends(get_db)` in endpoint
- **User ID Handling**: Currently using X-User-Id header (TODO: replace with proper auth)
- **Conversation/Message Models**: Already imported and working in generation_service.py
- **UUID Handling**: Use `UUID()` constructor to convert string UUIDs for queries
- **Error Patterns**: Use `HTTPException` with appropriate status codes (404, 500)
- **Testing Pattern**: Mock OpenAI client in tests using `monkeypatch.setenv("OPENAI_API_KEY", "fake-key")`

**Key Files Created in 3.1:**
- Generation service conversation context methods (can reference for database patterns)
- Test patterns in `tests/unit/test_conversation_context.py` (follow same structure)

[Source: docs/scrum/stories/3-1-multi-turn-conversation-context-management.md]

## Dev Agent Record

### Context Reference

- docs/scrum/stories/3-2-conversation-persistence-auto-save.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

N/A - Implementation proceeded smoothly without major debugging required.

### Completion Notes List

✅ **Implementation Summary:**

1. **Modified /api/coach/query endpoint** to add conversation persistence:
   - Added conversation creation logic when conversation_id is None
   - Auto-generates title from first 50 chars of user query (adds "..." if longer)
   - Saves user message immediately after receiving request (using db.flush())
   - Saves assistant message after generation completes (with citations as JSONB)
   - Uses atomic transaction: conversation + user message + assistant message commit together
   - Returns conversation_id in response so frontend can track it

2. **Updated QueryResponse model**:
   - Added conversation_id field (Optional[str])
   - Allows frontend to receive and store conversation_id for subsequent requests

3. **Atomic transaction pattern**:
   - Step 0: Create conversation (db.add + db.flush)
   - Step 0.5: Save user message (db.add + db.flush)
   - Step 1-2: Retrieve + generate (existing logic)
   - Step 3: Save assistant message (db.add + db.commit)
   - All three saves commit together for atomicity

4. **Error handling**:
   - Wrapped each persistence step in try/except
   - Rolls back on SQLAlchemyError
   - Non-fatal: if persistence fails, response is still returned (graceful degradation)
   - Logging at each step for debugging

5. **Comprehensive test coverage**:
   - 20 unit tests covering all acceptance criteria
   - Integration tests for full API flow (with mocked AI services)
   - Tests for edge cases: long messages, special characters, missing user_id
   - All 20 unit tests passing ✓

**Key Technical Decisions:**
- Used db.flush() for intermediate saves to get UUIDs without committing
- Single db.commit() at end ensures all-or-nothing atomicity
- Title generation: simple string slicing `query[:50] + "..."` for titles > 50 chars
- UUID conversion: `UUID(string_id)` for SQLAlchemy compatibility
- Non-fatal error handling: continue serving responses even if persistence fails

**Database Updates:**
- No schema changes required (tables from Story 1.2)
- Conversations.updated_at uses SQLAlchemy onupdate=datetime.utcnow
- Messages.citations stored as JSONB (PostgreSQL native JSON)

**Future Enhancements** (deferred):
- Title editing API endpoint (Story 3.3)
- Replace X-User-Id header with proper JWT authentication (Epic 4)
- Conversation summarization for very long conversations (Epic 4)

### File List

**MODIFIED:**
- api-service/app/routers/coach.py - Added conversation creation, user/assistant message persistence, atomic transaction logic

**CREATED:**
- api-service/tests/unit/test_conversation_persistence.py - 20 unit tests for conversation persistence
- api-service/tests/integration/test_message_autosave.py - Integration tests for full API flow
- docs/validation/epic3_3-2_validation.md - Comprehensive validation guide with manual test steps
