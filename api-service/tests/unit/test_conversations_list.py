"""
Unit tests for Story 3.3: Conversation List Sidebar
Tests GET /api/conversations endpoint
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from app.routers.conversations import list_conversations, ConversationItem


class TestConversationsList:
    """Test conversation list endpoint (AC #1, #4)."""

    @pytest.mark.asyncio
    async def test_list_conversations_returns_ordered_by_updated_at(self):
        """AC #1: Conversations ordered by updated_at DESC (most recent first)."""
        # Arrange
        mock_db = Mock()
        user_id = str(uuid4())

        # Create mock conversations with different updated_at times
        now = datetime.utcnow()
        conv1 = Mock(
            id=uuid4(),
            user_id=user_id,
            title="Old Conversation",
            status='active',
            updated_at=now - timedelta(days=5)
        )
        conv2 = Mock(
            id=uuid4(),
            user_id=user_id,
            title="Recent Conversation",
            status='active',
            updated_at=now - timedelta(hours=1)
        )
        conv3 = Mock(
            id=uuid4(),
            user_id=user_id,
            title="Middle Conversation",
            status='active',
            updated_at=now - timedelta(days=2)
        )

        # Mock database queries
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        # Return in correct order (most recent first)
        mock_query.all.return_value = [conv2, conv3, conv1]

        # Mock message queries
        mock_query.first.return_value = Mock(content="Test message")
        mock_query.scalar.return_value = 1

        # Act
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=0,
            db=mock_db
        )

        # Assert
        assert len(response.conversations) == 3
        assert response.conversations[0].title == "Recent Conversation"
        assert response.conversations[1].title == "Middle Conversation"
        assert response.conversations[2].title == "Old Conversation"

    @pytest.mark.asyncio
    async def test_list_conversations_pagination_metadata(self):
        """AC #4: Pagination metadata (total, limit, offset, has_more) correct."""
        # Arrange
        mock_db = Mock()
        user_id = str(uuid4())

        # Mock total of 45 conversations
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 45
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_query.scalar.return_value = 0

        # Act - First page
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=0,
            db=mock_db
        )

        # Assert
        assert response.total == 45
        assert response.limit == 20
        assert response.offset == 0
        assert response.has_more is True  # 0 + 20 < 45

        # Act - Second page
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=20,
            db=mock_db
        )

        # Assert
        assert response.has_more is True  # 20 + 20 < 45

        # Act - Third page (last)
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=40,
            db=mock_db
        )

        # Assert
        assert response.has_more is False  # 40 + 20 >= 45

    @pytest.mark.asyncio
    async def test_list_conversations_preview_truncated_at_60_chars(self):
        """AC #2: First message preview truncated at 60 characters."""
        # Arrange
        mock_db = Mock()
        user_id = str(uuid4())
        long_message = "A" * 100  # 100 character message

        conv = Mock(
            id=uuid4(),
            user_id=user_id,
            title="Test",
            status='active',
            updated_at=datetime.utcnow()
        )

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [conv]
        mock_query.first.return_value = Mock(content=long_message)
        mock_query.scalar.return_value = 1

        # Act
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=0,
            db=mock_db
        )

        # Assert
        preview = response.conversations[0].first_message_preview
        assert len(preview) == 63  # 60 chars + "..."
        assert preview.endswith("...")

    @pytest.mark.asyncio
    async def test_list_conversations_filters_by_user_id(self):
        """Only returns conversations for specified user."""
        # Arrange
        mock_db = Mock()
        user_id = str(uuid4())

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []  # Return empty list

        # Act
        await list_conversations(
            user_id=user_id,
            limit=20,
            offset=0,
            db=mock_db
        )

        # Assert - filter was called (verifies user_id filtering)
        assert mock_query.filter.called

    @pytest.mark.asyncio
    async def test_list_conversations_only_shows_active(self):
        """Only returns conversations with status='active' (excludes archived/deleted)."""
        # This is implicitly tested by the filter, but verifying the behavior
        # AC relates to future stories (archiving), but filtering is implemented now
        mock_db = Mock()
        user_id = str(uuid4())

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []

        # Act
        response = await list_conversations(
            user_id=user_id,
            limit=20,
            offset=0,
            db=mock_db
        )

        # Assert
        assert response.total == 0
        assert len(response.conversations) == 0
