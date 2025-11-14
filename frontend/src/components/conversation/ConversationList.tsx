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
  const observerTarget = useRef<HTMLDivElement>(null);

  // Fetch conversations with infinite scroll
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useConversations(userId);

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
                No conversations yet
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
