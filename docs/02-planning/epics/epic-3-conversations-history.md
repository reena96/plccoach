# Epic 3: Conversations & History

**Author:** Reena
**Date:** 2025-11-12
**Duration:** 2-3 weeks
**Project:** AI Powered PLC at Work Virtual Coach

---

## Epic Goal

Enable persistent, context-aware multi-turn conversations with searchable history and sharing capabilities, allowing educators to build on previous discussions and collaborate with colleagues.

**Business Value:** Users can have ongoing coaching conversations that build context over time, review past guidance weeks later, and share helpful conversations with team members. This transforms the coach from a one-off Q&A tool into a persistent learning companion.

---

## Stories

### Story 3.1: Multi-Turn Conversation Context Management

**As an** educator,
**I want** the AI coach to remember our conversation,
**So that** I can ask follow-up questions without repeating context.

**Acceptance Criteria:**

**Given** I have an active conversation with messages
**When** I ask a follow-up question
**Then** the AI coach receives the last 10 messages as context

**And** the conversation history is formatted in the prompt as:
```
User: [First question]
Assistant: [First response]
User: [Second question]
Assistant: [Second response]
...
User: [Current question]
```

**And** the response considers previous context

**Given** the conversation exceeds 10 message turns
**When** I ask a new question
**Then** only the most recent 10 messages are included as context

**And** older messages are still stored but not sent to the AI

**Given** I ask "Can you elaborate on that?"
**When** the AI generates a response
**Then** it references the previous response appropriately

**And** maintains coherence with the conversation flow

**Prerequisites:** Epic 2 Story 2.8 (chat API must exist)

**Technical Notes:**
- Implement conversation context assembly in generation service
- Limit context to last 10 messages to manage token costs
- Include conversation_id in all /coach/query requests
- Load messages from database ordered by created_at
- Summarize older messages if conversation becomes very long (future enhancement)
- Reference: TECHNICAL_ARCHITECTURE.md Section 4.3 (Response Generation with history)
- Reference: PRD Section 6.3 (Multi-turn Conversations FR-3.1)

---

### Story 3.2: Conversation Persistence & Auto-Save

**As an** educator,
**I want** my conversations saved automatically,
**So that** I don't lose my coaching sessions if I close the browser.

**Acceptance Criteria:**

**Given** I am in a chat conversation
**When** I send a message
**Then** both my message and the AI response are immediately saved to the database

**And** if no conversation_id exists, a new conversation record is created

**And** the conversation is associated with my user_id

**Given** I close the browser and return later
**When** I access the chat page
**Then** I can continue from where I left off

**And** all previous messages are loaded and displayed

**Given** a conversation is created
**When** the first message is sent
**Then** the conversation title is auto-generated from the first user question (first 50 characters)

**And** the title can be edited later by the user

**Given** I send multiple messages in quick succession
**When** each message is processed
**Then** the conversation updated_at timestamp is refreshed

**And** the conversation appears at the top of my history list

**Prerequisites:** Epic 1 Story 1.2 (conversations and messages tables must exist)

**Technical Notes:**
- Implement auto-save on every message
- Use database transactions to ensure message pairs (user + assistant) are saved atomically
- Generate conversation title from first user message (truncate at 50 chars, add "...")
- Update conversations.updated_at on every new message for sorting
- No manual "Save" button needed - everything is automatic
- Reference: PRD Section 6.3 (Multi-turn Conversations FR-3.5)

---

### Story 3.3: Conversation List Sidebar

**As an** educator,
**I want** to see a list of my past conversations,
**So that** I can easily navigate between different coaching sessions.

**Acceptance Criteria:**

**Given** I have multiple saved conversations
**When** I view the chat page
**Then** I see a left sidebar with a list of my conversations

**And** conversations are ordered by updated_at (most recent first)

**And** each conversation item shows:
- Conversation title (auto-generated or user-edited)
- Preview of first message (first 60 characters)
- Timestamp (relative: "2 hours ago", "3 days ago", or absolute for older)
- Unread indicator if new messages (future enhancement)

