/**
 * Story 3.3: Conversation List Sidebar
 * React Query hook for fetching and paginating conversations
 */

import { useInfiniteQuery } from '@tanstack/react-query';
import axios from 'axios';

export interface Conversation {
  id: string;
  title: string;
  first_message_preview: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Fetch conversations for infinite scroll pagination with optional search filtering.
 *
 * Story 3.3 AC #4: Implement pagination with infinite scroll using React Query
 * Story 3.5 AC #1: Add search parameter for filtering conversations
 *
 * @param userId - User ID to fetch conversations for
 * @param limit - Number of conversations per page (default: 20)
 * @param search - Optional search query for filtering (Story 3.5)
 * @returns useInfiniteQuery result with conversations data
 */
export function useConversations(userId: string, limit: number = 20, search?: string) {
  return useInfiniteQuery<ConversationsResponse>({
    queryKey: ['conversations', userId, limit, search],
    queryFn: async ({ pageParam = 0 }) => {
      const params: Record<string, any> = {
        user_id: userId,
        limit,
        offset: pageParam as number,
      };

      // Add search param if provided (Story 3.5)
      if (search && search.trim()) {
        params.search = search.trim();
      }

      const response = await axios.get<ConversationsResponse>(
        '/api/conversations',
        { params }
      );
      return response.data;
    },
    getNextPageParam: (lastPage) => {
      if (lastPage.has_more) {
        return lastPage.offset + lastPage.limit;
      }
      return undefined;
    },
    initialPageParam: 0,
    staleTime: 1000 * 60, // Consider data fresh for 1 minute
    refetchOnWindowFocus: true, // Refetch when user returns to window
  });
}
