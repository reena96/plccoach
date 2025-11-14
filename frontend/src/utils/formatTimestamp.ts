/**
 * Story 3.3: Conversation List Sidebar
 * Utility for formatting timestamps with relative time for recent dates
 */

import { formatDistanceToNow, format, differenceInDays } from 'date-fns';

/**
 * Format timestamp for conversation list display.
 *
 * AC #2: Use relative time for recent conversations (<7 days),
 * absolute date for older conversations (>=7 days)
 *
 * @param date - Date to format
 * @returns Formatted string ("2 hours ago", "3 days ago", or "Nov 12, 2025")
 */
export function formatTimestamp(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const daysDiff = differenceInDays(new Date(), dateObj);

  if (daysDiff < 7) {
    // Relative time for recent conversations
    return formatDistanceToNow(dateObj, { addSuffix: true });
  } else {
    // Absolute date for older conversations
    return format(dateObj, 'MMM d, yyyy');
  }
}
