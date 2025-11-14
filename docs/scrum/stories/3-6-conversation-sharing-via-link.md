# Story 3.6: Conversation Sharing via Link

Status: review

## Story

As a team leader,
I want to share helpful conversations with my team,
so that everyone can benefit from the AI coach's guidance.

## Acceptance Criteria

1. **Share Button & Modal:**
   - Given I have a conversation I want to share
   - When I click the "Share" button (icon in conversation header)
   - Then a modal opens with sharing options: generate share link button, expiration options (7 days, 30 days, never), copy link button

2. **Generate Share Link:**
   - Given I click "Generate Share Link"
   - When the link is created
   - Then a unique share token (UUID) is generated and saved
   - And conversation.share_enabled is set to true
   - And share URL is displayed: https://app.plccoach.com/shared/{share_token}
   - And I can copy the link to clipboard

3. **View Shared Conversation:**
   - Given a logged-in user opens a shared link
   - When they access the URL
   - Then they see the full conversation in read-only mode
   - And they cannot send new messages
   - And a banner indicates "Shared by [Owner Name]"

4. **Disable Sharing:**
   - Given I want to stop sharing
   - When I click "Disable Sharing"
   - Then share_enabled is set to false
   - And the share link becomes invalid (404 error)

## Tasks / Subtasks

- [ ] Add share_token and share_enabled to database (AC: #2)
  - [ ] Migration: Add share_token (UUID, nullable, unique) to conversations table
  - [ ] Migration: Add share_enabled (boolean, default false)
  - [ ] Migration: Add share_expires_at (timestamp, nullable)

- [ ] Create Share button UI (AC: #1)
  - [ ] Add share icon to conversation header
  - [ ] Create ShareModal component
  - [ ] Expiration dropdown (7 days, 30 days, never)
  - [ ] Copy link button with clipboard API

- [ ] Implement share link generation endpoint (AC: #2)
  - [ ] POST /api/conversations/{id}/share
  - [ ] Generate UUID for share_token
  - [ ] Set share_enabled = true
  - [ ] Calculate share_expires_at based on selected duration
  - [ ] Return share URL

- [ ] Implement shared conversation view endpoint (AC: #3)
  - [ ] GET /api/conversations/shared/{token}
  - [ ] Verify share_enabled = true
  - [ ] Check share_expires_at not passed
  - [ ] Return conversation with messages (read-only)
  - [ ] Include owner name for banner

- [ ] Create shared conversation UI (AC: #3)
  - [ ] Route: /shared/{token}
  - [ ] Display conversation in read-only mode
  - [ ] Show "Shared by [Name]" banner
  - [ ] Disable message input

- [ ] Implement disable sharing endpoint (AC: #4)
  - [ ] DELETE /api/conversations/{id}/share
  - [ ] Set share_enabled = false
  - [ ] Clear share_token (optional, for security)

- [ ] Testing and validation (AC: all)
  - [ ] Unit test: Share token generation
  - [ ] Integration test: Generate and access shared link
  - [ ] Integration test: Expired shares return 404
  - [ ] Integration test: Disabled shares return 404
  - [ ] Unit test: Copy link to clipboard

## Dev Notes

### Prerequisites
- Story 3.2 (Conversation Persistence)

### Database Schema Changes
```sql
ALTER TABLE conversations
ADD COLUMN share_token UUID UNIQUE,
ADD COLUMN share_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN share_expires_at TIMESTAMP;
```

[Source: docs/epics/epic-3-conversations-history.md#Story-3.6]

## Dev Agent Record

### Context Reference

<!-- Will be filled by story-context workflow -->

### File List

<!-- Will be filled during implementation -->
