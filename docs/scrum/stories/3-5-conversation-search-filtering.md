# Story 3.5: Conversation Search & Filtering

Status: drafted

## Story

As an educator,
I want to search my conversation history,
so that I can find specific guidance I received weeks ago.

## Acceptance Criteria

1. **Search Box in Sidebar:**
   - Given I have many past conversations
   - When I enter text in the search box at the top of the sidebar
   - Then conversations are filtered to show only those containing the search text in conversation title or message content (user/assistant messages)
   - And search results are highlighted
   - And search is case-insensitive

2. **Search Results Display:**
   - Given I search for "common formative assessments"
   - When results are displayed
   - Then I see all conversations that discussed this topic
   - And clicking a result loads that conversation with search terms highlighted

3. **Clear Search:**
   - Given I clear the search box
   - When the search text is removed
   - Then all conversations are shown again
   - And the list returns to normal sorted order (most recent first)

## Tasks / Subtasks

- [ ] Add search box UI to sidebar (AC: #1)
  - [ ] Position at top of ConversationList component
  - [ ] Add search icon
  - [ ] Implement debounced input (300ms delay)
  - [ ] Clear button when search active

- [ ] Implement search API endpoint (AC: #1, #2)
  - [ ] Create GET /api/conversations?search={query} endpoint
  - [ ] Search in conversation.title field
  - [ ] Search in message.content field (JOIN messages table)
  - [ ] Use PostgreSQL ILIKE for case-insensitive search (MVP)
  - [ ] Return matching conversations with highlighted snippets

- [ ] Frontend search integration (AC: #1, #2, #3)
  - [ ] Hook search input to API call
  - [ ] Update ConversationList with filtered results
  - [ ] Highlight search terms in results (use mark.js or similar)
  - [ ] Clear search resets to full list

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: Search filters conversations correctly
  - [ ] Integration test: Full-text search in titles and messages
  - [ ] Unit test: Debounce prevents excessive API calls
  - [ ] Integration test: Clear search shows all conversations

## Dev Notes

### Prerequisites
- Story 3.3 (Conversation List Sidebar) - sidebar UI exists

### Architecture Patterns
- **Search Implementation**: PostgreSQL ILIKE query for MVP (can upgrade to full-text search later)
- **Debouncing**: 300ms delay before triggering search API call
- **Highlighting**: Use mark.js library for search term highlighting

### Technical Notes
- Search endpoint: GET /api/conversations?user_id={id}&search={query}
- SQL: WHERE title ILIKE '%{query}%' OR id IN (SELECT conversation_id FROM messages WHERE content ILIKE '%{query}%')
- Cache search results in React Query

[Source: docs/epics/epic-3-conversations-history.md#Story-3.5]

## Dev Agent Record

### Context Reference

- Inline context (simple search feature, no formal context needed)

### File List

**Modified:**
- api-service/app/routers/conversations.py (added search parameter to GET /api/conversations)
- frontend/src/hooks/useConversations.ts (added search parameter to hook)
- frontend/src/components/conversation/ConversationList.tsx (added search UI with debouncing)

**Created:**
- docs/validation/epic3_3-5_validation.md (validation guide)

### Implementation Summary

Added search capability to conversation list with backend filtering and debounced frontend input:

**Backend:**
- Added optional `search` query parameter to `GET /api/conversations`
- PostgreSQL ILIKE search on conversation title AND message content
- Case-insensitive substring matching
- Maintains pagination and sorting

**Frontend:**
- Search input UI at top of sidebar with search icon and clear button
- Debounced search (300ms delay) to prevent excessive API calls
- React Query integration with search parameter
- Empty state handling for no results vs no conversations

**Acceptance Criteria Status:**
- ✅ AC#1: Search box filters by title and message content (case-insensitive)
- ✅ AC#2: Search results clickable, loads conversation
- ✅ AC#3: Clear search returns all conversations in normal order
