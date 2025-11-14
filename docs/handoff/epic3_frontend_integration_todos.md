# Epic 3: Frontend Integration Todos - Session 4

**Current Status:** Backend 100% complete, Frontend ~60% complete
**Branch:** epic-3-conversations-history
**Estimated Effort:** 20-30k tokens (~30-45 minutes)
**Priority:** High - Required for fully functional Epic 3

---

## 🎯 Goal

Connect the three-dot menu actions to backend APIs and make all Epic 3 features fully testable through the UI.

---

## ✅ Already Complete

### Backend APIs (All Working)
- ✅ GET /api/conversations?search={query} - Search
- ✅ POST /api/conversations/{id}/share - Generate share link
- ✅ GET /api/conversations/shared/{token} - View shared
- ✅ DELETE /api/conversations/{id}/share - Disable share
- ✅ PATCH /api/conversations/{id}/archive - Archive
- ✅ PATCH /api/conversations/{id}/unarchive - Unarchive
- ✅ DELETE /api/conversations/{id} - Delete
- ✅ GET /api/conversations/{id}/export - Export markdown

### Frontend UI (Placeholders)
- ✅ Three-dot menu visible on conversations
- ✅ Menu shows Export/Share/Archive/Delete options
- ✅ Menu opens/closes correctly
- ✅ Search UI with debouncing

---

## 📋 TODO: Frontend Integration

### Story 3.9: Export - Connect Frontend to Backend

**Current State:** Menu item shows alert, doesn't actually export

**Todo:**
```typescript
// frontend/src/components/conversation/ConversationList.tsx

// 1. Add export handler function
const handleExport = async (conversationId: string) => {
  try {
    // Call export API
    const response = await axios.get(
      `/api/conversations/${conversationId}/export`,
      {
        params: {
          user_id: userId,
          format: 'markdown'
        },
        responseType: 'blob'
      }
    );

    // Trigger download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `conversation_${conversationId}.md`);
    document.body.appendChild(link);
    link.click();
    link.remove();

    // Show success message
    alert('Conversation exported successfully!');
  } catch (error) {
    console.error('Export failed:', error);
    alert('Failed to export conversation');
  }
};

// 2. Update Export button onClick
onClick={(e) => handleExport(conversation.id)}
```

**Files to Modify:**
- `frontend/src/components/conversation/ConversationList.tsx`

**Acceptance Criteria:**
- [ ] Clicking Export downloads .md file
- [ ] Filename includes conversation title/date
- [ ] Shows success/error message
- [ ] Works on desktop and mobile

---

### Story 3.6: Share - Add Share Modal

**Current State:** Menu item shows alert, doesn't generate share link

**Todo:**
```typescript
// frontend/src/components/conversation/ShareModal.tsx (NEW FILE)

interface ShareModalProps {
  conversationId: string;
  userId: string;
  onClose: () => void;
}

export function ShareModal({ conversationId, userId, onClose }: ShareModalProps) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [expiresIn, setExpiresIn] = useState<number>(30); // days
  const [loading, setLoading] = useState(false);

  const generateShareLink = async () => {
    setLoading(true);
    try {
      const response = await axios.post(
        `/api/conversations/${conversationId}/share`,
        { expires_in_days: expiresIn },
        { params: { user_id: userId } }
      );
      setShareUrl(response.data.share_url);
    } catch (error) {
      alert('Failed to generate share link');
    }
    setLoading(false);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareUrl!);
    alert('Link copied to clipboard!');
  };

  const disableSharing = async () => {
    try {
      await axios.delete(
        `/api/conversations/${conversationId}/share`,
        { params: { user_id: userId } }
      );
      alert('Sharing disabled');
      onClose();
    } catch (error) {
      alert('Failed to disable sharing');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Share Conversation</h2>

        {!shareUrl ? (
          <>
            <p className="text-gray-600 mb-4">
              Generate a shareable link that others can use to view this conversation.
            </p>

            <label className="block mb-4">
              <span className="text-sm font-medium">Expires in:</span>
              <select
                value={expiresIn}
                onChange={(e) => setExpiresIn(Number(e.target.value))}
                className="mt-1 block w-full border rounded px-3 py-2"
              >
                <option value={7}>7 days</option>
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
                <option value={365}>1 year</option>
              </select>
            </label>

            <button
              onClick={generateShareLink}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
            >
              {loading ? 'Generating...' : 'Generate Share Link'}
            </button>
          </>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-2">Share this link:</p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 border rounded px-3 py-2 text-sm"
              />
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
              >
                Copy
              </button>
            </div>

            <button
              onClick={disableSharing}
              className="w-full text-red-600 hover:bg-red-50 py-2 rounded"
            >
              Disable Sharing
            </button>
          </>
        )}

        <button
          onClick={onClose}
          className="w-full mt-4 text-gray-600 hover:bg-gray-100 py-2 rounded"
        >
          Close
        </button>
      </div>
    </div>
  );
}
```

