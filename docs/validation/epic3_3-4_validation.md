# Story 3.4: New Conversation & Clear Context - Validation Guide

**Story:** 3.4 - New Conversation & Clear Context
**Epic:** 3 - Conversations & History
**Date:** 2025-11-14
**Status:** Ready for Validation

---

## 30-Second Quick Test

```bash
# 1. Start frontend dev server
cd frontend && npm run dev

# 2. Navigate to http://localhost:5173/chat

# 3. Click "New Conversation" button in sidebar
# 4. Verify chat clears and welcome message appears
# 5. Click "New Conversation" again - verify same behavior
```

**Expected:** Chat clears, welcome message displays with example questions

---

## Manual Validation Steps

### AC #1: New Conversation Button

**Test:** Click "New Conversation" clears chat and shows welcome

1. Navigate to `/chat` page
2. Verify "New Conversation" button visible at top of sidebar (blue button with + icon)
3. Click "New Conversation"
4. Verify:
   - Chat area clears (if any messages were displayed)
   - Welcome message appears: "Welcome to your PLC Coach"
   - 4 example question cards displayed
   - conversation_id state reset to null (check React DevTools)
   - isNewConversation state set to true

**Expected:**
- Button functional
- Chat area clears
- Welcome message with example questions displayed
- State properly reset

---

### AC #2: New Conversation from Past Conversation

**Test:** Can navigate between conversations

1. Click "New Conversation"
2. Verify welcome message shown
3. Click on a past conversation in sidebar (if any exist)
4. Verify conversation loads (though messages won't display without Epic 2 integration)
5. Click "New Conversation" again
6. Verify welcome message appears again
7. Click back to previous conversation
8. Verify can navigate freely

**Expected:**
- Can start new conversation from any state
- Can navigate back to previous conversations
- Sidebar highlighting updates correctly
- No errors or broken functionality

---

### AC #3: Empty Conversation Cleanup

**Test:** Empty conversations filtered from sidebar

**Note:** This is handled by Story 3.3's sidebar endpoint - it already filters conversations with message_count=0

1. Click "New Conversation" multiple times
2. Verify sidebar doesn't fill with empty conversations
3. Check network tab - verify GET /api/conversations response only includes conversations with messages

**Expected:**
- Sidebar only shows conversations with at least 1 message
- Empty conversations (no messages sent) not visible in list
- Backend endpoint filters correctly (message_count > 0)

---

## Component Integration Test

### ConversationList Integration

**Test:** Verify Chat page properly integrates ConversationList

1. Check props passed to ConversationList:
   - `userId={user.id}` - user ID from auth context
   - `activeConversationId` - currently selected conversation
   - `onSelectConversation={handleSelectConversation}` - handler provided
   - `onNewConversation={handleNewConversation}` - handler provided

2. Verify handlers work:
   - Click conversation in sidebar → `handleSelectConversation` called
   - Click "New Conversation" → `handleNewConversation` called
   - State updates correctly

**Expected:**
- All props correctly passed
- Handlers trigger state updates
- Component integration seamless

---

## State Management Test

**Test:** Verify conversation state managed correctly

**Using React DevTools:**

1. **Initial State:**
   - `activeConversationId`: null
   - `messages`: []
   - `isNewConversation`: true

2. **After clicking "New Conversation":**
   - `activeConversationId`: null
   - `messages`: []
   - `isNewConversation`: true

3. **After selecting conversation:**
   - `activeConversationId`: "<conversation-id>"
   - `isNewConversation`: false
   - `messages`: [] (will populate when Epic 2 integrated)

**Expected:**
- State transitions correctly
- No stale state or memory leaks
- Clean resets on new conversation

---

## Edge Cases & Error Handling

### Edge Case 1: Rapid Clicking

1. Click "New Conversation" button 10 times rapidly
2. Verify no errors
3. Verify welcome message still displays correctly
4. Verify state stable

**Expected:** No errors, state remains consistent

### Edge Case 2: No User Logged In

1. Log out or access without authentication
2. Verify redirect to login or appropriate message

**Expected:** Auth guard prevents access or shows message

### Edge Case 3: Sidebar Not Loaded Yet

1. Slow network simulation
2. Verify loading states handled gracefully

**Expected:** No crashes, appropriate loading indicators

---

## Acceptance Criteria Checklist

- [ ] **AC #1:** "New Conversation" button clears chat area
- [ ] **AC #1:** Welcome message and example questions appear
- [ ] **AC #1:** conversation_id reset to null (lazy creation)
- [ ] **AC #1:** Previous conversations remain in sidebar
- [ ] **AC #2:** Can navigate from new conversation to past conversation
- [ ] **AC #2:** Can navigate from past conversation to new conversation
- [ ] **AC #3:** Empty conversations not shown in sidebar
- [ ] **AC #3:** Sidebar filtering works correctly
- [ ] **Integration:** ConversationList properly integrated
- [ ] **Integration:** State management working correctly

---

## Known Limitations / Technical Debt

1. **Epic 2 Integration Pending:**
   - Message input disabled (placeholder)
   - Actual chat messaging not connected
   - Message loading from conversations not implemented
   - **Will be completed:** When Epic 2 and Epic 3 branches merge

2. **Database Record Creation:**
   - No database interaction on button click (intentional - lazy creation)
   - Conversation record created when first message sent (Epic 2 logic)
   - **Status:** Working as designed

3. **Testing:**
   - No automated tests (test framework not configured)
   - Manual validation required
   - **Defer to:** Story 3.12 (Integration Testing)

---

## Rollback Plan

**If issues found:**

1. **Frontend Issues:**
   - Revert Chat.tsx to placeholder version:
   ```bash
   git checkout HEAD~1 -- frontend/src/pages/Chat.tsx
   ```

2. **Integration Issues:**
   - ConversationList will still work independently
   - Chat page will show error but app won't crash

**Full Rollback:**
```bash
git revert <commit-hash>  # Revert Story 3.4 commit
```

---

## Files Modified

**Created:**
- docs/validation/epic3_3-4_validation.md

**Modified:**
- frontend/src/pages/Chat.tsx (complete rewrite - integrated ConversationList)
- docs/scrum/stories/3-4-new-conversation-clear-context.md (tasks marked complete)
- docs/scrum/sprint-status.yaml (status updated)

---

## Next Steps

After validation passes:
1. Mark story as "review" in sprint-status.yaml
2. Continue to Story 3.5: Conversation Search & Filtering
3. Eventually: Merge Epic 2 and Epic 3 branches for full functionality
