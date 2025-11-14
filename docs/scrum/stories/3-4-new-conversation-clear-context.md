# Story 3.4: New Conversation & Clear Context

Status: drafted

## Story

As an educator,
I want to start a fresh conversation,
so that I can ask about a different topic without confusing context.

## Acceptance Criteria

1. **New Conversation Button:**
   - Given I am in an existing conversation
   - When I click the "New Conversation" button
   - Then the chat area clears
   - And a new conversation record is created in the database
   - And I see the welcome message and example questions again
   - And the conversation_id for subsequent messages is the new conversation ID
   - And the previous conversation remains in the sidebar list

2. **New Conversation from Past Conversation:**
   - Given I am viewing a past conversation (loaded from sidebar)
   - When I click "New Conversation"
   - Then a new conversation starts with cleared context
   - And I can still navigate back to view the previous conversation

3. **Empty Conversation Cleanup:**
   - Given I have an empty conversation (no messages sent yet)
   - When I navigate away without sending any messages
   - Then the empty conversation is not saved to the sidebar list
   - And it is cleaned up from the database (optional - can be done via background job)

## Tasks / Subtasks

- [ ] Add "New Conversation" button to sidebar (AC: #1)
  - [ ] Position button prominently at top of ConversationList component
  - [ ] Style consistently with design system
  - [ ] Add icon (plus sign or similar)
  - [ ] Make accessible on both desktop and mobile

- [ ] Implement new conversation creation logic (AC: #1)
  - [ ] Generate new UUID for conversation_id on button click
  - [ ] Clear chat area messages
  - [ ] Reset conversation state in frontend
  - [ ] Show welcome message and example questions
  - [ ] Set new conversation_id for subsequent API calls

- [ ] Defer database record creation until first message (AC: #1)
  - [ ] Don't create conversation record on button click
  - [ ] Let existing POST /api/coach/query create conversation on first message
  - [ ] Frontend tracks conversation_id = null initially
  - [ ] After first message, store returned conversation_id

- [ ] Update sidebar to reflect new conversation (AC: #1)
  - [ ] Highlight new conversation as active
  - [ ] Keep previous conversations visible in list
  - [ ] Refresh conversation list after first message sent

- [ ] Handle navigation from past conversations (AC: #2)
  - [ ] Allow clicking "New Conversation" from any conversation view
  - [ ] Preserve ability to navigate back to previous conversations
  - [ ] Update active conversation highlight appropriately

- [ ] Implement empty conversation cleanup (AC: #3)
  - [ ] Optional: Background job to delete conversations with 0 messages after 24 hours
  - [ ] Or: Check on conversation load, hide/delete if no messages
  - [ ] Ensure sidebar only shows conversations with at least 1 message

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: New conversation button triggers state reset
  - [ ] Integration test: New conversation clears chat and shows welcome
  - [ ] Integration test: First message creates conversation record
  - [ ] Integration test: Can navigate between old and new conversations
  - [ ] Unit test: Empty conversations not shown in sidebar
  - [ ] Validation guide created

## Dev Notes

### Prerequisites
- Story 3.2 (Conversation Persistence) - conversation creation logic exists
- Story 3.3 (Conversation List Sidebar) - sidebar UI with button location

### Architecture Patterns and Constraints
- **No Premature Database Creation**: Don't create conversation record until first message sent
- **State Management**: Clear frontend conversation context on new conversation
- **UUID Generation**: Generate conversation_id client-side, server validates/uses it
- **Welcome Message**: Re-display onboarding content (example questions, instructions)
- **Sidebar Sync**: Refresh conversation list after first message of new conversation

### Key Technical Decisions
- **Lazy Conversation Creation**: Prevents database clutter from abandoned conversations
- **Client-Side UUID**: Frontend generates UUID, sends with first message
- **State Reset**: Clear messages array, conversation_id, and any cached context
- **Background Cleanup**: Optional job to delete empty conversations after 24 hours (can defer)
- **Sidebar Filter**: Only show conversations with message_count > 0

### Testing Standards
- Unit tests for state management and button behavior
- Integration tests for full new conversation flow
- Test edge cases: rapid clicking, navigation during creation, abandoned conversations
- Verify database cleanup (if implemented)

### Project Structure Notes
```
frontend/
├── src/
│   ├── components/
│   │   └── conversation/
│   │       ├── ConversationList.tsx (MODIFY - add button)
│   │       └── NewConversationButton.tsx (CREATE)
│   ├── hooks/
│   │   └── useNewConversation.ts (CREATE)
│   └── contexts/
│       └── ConversationContext.tsx (MODIFY - add reset function)
api-service/
└── app/
    └── routers/
        ├── coach.py (existing - already creates conversations on first message)
        └── conversations.py (MODIFY - filter empty conversations in list)
```

### References
- [Source: docs/epics/epic-3-conversations-history.md#Story-3.4]
- Conversation Creation: Story 3.2 (POST /api/coach/query creates on first message)
- Sidebar UI: Story 3.3 (button placement)

### Learnings from Previous Story

**From Story 3-3-conversation-list-sidebar (Status: ready-for-dev)**

- **Frontend Blocker**: No frontend directory exists yet. Story 1.7 (Frontend Application Shell) is prerequisite.
- **API Endpoint Pattern**: GET /api/conversations established for sidebar
- **Pagination**: 20 conversations per page with infinite scroll
- **Component Structure**: ConversationList.tsx is the main sidebar component
- **Database Models**: Conversation and Message models available at app/models/
- **Timestamp Handling**: Use date-fns for relative time formatting

[Source: docs/scrum/stories/3-3-conversation-list-sidebar.md]

## Dev Agent Record

### Context Reference

<!-- Path to story context XML will be added by story-context workflow -->

### Agent Model Used

<!-- Will be filled during implementation -->

### Debug Log References

<!-- Will be filled during implementation -->

### Completion Notes List

<!-- Will be filled during implementation -->

### File List

<!-- Will be filled during implementation -->