**Then update ConversationList.tsx:**
```typescript
// Add state for modal
const [shareModalOpen, setShareModalOpen] = useState(false);
const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

// Update Share button
onClick={(e) => {
  e.stopPropagation();
  setSelectedConversationId(conversation.id);
  setShareModalOpen(true);
  setShowMenu(false);
}}

// Render modal
{shareModalOpen && selectedConversationId && (
  <ShareModal
    conversationId={selectedConversationId}
    userId={userId}
    onClose={() => {
      setShareModalOpen(false);
      setSelectedConversationId(null);
    }}
  />
)}
```

**Files to Create:**
- `frontend/src/components/conversation/ShareModal.tsx` (NEW)

**Files to Modify:**
- `frontend/src/components/conversation/ConversationList.tsx`

**Acceptance Criteria:**
- [ ] Clicking Share opens modal
- [ ] Can select expiration period
- [ ] Generate button creates share link
- [ ] Copy button copies to clipboard
- [ ] Disable button invalidates link
- [ ] Modal closes properly

---

### Story 3.7: Archive - Connect to API

**Current State:** Menu item shows alert, doesn't archive

**Todo:**
```typescript
// frontend/src/components/conversation/ConversationList.tsx

// 1. Add archive handler
const handleArchive = async (conversationId: string) => {
  try {
    await axios.patch(
      `/api/conversations/${conversationId}/archive`,
      {},
      { params: { user_id: userId } }
    );

    // Refetch conversations to update list
    refetch();

    alert('Conversation archived');
  } catch (error) {
    console.error('Archive failed:', error);
    alert('Failed to archive conversation');
  }
};

// 2. Update Archive button onClick
onClick={(e) => handleArchive(conversation.id)}

// 3. Add refetch from React Query
const { data, refetch } = useConversations(userId, 20, debouncedSearch);
```

**Optional Enhancement:**
Add "Show Archived" toggle to view archived conversations:
```typescript
const [showArchived, setShowArchived] = useState(false);

// Add toggle button in sidebar header
<button
  onClick={() => setShowArchived(!showArchived)}
  className="text-sm text-gray-600 hover:text-gray-900"
>
  {showArchived ? 'Hide Archived' : 'Show Archived'}
</button>

// Filter conversations based on toggle
// (Note: Backend needs ?status=archived parameter support)
```

**Files to Modify:**
- `frontend/src/components/conversation/ConversationList.tsx`
- `frontend/src/hooks/useConversations.ts` (add refetch support)

**Acceptance Criteria:**
- [ ] Clicking Archive removes conversation from list
- [ ] Conversation still exists in database (status='archived')
- [ ] Shows success/error message
- [ ] List refreshes automatically

---

### Story 3.8: Delete - Add Confirmation Dialog

**Current State:** Menu item shows alert, doesn't delete

**Todo:**
```typescript
// frontend/src/components/conversation/DeleteConfirmModal.tsx (NEW FILE)

interface DeleteConfirmModalProps {
  conversationTitle: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirmModal({
  conversationTitle,
  onConfirm,
  onCancel
}: DeleteConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold text-red-600 mb-4">Delete Conversation?</h2>

        <p className="text-gray-700 mb-2">
          Are you sure you want to delete:
        </p>
        <p className="font-medium mb-4">"{conversationTitle}"</p>

        <p className="text-sm text-gray-600 mb-6">
          This action cannot be undone. All messages will be permanently deleted.
        </p>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Then update ConversationList.tsx:**
```typescript
// Add state for delete confirmation
const [deleteModalOpen, setDeleteModalOpen] = useState(false);
const [conversationToDelete, setConversationToDelete] = useState<Conversation | null>(null);

// Add delete handler
const handleDelete = async () => {
  if (!conversationToDelete) return;

  try {
    await axios.delete(
      `/api/conversations/${conversationToDelete.id}`,
      { params: { user_id: userId } }
    );

    // Refetch conversations
    refetch();

    // Close modal
    setDeleteModalOpen(false);
    setConversationToDelete(null);

    alert('Conversation deleted');
  } catch (error) {
    console.error('Delete failed:', error);
    alert('Failed to delete conversation');
  }
};

