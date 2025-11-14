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
  return (
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
  );
}