**Given** I click on a conversation
**When** it loads
**Then** all messages in that conversation are displayed

**And** the conversation is highlighted in the sidebar as active

**Given** the sidebar contains many conversations
**When** I scroll down
**Then** conversations are loaded with pagination (20 at a time)

**And** additional conversations load as I scroll (infinite scroll)

**Given** I am on mobile
**When** I view the chat page
**Then** the sidebar is hidden by default

**And** a hamburger menu button toggles the sidebar visibility

**Prerequisites:** Story 3.2 (conversations must be persisted)

**Technical Notes:**
- Implement in `/frontend/src/components/conversation/ConversationList.tsx`
- Use React Query for data fetching with caching
- Implement virtual scrolling for performance with many conversations
- Sidebar width: 280px on desktop, full width on mobile
- Add "New Conversation" button at top of sidebar
- Reference: TECHNICAL_ARCHITECTURE.md Section 2.1 (Frontend Application)
- Reference: PRD Section 8.1 (Conversation Sidebar)

---

### Story 3.4: New Conversation & Clear Context

**As an** educator,
**I want** to start a fresh conversation,
**So that** I can ask about a different topic without confusing context.

**Acceptance Criteria:**

**Given** I am in an existing conversation
**When** I click the "New Conversation" button
**Then** the chat area clears

**And** a new conversation record is created in the database

**And** I see the welcome message and example questions again

**And** the conversation_id for subsequent messages is the new conversation ID

**And** the previous conversation remains in the sidebar list

**Given** I am viewing a past conversation
**When** I click "New Conversation"
**Then** a new conversation starts

**And** I can still navigate back to view the previous conversation

**Given** I have an empty conversation (no messages sent yet)
**When** I navigate away without sending any messages
**Then** the empty conversation is not saved to the sidebar list

**And** it is cleaned up from the database (optional - can be done via background job)

**Prerequisites:** Story 3.3 (sidebar must exist)

**Technical Notes:**
- "New Conversation" button prominent at top of sidebar
- Clear frontend state when starting new conversation
- Generate new UUID for conversation_id
- Don't create database record until first message is sent
- Optional: Background job to clean up conversations with 0 messages after 24 hours
- Reference: PRD Section 6.3 (Multi-turn Conversations FR-3.4)

---

### Story 3.5: Conversation Search & Filtering

**As an** educator,
**I want** to search my conversation history,
**So that** I can find specific guidance I received weeks ago.

**Acceptance Criteria:**

**Given** I have many past conversations
**When** I enter text in the search box at the top of the sidebar
**Then** conversations are filtered to show only those containing the search text in:
- Conversation title
- Message content (user or assistant messages)

**And** search results are highlighted in the conversation list

**And** search is case-insensitive

**Given** I search for "common formative assessments"
**When** results are displayed
**Then** I see all conversations that discussed this topic

**And** clicking a result loads that conversation with search terms highlighted

**Given** I clear the search box
**When** the search text is removed
**Then** all conversations are shown again

**And** the list returns to normal sorted order (most recent first)

**Given** I filter by status (active, archived - future enhancement)
**When** I select a filter
**Then** only conversations matching that status are shown

**Prerequisites:** Story 3.3 (conversation list must exist)

**Technical Notes:**
- Implement search API endpoint: `GET /api/conversations?search=query`
- Use PostgreSQL full-text search or simple LIKE query for MVP
- Debounce search input (300ms delay before querying)
- Cache search results in React Query
- Highlight search terms in results using mark.js or similar
- Reference: PRD Section 6.4 (Conversation History FR-4.6)

---

### Story 3.6: Conversation Sharing via Link

**As a** team leader,
**I want** to share helpful conversations with my team,
**So that** everyone can benefit from the AI coach's guidance.

**Acceptance Criteria:**

**Given** I have a conversation I want to share
**When** I click the "Share" button (icon in conversation header)
**Then** a modal opens with sharing options:
- "Generate Share Link" button
- Option to set expiration (7 days, 30 days, never)
- Copy link button

**Given** I click "Generate Share Link"
**When** the link is created
**Then** a unique share token is generated and saved to the conversation record