// Update Delete button onClick
onClick={(e) => {
  e.stopPropagation();
  setConversationToDelete(conversation);
  setDeleteModalOpen(true);
  setShowMenu(false);
}}

// Render modal
{deleteModalOpen && conversationToDelete && (
  <DeleteConfirmModal
    conversationTitle={conversationToDelete.title}
    onConfirm={handleDelete}
    onCancel={() => {
      setDeleteModalOpen(false);
      setConversationToDelete(null);
    }}
  />
)}
```

**Files to Create:**
- `frontend/src/components/conversation/DeleteConfirmModal.tsx` (NEW)

**Files to Modify:**
- `frontend/src/components/conversation/ConversationList.tsx`

**Acceptance Criteria:**
- [ ] Clicking Delete opens confirmation modal
- [ ] Modal shows conversation title
- [ ] Cancel closes modal without deleting
- [ ] Confirm deletes conversation
- [ ] Conversation removed from list
- [ ] Shows success/error message

---

## 📁 Files Summary

### Files to Create (3 new files)
1. `frontend/src/components/conversation/ShareModal.tsx`
2. `frontend/src/components/conversation/DeleteConfirmModal.tsx`
3. (Optional) `frontend/src/components/conversation/ArchiveToggle.tsx`

### Files to Modify (2 files)
1. `frontend/src/components/conversation/ConversationList.tsx` - Main integration
2. `frontend/src/hooks/useConversations.ts` - Add refetch, status filter support

---

## ✅ Testing Checklist

After implementation, test each feature:

### Export
- [ ] Click Export → file downloads
- [ ] Filename includes title and date
- [ ] File contains all messages
- [ ] Citations preserved
- [ ] Works on mobile

### Share
- [ ] Click Share → modal opens
- [ ] Generate Link → URL created
- [ ] Copy → clipboard works
- [ ] Open share URL → conversation visible
- [ ] Disable → link becomes invalid (404)

### Archive
- [ ] Click Archive → conversation disappears
- [ ] Database: status = 'archived'
- [ ] (Optional) Show Archived → conversation reappears
- [ ] Unarchive → returns to main list

### Delete
- [ ] Click Delete → confirmation appears
- [ ] Cancel → nothing happens
- [ ] Confirm → conversation deleted
- [ ] Database: conversation + messages gone
- [ ] List refreshes automatically

---

## 🎯 Success Criteria

**Epic 3 is complete when:**
- [x] All backend APIs functional
- [ ] All frontend actions connected to APIs
- [ ] All modals/confirmations implemented
- [ ] Manual testing passes all scenarios
- [ ] No console errors
- [ ] Responsive on mobile
- [ ] Basic error handling in place

---

## 🚀 Implementation Order (Recommended)

1. **Start with Delete** (15 min, ~5k tokens)
   - Simplest: just confirmation + API call
   - Most critical for safety

2. **Then Export** (10 min, ~3k tokens)
   - Simple blob download
   - No modal needed

3. **Then Archive** (10 min, ~4k tokens)
   - Direct API call + refetch
   - Optional: Show Archived toggle

4. **Finally Share** (20 min, ~10k tokens)
   - Most complex: modal + state management
   - Multiple API calls (generate, view, disable)

**Total Estimated:** ~40 min, 22k tokens

---

## 🔧 Helpful Code Snippets

### Axios with Blob Response (for Export)
```typescript
const response = await axios.get(url, {
  responseType: 'blob'
});
```

### Trigger File Download
```typescript
const url = window.URL.createObjectURL(new Blob([response.data]));
const link = document.createElement('a');
link.href = url;
link.setAttribute('download', filename);
document.body.appendChild(link);
link.click();
link.remove();
```

### Copy to Clipboard
```typescript
navigator.clipboard.writeText(text);
```

### Refetch in React Query
```typescript
const { data, refetch } = useConversations(...);
// Later:
await refetch();
```

---

## 📝 Notes

- All backend APIs are already tested and working
- Frontend just needs to call them with correct parameters
- Error handling should show user-friendly messages
- Consider adding loading states for better UX
- Test with real conversations containing messages

---

## 🎊 After Completion

Once all todos are complete:

1. Run full manual test suite (use validation guides)
2. Update handoff document as "FULLY COMPLETE"
3. Mark Epic 3 as production-ready
4. Create PR for review
5. Celebrate! 🎉

---

**Saved:** 2025-11-14
**Ready for:** Next development session
**Estimated Effort:** 22k tokens (~40 minutes)
