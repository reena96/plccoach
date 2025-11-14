/**
 * Story 3.3: Conversation List Sidebar
 * Main conversation list component with pagination and mobile support
 */

import { useEffect, useRef, useState } from 'react';
import { useConversations, type Conversation } from '../../hooks/useConversations';
import { formatTimestamp } from '../../utils/formatTimestamp';

interface ConversationListProps {
  userId: string;
  activeConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation?: () => void;
}

/**
 * Conversation List Sidebar Component
 *
 * AC #1: Display sidebar with conversations ordered by updated_at DESC
 * AC #2: Show title, preview (60 chars), and timestamp for each conversation
 * AC #3: Highlight active conversation and handle selection
 * AC #4: Implement pagination with infinite scroll
 * AC #5: Mobile responsive with hamburger menu toggle
 */
export function ConversationList({
  userId,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
}: ConversationListProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [searchQuery, setSearchQuery] = useState(''); // Story 3.5: Search input
  const [debouncedSearch, setDebouncedSearch] = useState(''); // Story 3.5: Debounced search
  const observerTarget = useRef<HTMLDivElement>(null);

  // Story 3.5: Debounce search input (300ms delay)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Fetch conversations with infinite scroll and search filtering
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useConversations(userId, 20, debouncedSearch);

  // Detect mobile breakpoint (768px)
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  // Handle conversation selection (close sidebar on mobile)
  const handleSelectConversation = (conversationId: string) => {
    onSelectConversation(conversationId);
    if (isMobile) {
      setIsSidebarOpen(false);
    }
  };

  // Flatten paginated data
  const conversations =
    data?.pages.flatMap((page) => page.conversations) ?? [];

  return (
    <>
      {/* Mobile hamburger button */}
      {isMobile && (
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow-md md:hidden"
          aria-label="Toggle conversation list"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isSidebarOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>
      )}

      {/* Sidebar overlay (mobile only) */}
      {isMobile && isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-full bg-white border-r border-gray-200 z-40 transition-transform
          ${isMobile ? 'w-full' : 'w-80'}
          ${isMobile && !isSidebarOpen ? '-translate-x-full' : 'translate-x-0'}
          md:translate-x-0
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header with New Conversation button */}
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={onNewConversation}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              New Conversation
            </button>

            {/* Story 3.5: Search Box */}
            <div className="mt-3 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full px-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                aria-label="Search conversations"
              />
              {/* Search icon */}
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              {/* Clear button (Story 3.5 AC #3) */}
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label="Clear search"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading && (
              <div className="p-4 text-center text-gray-500">
                Loading conversations...
              </div>
            )}

            {isError && (
              <div className="p-4 text-center text-red-500">
                Failed to load conversations
              </div>
            )}

            {!isLoading && conversations.length === 0 && (
              <div className="p-4 text-center text-gray-500">
                {debouncedSearch ? (
                  // Story 3.5: Search returned no results
                  <>
                    <p>No conversations found for "{debouncedSearch}"</p>
                    <button
                      onClick={() => setSearchQuery('')}
                      className="mt-2 text-sm text-blue-600 hover:underline"
                    >
                      Clear search
                    </button>
                  </>
                ) : (
                  'No conversations yet'
                )}
              </div>
            )}

            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                isActive={conversation.id === activeConversationId}
                onClick={() => handleSelectConversation(conversation.id)}
              />
            ))}

            {/* Infinite scroll trigger */}
            {hasNextPage && (
              <div ref={observerTarget} className="p-4 text-center">
                {isFetchingNextPage ? (
                  <div className="text-gray-500">Loading more...</div>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

/**
 * Individual conversation item component
 *
 * AC #2: Display title, preview (60 chars), and timestamp
 * AC #3: Highlight active conversation
 */
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
}

function ConversationItem({
  conversation,
  isActive,
  onClick,
}: ConversationItemProps) {
  const [showMenu, setShowMenu] = useState(false);

  const handleMenuClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowMenu(!showMenu);
  };

  const handleAction = (e: React.MouseEvent, action: string) => {
    e.stopPropagation();
    setShowMenu(false);

    // TODO: Implement actions (Story 3.11)
    console.log(`Action: ${action} for conversation ${conversation.id}`);
    alert(`${action} feature coming soon in Story 3.11!`);
  };

  return (
    <div className="relative">
      <button
        onClick={onClick}
        className={`
          w-full p-4 text-left border-b border-gray-100 hover:bg-gray-50 transition-colors
          ${isActive ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''}
        `}
      >
        <h3 className="font-medium text-gray-900 truncate mb-1">
          {conversation.title}
        </h3>
        <p className="text-sm text-gray-600 truncate mb-2">
          {conversation.first_message_preview || 'No preview available'}
        </p>
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{formatTimestamp(conversation.updated_at)}</span>
          <span>{conversation.message_count} messages</span>
        </div>
      </button>

      {/* Story 3.11: Three-dot menu for actions */}
      <button
        onClick={handleMenuClick}
        className="absolute top-2 right-2 p-2 hover:bg-gray-200 rounded-full transition-colors"
        aria-label="Conversation actions"
      >
        <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {showMenu && (
        <>
          {/* Backdrop to close menu */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowMenu(false)}
          />

          {/* Menu items */}
          <div className="absolute right-2 top-12 z-20 bg-white border border-gray-200 rounded-md shadow-lg py-1 w-48">
            <button
              onClick={(e) => handleAction(e, 'Export')}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export (Story 3.9)
            </button>

            <button
              onClick={(e) => handleAction(e, 'Share')}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share Link (Story 3.6)
            </button>

            <button
              onClick={(e) => handleAction(e, 'Archive')}
              className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
              </svg>
              Archive (Story 3.7)
            </button>

            <hr className="my-1" />

            <button
              onClick={(e) => handleAction(e, 'Delete')}
              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete (Story 3.8)
            </button>
          </div>
        </>
      )}
    </div>
  );
}