**And** the conversation.share_enabled field is set to true

**And** the share URL is displayed: `https://app.plccoach.com/shared/{share_token}`

**And** I can copy the link to clipboard

**Given** someone opens a shared conversation link
**When** they are not logged in
**Then** they are prompted to log in first

**Given** a logged-in user opens a shared link
**When** they access the URL
**Then** they see the full conversation in read-only mode

**And** they cannot send new messages (viewing only)

**And** a banner indicates "Shared by [Owner Name]"

**Given** I want to stop sharing a conversation
**When** I click "Disable Sharing"
**Then** the share_enabled field is set to false

**And** the share link becomes invalid (404 error)

**Prerequisites:** Story 3.2 (conversations must be persisted)

**Technical Notes:**
- Generate share_token as UUID
- Add share_token and share_enabled columns to conversations table (if not already added in Epic 1)
- Implement `GET /api/conversations/shared/:token` endpoint
- Add "Shared by" banner in UI for shared conversations
- Optional: Track view count on shared conversations
- Reference: PRD Section 6.4 (Conversation History FR-4.9)

---

### Story 3.7: Conversation Archiving

**As an** educator,
**I want** to archive old conversations,
**So that** my active conversation list stays organized without deleting valuable history.

**Acceptance Criteria:**

**Given** I have a conversation I no longer need in my active list
**When** I click the archive button (three-dot menu → Archive)
**Then** the conversation status is updated to 'archived'

**And** it is removed from the main conversation list

**Given** I want to view archived conversations
**When** I click "Show Archived" toggle in sidebar
**Then** archived conversations appear in a separate section

**And** they are visually distinguished (grayed out or different icon)

**Given** I want to restore an archived conversation
**When** I click "Unarchive" from the three-dot menu
**Then** the conversation status is updated to 'active'

**And** it returns to the main conversation list

**Given** I archive a conversation I'm currently viewing
**When** the archive action completes
**Then** I am redirected to a new empty conversation or the most recent active conversation

**Prerequisites:** Story 3.3 (conversation list must exist)

**Technical Notes:**
- Add status field to conversations table: 'active' | 'archived' (default: 'active')
- Update sidebar query to filter by status
- Add toggle UI element: "Show Archived" checkbox or tab
- Archive action updates database via `PATCH /api/conversations/:id`
- Reference: PRD Section 6.4 (Conversation History FR-4.7)

---

### Story 3.8: Conversation Deletion

**As an** educator,
**I want** to permanently delete conversations,
**So that** I can remove sensitive or unwanted discussions.

**Acceptance Criteria:**

**Given** I want to delete a conversation
**When** I click "Delete" from the three-dot menu
**Then** a confirmation modal appears: "Are you sure? This cannot be undone."

**Given** I confirm deletion
**When** I click "Yes, Delete"
**Then** the conversation and all associated messages are permanently deleted from the database

**And** the conversation disappears from the sidebar

**And** if I was viewing that conversation, I am redirected to a new conversation or dashboard

**Given** I cancel deletion
**When** I click "Cancel" or close the modal
**Then** the conversation remains unchanged

**And** no deletion occurs

**Given** a conversation has been shared
**When** I delete it
**Then** the share link becomes invalid (404)

**And** any users viewing the shared link see "This conversation has been deleted"

**Prerequisites:** Story 3.7 (archive must exist as alternative to deletion)

**Technical Notes:**
- Use CASCADE delete to remove all messages when conversation is deleted
- Implement `DELETE /api/conversations/:id` endpoint
- Require double confirmation for safety
- Log deletion events for audit purposes
- Consider soft delete (deleted_at timestamp) instead of hard delete for data retention
- Reference: PRD Section 6.4 (Conversation History FR-4.8)

---

### Story 3.9: Conversation Export (PDF/Text)

**As a** team leader,
**I want** to export conversations as PDF or text files,
**So that** I can include coaching guidance in meeting notes or share offline.

**Acceptance Criteria:**

**Given** I am viewing a conversation
**When** I click "Export" from the three-dot menu
**Then** I see export format options:
- PDF (formatted, with citations)
- Text (plain text, markdown)

