/**
 * Unit tests for Story 3.3: formatTimestamp utility
 * AC #2: Timestamp formatting (relative for <7 days, absolute for >=7 days)
 */

import { describe, it, expect } from 'vitest';
import { formatTimestamp } from '../formatTimestamp';

describe('formatTimestamp', () => {
  it('returns relative time for dates less than 7 days old', () => {
    // Arrange
    const now = new Date();
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
    const threeDaysAgo = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);

    // Act
    const result1 = formatTimestamp(twoHoursAgo);
    const result2 = formatTimestamp(threeDaysAgo);

    // Assert
    expect(result1).toContain('ago'); // "2 hours ago"
    expect(result2).toContain('ago'); // "3 days ago"
  });

  it('returns absolute date for dates 7 days or older', () => {
    // Arrange
    const sevenDaysAgo = new Date('2025-11-07T10:00:00Z');
    const oneMonthAgo = new Date('2025-10-14T10:00:00Z');

    // Act (assuming current date is around Nov 14, 2025)
    const result1 = formatTimestamp(sevenDaysAgo);
    const result2 = formatTimestamp(oneMonthAgo);

    // Assert
    expect(result1).toMatch(/Nov \d+, \d{4}/); // "Nov 7, 2025"
    expect(result2).toMatch(/Oct \d+, \d{4}/); // "Oct 14, 2025"
  });

  it('handles string dates', () => {
    // Arrange
    const dateString = '2025-11-14T10:30:00Z';

    // Act
    const result = formatTimestamp(dateString);

    // Assert
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
  });

  it('handles Date objects', () => {
    // Arrange
    const dateObj = new Date('2025-11-14T10:30:00Z');

    // Act
    const result = formatTimestamp(dateObj);

    // Assert
    expect(result).toBeTruthy();
    expect(typeof result).toBe('string');
  });
});
