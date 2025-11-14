# Story 3.3: Conversation List Sidebar

Status: ready-for-dev

## Story

As an educator,
I want to see a list of my past conversations,
so that I can easily navigate between different coaching sessions.

## Acceptance Criteria

1. **Sidebar Display:**
   - Given I have multiple saved conversations
   - When I view the chat page
   - Then I see a left sidebar with a list of my conversations
   - And conversations are ordered by updated_at (most recent first)

2. **Conversation Item Display:**
   - Given I view the conversation list
   - When I look at each conversation item
   - Then each item shows:
     - Conversation title (auto-generated or user-edited)
     - Preview of first message (first 60 characters)
     - Timestamp (relative: "2 hours ago", "3 days ago", or absolute for older)
     - Unread indicator if new messages (future enhancement - can defer)

3. **Conversation Selection:**
   - Given I click on a conversation in the sidebar
   - When it loads
   - Then all messages in that conversation are displayed in the main chat area
   - And the conversation is highlighted in the sidebar as active

4. **Pagination & Infinite Scroll:**
   - Given the sidebar contains many conversations (>20)
   - When I scroll down
   - Then conversations are loaded with pagination (20 at a time)
   - And additional conversations load as I scroll (infinite scroll)

5. **Mobile Responsiveness:**
   - Given I am on mobile
   - When I view the chat page
   - Then the sidebar is hidden by default
   - And a hamburger menu button toggles the sidebar visibility

## Tasks / Subtasks

- [ ] Create API endpoint for fetching conversations (AC: #1, #4)
  - [ ] Implement GET /api/conversations endpoint
  - [ ] Add query parameters: user_id, limit (default=20), offset
  - [ ] Order by updated_at DESC
  - [ ] Return conversation list with: id, title, first_message_preview, updated_at
  - [ ] Add pagination metadata to response

- [ ] Create ConversationList React component (AC: #1, #2, #3)
  - [ ] Set up component file: frontend/src/components/conversation/ConversationList.tsx
  - [ ] Implement conversation item rendering
  - [ ] Display title, preview (60 chars), and timestamp
  - [ ] Add active conversation highlighting
  - [ ] Handle click to load conversation

- [ ] Implement timestamp formatting (AC: #2)
  - [ ] Use relative time for recent conversations ("2 hours ago", "3 days ago")
  - [ ] Use absolute date for older conversations (>7 days)
  - [ ] Consider using date-fns or similar library

- [ ] Implement pagination with infinite scroll (AC: #4)
  - [ ] Use React Query for data fetching and caching
  - [ ] Implement useInfiniteQuery for pagination
  - [ ] Add intersection observer for infinite scroll trigger
  - [ ] Show loading spinner while fetching next page

- [ ] Add mobile responsiveness (AC: #5)
  - [ ] Hide sidebar by default on mobile (<768px)
  - [ ] Add hamburger menu button
  - [ ] Implement toggle functionality
  - [ ] Sidebar full width on mobile when open
  - [ ] Close sidebar after selecting conversation on mobile

- [ ] Implement "New Conversation" button (UI only, functionality in Story 3.4)
  - [ ] Add button at top of sidebar
  - [ ] Style consistently with design system
  - [ ] Wire up to future new conversation handler (placeholder for now)

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: ConversationList component rendering
  - [ ] Unit test: Timestamp formatting
  - [ ] Integration test: Pagination and infinite scroll
  - [ ] Integration test: Conversation selection
  - [ ] Responsive test: Mobile sidebar toggle
  - [ ] Validation guide created

## Dev Notes

### Prerequisites
- **CRITICAL**: Story 3.2 (Conversation Persistence) must be complete - conversations and messages must be saved
- **CRITICAL**: Frontend application must be initialized (React + TypeScript setup)
- **ALERT**: No frontend directory found in current project structure. Frontend setup (Story 1.7) may need to be completed first.

### Architecture Patterns and Constraints
- **Component Location**: /frontend/src/components/conversation/ConversationList.tsx
- **Data Fetching**: Use React Query (TanStack Query) for caching and pagination
- **Styling**: Sidebar width 280px on desktop, full width on mobile
- **Performance**: Implement virtual scrolling for large conversation lists
- **Mobile Breakpoint**: 768px (standard tablet breakpoint)
- **API Endpoint**: GET /api/conversations?user_id={id}&limit=20&offset=0

### Key Technical Decisions
- **Pagination Strategy**: 20 conversations per page with infinite scroll
- **Timestamp Library**: Use date-fns for relative time formatting
- **Virtual Scrolling**: For performance with 100+ conversations (defer if not needed initially)
- **Mobile Pattern**: Slide-in sidebar with overlay (standard mobile nav pattern)
- **State Management**: React Query for server state, React Context/useState for UI state

### Testing Standards
- Unit tests for component rendering (Jest + React Testing Library)
- Integration tests for pagination (mock API responses)
- Responsive tests using viewport emulation
- Test edge cases: empty list, single conversation, 100+ conversations

### Project Structure Notes
```
frontend/
├── src/
│   ├── components/
│   │   └── conversation/
│   │       ├── ConversationList.tsx (CREATE)
│   │       ├── ConversationItem.tsx (CREATE)
│   │       └── ConversationList.test.tsx (CREATE)
│   ├── hooks/
│   │   └── useConversations.ts (CREATE - React Query hook)
│   └── utils/
│       └── formatTimestamp.ts (CREATE)
api-service/
└── app/
    └── routers/
        └── conversations.py (MODIFY - add GET endpoint)
```

### API Endpoint Specification

**GET /api/conversations**

Query Parameters:
- user_id (required): UUID of current user
- limit (optional, default=20): Number of conversations to return
- offset (optional, default=0): Pagination offset

Response:
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "What is project-based learning?",
      "first_message_preview": "What is project-based learning and how can I impl...",
      "updated_at": "2025-11-14T10:30:00Z",
      "message_count": 4
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### References
- [Source: docs/epics/epic-3-conversations-history.md#Story-3.3]
- Database Schema: conversations table (Story 1.2)
- Conversation Persistence: Story 3.2 implementation

### Learnings from Previous Story

**From Story 3-2-conversation-persistence-auto-save (Status: review)**

- **Database Pattern**: Use `db: Session = Depends(get_db)` for database access in endpoints
- **User ID Handling**: Currently using X-User-Id header (temporary - will be replaced with proper auth in Epic 4)
- **Conversation Model**: Available at `app/models/conversation.py` with fields: id, user_id, title, status, created_at, updated_at
- **Message Model**: Available at `app/models/message.py` with role, content, citations
- **Query Pattern**: Use SQLAlchemy ORM with ORDER BY updated_at DESC for chronological sorting
- **UUID Handling**: Use `UUID()` constructor to convert string UUIDs for database queries
- **Title Generation**: Titles are auto-generated from first 50 chars of first message + "..." if longer
- **API Response Pattern**: Include metadata in responses (e.g., conversation_id returned after creation)

**Key Files Created in Story 3.2:**
- api-service/app/routers/coach.py - Modified to add conversation persistence
- Conversation and Message models - Already exist and working

[Source: docs/scrum/stories/3-2-conversation-persistence-auto-save.md#Dev-Agent-Record]

## Dev Agent Record

### Context Reference

- docs/scrum/stories/3-3-conversation-list-sidebar.context.xml

### Agent Model Used

<!-- Will be filled during implementation -->

### Debug Log References

<!-- Will be filled during implementation -->

### Completion Notes List

<!-- Will be filled during implementation -->

### File List

<!-- Will be filled during implementation -->