**Given** I select "Export as PDF"
**When** the export generates
**Then** a PDF file is created with:
- Conversation title
- Date and timestamp
- All messages (user and assistant)
- Citations formatted and preserved
- Solution Tree branding/footer

**And** the PDF downloads to my device

**Given** I select "Export as Text"
**When** the export generates
**Then** a .txt or .md file is created with:
- Markdown formatting
- Message timestamps
- Citations preserved

**And** the file downloads to my device

**Given** I export a long conversation (50+ messages)
**When** the export processes
**Then** it completes within 10 seconds

**And** page breaks are handled appropriately in PDF

**Prerequisites:** Story 3.2 (conversations must be persisted)

**Technical Notes:**
- Implement `POST /api/conversations/:id/export` endpoint
- Use a library like ReportLab (Python) or Puppeteer (Node.js) for PDF generation
- Generate exports asynchronously for large conversations
- Store temporary exports in S3 with pre-signed URLs (expire after 1 hour)
- Consider rate limiting exports (10 per day per user)
- Reference: PRD Section 6.4 (Conversation History FR-4.10)

---

### Story 3.10: All 7 Knowledge Domains Operational

**As a** product owner,
**I want** all 7 knowledge domains to be fully operational,
**So that** educators can get guidance on any PLC topic.

**Acceptance Criteria:**

**Given** the content ingestion from Epic 2 is complete
**When** domain testing is performed
**Then** queries for each of the 7 domains return relevant responses:

1. **Assessment & Evaluation**
   - Test query: "What makes a good common formative assessment?"
   - Expected: Response cites books like "Collaborative Common Assessments"

2. **Collaborative Teams**
   - Test query: "How do we establish effective team norms?"
   - Expected: Response cites "Learning by Doing" or "Handbook for Collaborative Teams"

3. **Leadership & Administration**
   - Test query: "What is the role of the principal in a PLC?"
   - Expected: Response cites "Leaders of Learning"

4. **Curriculum & Instruction**
   - Test query: "What is a guaranteed and viable curriculum?"
   - Expected: Response cites relevant curriculum-focused books

5. **Data Analysis & Response**
   - Test query: "How do we implement RTI effectively?"
   - Expected: Response cites "Simplifying Response to Intervention"

6. **School Culture & Systems**
   - Test query: "How do we shift to a PLC culture?"
   - Expected: Response cites implementation-focused books

7. **Student Learning & Engagement**
   - Test query: "How do we increase student engagement?"
   - Expected: Response cites student-focused practices books

**And** cross-domain queries work correctly:
- Test query: "How do assessments connect to RTI?"
- Expected: Response pulls from both "assessment" and "data_analysis" domains

**And** clarification prompts trigger for vague queries:
- Test query: "Tell me about PLCs"
- Expected: Clarification question about specific area of interest

**Prerequisites:** Epic 2 (all AI infrastructure must be complete)

**Technical Notes:**
- Create comprehensive test suite: `/tests/domain-coverage-tests.md`
- Test 3-5 queries per domain (21-35 total test queries)
- Validate intent routing correctly identifies domains
- Verify retrieval returns chunks from correct domain books
- Document any gaps in content coverage
- Reference: PRD Section 9.2 (Domain Taxonomy)

---

### Story 3.11: Conversation UI Polish & Responsiveness

**As a** user,
**I want** a polished, professional chat experience,
**So that** the interface feels reliable and easy to use during meetings.

**Acceptance Criteria:**

**Given** I am using the chat interface
**When** I interact with it
**Then** the following polish features are present:

**Visual Polish:**
- Smooth message animations (fade in, slide up)
- Loading states with animated spinner or typing indicator
- Empty states with helpful messages
- Proper spacing and typography (readable on all devices)
- Solution Tree brand colors and styling

**Interaction Polish:**
- Enter key sends message (Shift+Enter for new line)
- Auto-focus on input field after sending message
- Auto-scroll to latest message when new message arrives
- Character count indicator if message limits exist (optional)
- Disabled state for send button when input is empty

