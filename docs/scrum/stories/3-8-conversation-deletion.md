# Story 3.8: Conversation Deletion

Status: drafted

## Story

As an educator,
I want to permanently delete conversations,
so that I can remove sensitive or unwanted discussions.

## Acceptance Criteria

1. **Delete Confirmation:**
   - Given I want to delete a conversation
   - When I click "Delete" from the three-dot menu
   - Then a confirmation modal appears: "Are you sure? This cannot be undone."

2. **Confirm Deletion:**
   - Given I confirm deletion
   - When I click "Yes, Delete"
   - Then the conversation and all associated messages are permanently deleted from the database
   - And the conversation disappears from the sidebar
   - And if I was viewing that conversation, I am redirected to a new conversation or dashboard

3. **Cancel Deletion:**
   - Given I cancel deletion
   - When I click "Cancel" or close the modal
   - Then the conversation remains unchanged
   - And no deletion occurs

4. **Shared Conversation Deletion:**
   - Given a conversation has been shared
   - When I delete it
   - Then the share link becomes invalid (404)
   - And any users viewing the shared link see "This conversation has been deleted"

## Tasks / Subtasks

- [ ] Create delete endpoint (AC: #2, #4)
  - [ ] DELETE /api/conversations/{id}
  - [ ] Verify CASCADE delete configured for messages
  - [ ] Return 204 No Content on success
  - [ ] Invalidate share links (set share_enabled = false)

- [ ] Add Delete to three-dot menu (AC: #1)
  - [ ] "Delete" option in menu (styled in red/danger color)
  - [ ] Trigger confirmation modal

- [ ] Create confirmation modal (AC: #1, #3)
  - [ ] Modal with warning message
  - [ ] "Yes, Delete" button (danger style)
  - [ ] "Cancel" button
  - [ ] Close on backdrop click or X

- [ ] Handle post-deletion (AC: #2)
  - [ ] Remove from sidebar immediately
  - [ ] If viewing deleted conversation, redirect
  - [ ] Show success toast

- [ ] Testing and validation (AC: all)
  - [ ] Integration test: Delete removes conversation and messages
  - [ ] Unit test: Confirmation modal prevents accidental deletion
  - [ ] Integration test: Shared links invalidated after deletion
  - [ ] Unit test: Cancel preserves conversation

## Dev Notes

### Database Cascade
- messages table has ON DELETE CASCADE for conversation_id foreign key
- Deleting conversation automatically deletes all messages

### Alternative: Soft Delete
- Consider adding deleted_at timestamp instead of hard delete
- Allows data retention and potential recovery
- Filter queries: WHERE deleted_at IS NULL

[Source: docs/epics/epic-3-conversations-history.md#Story-3.8]

## Dev Agent Record

### Context Reference

<!-- Will be filled by story-context workflow -->

### File List

<!-- Will be filled during implementation -->
