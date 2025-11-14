/**
 * Story 3.4: New Conversation & Clear Context
 * Chat page with conversation management
 */

import { useState } from 'react';
import { ConversationList } from '../components/conversation/ConversationList';
import Layout from '../components/shared/Layout';
import { useAuth } from '../lib/auth';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export default function Chat() {
  const { user } = useAuth();
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isNewConversation, setIsNewConversation] = useState(true);

  /**
   * AC #1: Handle "New Conversation" button click
   * - Clear chat area
   * - Reset conversation state
   * - Show welcome message
   */
  const handleNewConversation = () => {
    // Clear messages
    setMessages([]);

    // Reset conversation ID (lazy creation - DB record created on first message)
    setActiveConversationId(null);

    // Mark as new conversation to show welcome message
    setIsNewConversation(true);
  };

  /**
   * AC #3: Handle conversation selection from sidebar
   * - Load conversation messages
   * - Set as active
   */
  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
    setIsNewConversation(false);

    // TODO: Load messages for selected conversation
    // This will be implemented when Epic 2 chat components are integrated
    setMessages([]);
  };

  if (!user) {
    return (
      <Layout>
        <div className="text-center text-gray-600">Please log in to access chat.</div>
      </Layout>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Conversation List Sidebar */}
      <ConversationList
        userId={user.id}
        activeConversationId={activeConversationId || undefined}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col bg-gray-50 md:ml-80">
        <Layout>
          <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-6">
            {/* Welcome Message (shown for new conversations) */}
            {isNewConversation && messages.length === 0 && (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center max-w-2xl">
                  <h1 className="text-3xl font-bold text-gray-900 mb-4">
                    Welcome to your PLC Coach
                  </h1>
                  <p className="text-lg text-gray-600 mb-8">
                    Ask me anything about Professional Learning Communities, collaborative teams,
                    assessment strategies, or instructional practices.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-2">
                        "What makes an effective common formative assessment?"
                      </h3>
                      <p className="text-sm text-gray-600">
                        Learn about assessment design
                      </p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-2">
                        "How do we establish productive team norms?"
                      </h3>
                      <p className="text-sm text-gray-600">
                        Build collaborative culture
                      </p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-2">
                        "What is Response to Intervention (RTI)?"
                      </h3>
                      <p className="text-sm text-gray-600">
                        Understand intervention systems
                      </p>
                    </div>
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer">
                      <h3 className="font-medium text-gray-900 mb-2">
                        "How do I implement project-based learning?"
                      </h3>
                      <p className="text-sm text-gray-600">
                        Explore instructional strategies
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Messages Display */}
            {messages.length > 0 && (
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-3xl px-4 py-3 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-white text-gray-900 shadow-sm'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Message Input Area (Placeholder - full implementation in Epic 2 integration) */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Ask your PLC Coach a question..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled
                />
                <button
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  disabled
                >
                  Send
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2 text-center">
                Full chat functionality will be integrated from Epic 2
              </p>
            </div>
          </div>
        </Layout>
      </main>
    </div>
  );
}
