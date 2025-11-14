# Story 3.7: Conversation Archiving

Status: drafted

## Story

As an educator,
I want to archive old conversations,
so that my active conversation list stays organized without deleting valuable history.

## Acceptance Criteria

1. **Archive Conversation:**
   - Given I have a conversation I no longer need in my active list
   - When I click the archive button (three-dot menu → Archive)
   - Then the conversation status is updated to 'archived'
   - And it is removed from the main conversation list

2. **View Archived Conversations:**
   - Given I want to view archived conversations
   - When I click "Show Archived" toggle in sidebar
   - Then archived conversations appear in a separate section
   - And they are visually distinguished (grayed out or different icon)

3. **Unarchive Conversation:**
   - Given I want to restore an archived conversation
   - When I click "Unarchive" from the three-dot menu
   - Then the conversation status is updated to 'active'
   - And it returns to the main conversation list

4. **Redirect After Archiving Current:**
   - Given I archive a conversation I'm currently viewing
   - When the archive action completes
   - Then I am redirected to a new empty conversation or the most recent active conversation

## Tasks / Subtasks

- [ ] Update conversations status field (AC: #1)
  - [ ] Verify status field exists with values: 'active', 'archived'
  - [ ] Default to 'active' for new conversations
  - [ ] Add database index on status for efficient filtering

- [ ] Create archive endpoint (AC: #1, #3)
  - [ ] PATCH /api/conversations/{id}/archive (sets status='archived')
  - [ ] PATCH /api/conversations/{id}/unarchive (sets status='active')
  - [ ] Return updated conversation

- [ ] Add three-dot menu to conversation items (AC: #1, #3)
  - [ ] Menu icon in ConversationItem component
  - [ ] Archive/Unarchive option based on current status
  - [ ] Other future options: Share, Export, Delete

- [ ] Implement "Show Archived" toggle (AC: #2)
  - [ ] Toggle/tab at top of sidebar
  - [ ] Filter API call by status when toggled
  - [ ] Visual distinction for archived items (gray, icon)

- [ ] Handle current conversation archiving (AC: #4)
  - [ ] Detect if archiving active conversation
  - [ ] Redirect to new conversation or recent active
  - [ ] Clear chat area

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: Archive updates status to 'archived'
  - [ ] Integration test: Archived conversations hidden from main list
  - [ ] Integration test: Show Archived displays archived conversations
  - [ ] Integration test: Unarchive restores to main list

## Dev Notes

### Database Schema
- conversations.status already exists with values: 'active', 'archived'
- Filter queries: WHERE status = 'active' for main list
- WHERE status = 'archived' for archived view

[Source: docs/epics/epic-3-conversations-history.md#Story-3.7]

## Dev Agent Record

### Context Reference

<!-- Will be filled by story-context workflow -->

### File List

<!-- Will be filled during implementation -->
