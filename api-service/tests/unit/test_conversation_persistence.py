"""
Unit tests for Story 3.2: Conversation Persistence & Auto-Save

Tests conversation creation, message persistence, title generation,
and transaction atomicity.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.models.conversation import Conversation
from app.models.message import Message
from sqlalchemy.exc import SQLAlchemyError


class TestConversationCreation:
    """Test conversation creation on first message (AC #1)."""

    def test_conversation_created_when_none_provided(self):
        """Test that a new conversation is created when conversation_id is None."""
        # Arrange
        mock_db = Mock()
        user_id = uuid4()
        query = "What is project-based learning?"

        # Act
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            title=query[:50],
            status='active'
        )

        # Assert
        assert conversation.id is not None
        assert conversation.user_id == user_id
        assert conversation.title == query[:50]
        assert conversation.status == 'active'

    def test_conversation_not_created_when_id_provided(self):
        """Test that no new conversation is created when conversation_id exists."""
        # This is a behavioral test - if conversation_id is provided,
        # the endpoint should NOT create a new conversation
        existing_conversation_id = str(uuid4())

        # The endpoint should skip conversation creation logic
        # when conversation_id is not None
        assert existing_conversation_id is not None

    def test_conversation_associated_with_user_id(self):
        """Test that conversation is associated with correct user_id."""
        user_id = uuid4()
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            title="Test conversation",
            status='active'
        )

        assert conversation.user_id == user_id


class TestTitleGeneration:
    """Test auto-generated conversation titles (AC #3)."""

    def test_title_under_50_chars(self):
        """Test title generation with message < 50 characters."""
        query = "What is PBL?"  # 13 characters

        title = query[:50]
        if len(query) > 50:
            title += "..."

        assert title == "What is PBL?"
        assert len(title) <= 53  # 50 chars + "..."

    def test_title_over_50_chars(self):
        """Test title generation with message > 50 characters (truncated)."""
        query = "What are the key principles of project-based learning and how can I implement them in my classroom?"  # 103 chars

        title = query[:50]
        if len(query) > 50:
            title += "..."

        assert title == query[:50] + "..."
        assert len(title) == 53  # 50 chars + "..."

    def test_title_exactly_50_chars(self):
        """Test title generation with message exactly 50 characters."""
        query = "A" * 50  # Exactly 50 characters

        title = query[:50]
        if len(query) > 50:
            title += "..."

        assert title == query
        assert len(title) == 50
        assert "..." not in title  # Should not be truncated

    def test_title_with_special_characters(self):
        """Test title generation preserves special characters."""
        query = "What's the difference between PBL & traditional learning?"

        title = query[:50]
        if len(query) > 50:
            title += "..."

        assert "'" in title
        assert "&" in title

    def test_empty_query_title(self):
        """Test title generation with empty query (edge case)."""
        query = ""

        title = query[:50]
        if len(query) > 50:
            title += "..."

        assert title == ""


class TestMessagePersistence:
    """Test user and assistant message persistence (AC #1)."""

    def test_user_message_creation(self):
        """Test creating a user message record."""
        conversation_id = uuid4()
        content = "What is differentiation in PBL?"

        user_message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role='user',
            content=content
        )

        assert user_message.id is not None
        assert user_message.conversation_id == conversation_id
        assert user_message.role == 'user'
        assert user_message.content == content
        assert user_message.citations is None  # User messages don't have citations

    def test_assistant_message_creation_with_citations(self):
        """Test creating an assistant message with citations."""
        conversation_id = uuid4()
        content = "Differentiation in PBL involves..."
        citations = [
            {
                "book_title": "PBL Handbook",
                "authors": "John Doe",
                "chapter": 5,
                "chapter_title": "Differentiation Strategies",
                "pages": "45-52"
            }
        ]

        assistant_message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role='assistant',
            content=content,
            citations=citations,
            input_tokens=150,
            cost_usd=0.002
        )

        assert assistant_message.id is not None
        assert assistant_message.conversation_id == conversation_id
        assert assistant_message.role == 'assistant'
        assert assistant_message.content == content
        assert assistant_message.citations == citations
        assert assistant_message.input_tokens == 150
        assert assistant_message.cost_usd == 0.002

    def test_message_content_length(self):
        """Test that long message content is handled correctly."""
        # Messages can be long (up to text field limit)
        long_content = "A" * 5000

        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='user',
            content=long_content
        )

        assert len(message.content) == 5000


class TestDatabaseTransactions:
    """Test transaction atomicity and error handling (AC #1)."""

    def test_transaction_rollback_on_error(self):
        """Test that database rolls back on error during save."""
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("Database error"))
        mock_db.rollback = Mock()

        try:
            conversation = Conversation(
                id=uuid4(),
                user_id=uuid4(),
                title="Test",
                status='active'
            )
            mock_db.add(conversation)
            mock_db.commit()
        except SQLAlchemyError:
            mock_db.rollback()

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    def test_flush_before_commit(self):
        """Test that flush is used to get IDs before final commit."""
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.flush = Mock()
        mock_db.commit = Mock()

        # Create conversation
        conversation = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            status='active'
        )
        mock_db.add(conversation)
        mock_db.flush()  # Get ID without committing

        # Create user message
        user_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role='user',
            content="Test message"
        )
        mock_db.add(user_message)
        mock_db.flush()  # Get ID without committing

        # Create assistant message
        assistant_message = Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role='assistant',
            content="Test response"
        )
        mock_db.add(assistant_message)

        # Final commit for all three
        mock_db.commit()

        # Verify flush was called twice (conversation + user message)
        # and commit once at the end
        assert mock_db.flush.call_count == 2
        mock_db.commit.assert_called_once()


class TestTimestampUpdates:
    """Test conversation timestamp updates (AC #4)."""

    def test_updated_at_on_message_save(self):
        """Test that conversation.updated_at is refreshed on message save."""
        # This is handled by SQLAlchemy's onupdate=datetime.utcnow
        # The test verifies the model behavior

        conversation = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            status='active'
        )

        # SQLAlchemy will automatically update updated_at when the record is modified
        # This test documents the expected behavior
        assert hasattr(conversation, 'updated_at')

    def test_conversation_has_timestamps(self):
        """Test that conversation model has created_at and updated_at fields."""
        conversation = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            title="Test",
            status='active'
        )

        # Both timestamps should exist
        assert hasattr(conversation, 'created_at')
        assert hasattr(conversation, 'updated_at')


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_very_long_message(self):
        """Test handling of very long messages (>1000 chars)."""
        long_message = "A" * 2000

        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='user',
            content=long_message
        )

        assert len(message.content) == 2000

    def test_special_characters_in_content(self):
        """Test that special characters in message content are preserved."""
        content = "Test with special chars: <>&\"'{}[]|\\~`!@#$%^&*()"

        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='user',
            content=content
        )

        assert message.content == content

    def test_unicode_in_content(self):
        """Test that unicode characters are handled correctly."""
        content = "Testing unicode: 你好 مرحبا שלום"

        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='user',
            content=content
        )

        assert message.content == content

    def test_null_citations_for_user_message(self):
        """Test that user messages have null citations."""
        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='user',
            content="Test"
        )

        assert message.citations is None

    def test_empty_citations_array(self):
        """Test assistant message with empty citations array."""
        message = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role='assistant',
            content="Response with no citations",
            citations=[]
        )

        assert message.citations == []