**Responsive Design:**
- Desktop (>1024px): Sidebar visible, chat area centered, max-width 800px
- Tablet (768-1023px): Collapsible sidebar, optimized for landscape
- Mobile (<768px): Full-width chat, sidebar as slide-out drawer

**Accessibility:**
- Keyboard navigation support (Tab through elements)
- Screen reader compatible (ARIA labels)
- Sufficient color contrast (WCAG 2.1 AA)
- Focus indicators visible

**Given** I am on mobile
**When** I type a message
**Then** the virtual keyboard doesn't obscure the input field

**And** the page scrolls appropriately

**Prerequisites:** Story 3.3 (conversation UI must exist)

**Technical Notes:**
- Use Tailwind CSS utilities for responsive design
- Test on real devices (iOS Safari, Android Chrome)
- Add loading skeletons for better perceived performance
- Implement smooth scroll behavior with react-scroll or native CSS
- Use react-textarea-autosize for auto-expanding input
- Reference: PRD Section 7.6 (Accessibility NFR-6.1 to NFR-6.5)

---

### Story 3.12: Integration Testing & Bug Fixes

**As a** developer,
**I want** comprehensive integration tests for the conversation system,
**So that** we ensure all features work together correctly.

**Acceptance Criteria:**

**Given** the conversation features are implemented
**When** integration tests run
**Then** the following scenarios are tested:

1. **Full conversation flow:**
   - User logs in → Starts conversation → Sends message → Receives response → Sends follow-up → Response maintains context → Conversation saved

2. **Multi-conversation management:**
   - Create multiple conversations → Switch between them → Each maintains separate context

3. **Search and filter:**
   - Create conversations with distinct topics → Search finds correct conversations → Filter by status works

4. **Sharing:**
   - Share conversation → Access shared link → Read-only view works → Disable sharing invalidates link

5. **Archive/Delete:**
   - Archive conversation → Verify removed from active list → Unarchive restores → Delete permanently removes

6. **Export:**
   - Export conversation as PDF → File contains all messages and citations
   - Export as text → Format is correct

**And** all tests pass in CI/CD pipeline

**And** any bugs found during testing are fixed before epic completion

**Prerequisites:** All previous stories in Epic 3

**Technical Notes:**
- Use pytest for backend integration tests
- Use React Testing Library + Playwright for frontend E2E tests
- Test database transactions and rollback scenarios
- Verify conversation context assembly with multiple turns
- Load test: 10 concurrent users with active conversations
- Document test coverage in `/docs/testing/epic-3-integration-tests.md`

---

## Epic Completion Criteria

- [ ] Multi-turn conversations maintain context up to 10 messages
- [ ] All conversations auto-save immediately
- [ ] Conversation list sidebar displays all user conversations
- [ ] Search finds conversations by title or content
- [ ] Conversations can be shared via link (read-only)
- [ ] Conversations can be archived and restored
- [ ] Conversations can be deleted (with confirmation)
- [ ] Conversations can be exported as PDF or text
- [ ] All 7 knowledge domains return quality responses
- [ ] UI is polished and responsive on all devices
- [ ] Integration tests pass for all conversation features

---

## Definition of Done

- All 12 stories completed and acceptance criteria met
- Integration tests cover key conversation workflows
- UI tested on desktop, tablet, and mobile devices
- All 7 domains validated with test queries
- Performance benchmarks met (conversation load <2s)
- No critical bugs in conversation management
- Export functionality works for various conversation lengths
- User documentation updated with conversation features

---

## Dependencies & Risks

**Dependencies:**
- Epic 2 completion (AI coach must be working)
- Database schema from Epic 1

**Risks:**
- Context management complexity with long conversations (Mitigation: Limit to 10 messages, implement summarization later)
- Search performance with many conversations (Mitigation: Database indexing, pagination)
- Export generation timeout for very long conversations (Mitigation: Async generation, S3 storage)
- Shared links security concerns (Mitigation: Require login, optional expiration)

**Next Epic:** Epic 4 - Analytics, Feedback & Production Polish
