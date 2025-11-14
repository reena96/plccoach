"""
Unit tests for Story 3.1: Multi-Turn Conversation Context Management

Tests the get_conversation_context() method and conversation history formatting.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from app.services.generation_service import GenerationService
from app.models.conversation import Conversation
from app.models.message import Message


class TestGetConversationContext:
    """Test suite for get_conversation_context() method."""

    @pytest.fixture
    def generation_service(self, monkeypatch):
        """Create a GenerationService instance with mocked OpenAI client."""
        # Mock OpenAI client to avoid requiring API key
        mock_client = Mock()
        monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
        service = GenerationService()
        service.client = mock_client  # Replace with mock after initialization
        return service

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock()

    @pytest.fixture
    def sample_conversation_id(self):
        """Generate a sample conversation UUID."""
        return str(uuid4())

    @pytest.fixture
    def sample_user_id(self):
        """Generate a sample user UUID."""
        return str(uuid4())

    def test_empty_conversation_returns_empty_string(
        self, generation_service, mock_db_session, sample_conversation_id, sample_user_id
    ):
        """Test that empty conversation (0 messages) returns empty string."""
        # Arrange
        conv_uuid = UUID(sample_conversation_id)
        user_uuid = UUID(sample_user_id)

        # Mock conversation exists
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.id = conv_uuid
        mock_conversation.user_id = user_uuid

        # Mock query chain for conversation
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation

        # Mock empty messages
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        # Act
        result = generation_service.get_conversation_context(
            conversation_id=sample_conversation_id,
            user_id=sample_user_id,
            db_session=mock_db_session
        )

        # Assert
        assert result == ""

    def test_formats_messages_correctly(
        self, generation_service, mock_db_session, sample_conversation_id, sample_user_id
    ):
        """Test that messages are formatted as User/Assistant dialog."""
        # Arrange
        conv_uuid = UUID(sample_conversation_id)
        user_uuid = UUID(sample_user_id)

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.id = conv_uuid
        mock_conversation.user_id = user_uuid

        # Create mock messages
        messages = [
            Mock(role="user", content="What is a PLC?", created_at=datetime(2024, 1, 1, 10, 0)),
            Mock(role="assistant", content="A PLC is a Professional Learning Community.", created_at=datetime(2024, 1, 1, 10, 1)),
            Mock(role="user", content="How do we implement it?", created_at=datetime(2024, 1, 1, 10, 2)),
        ]

        # Setup mock query chains
        conversation_query = Mock()
        conversation_query.filter.return_value.first.return_value = mock_conversation

        messages_query = Mock()
        messages_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = list(reversed(messages))

        # Mock different return values for conversation vs messages queries
        mock_db_session.query.side_effect = [conversation_query, messages_query]

        # Act
        result = generation_service.get_conversation_context(
            conversation_id=sample_conversation_id,
            user_id=sample_user_id,
            db_session=mock_db_session
        )

        # Assert
        assert "User: What is a PLC?" in result
        assert "Assistant: A PLC is a Professional Learning Community." in result
        assert "User: How do we implement it?" in result
        # Check order (oldest to newest after reversal)
        assert result.index("What is a PLC?") < result.index("Professional Learning Community")
        assert result.index("Professional Learning Community") < result.index("How do we implement it?")

    def test_limits_to_10_messages(
        self, generation_service, mock_db_session, sample_conversation_id, sample_user_id
    ):
        """Test that only last 10 messages are included."""
        # Arrange
        conv_uuid = UUID(sample_conversation_id)
        user_uuid = UUID(sample_user_id)

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.id = conv_uuid
        mock_conversation.user_id = user_uuid

        # Create 15 mock messages (should only get 10)
        messages = [
            Mock(role="user" if i % 2 == 0 else "assistant", content=f"Message {i}", created_at=datetime(2024, 1, 1, 10, i))
            for i in range(15)
        ]

        # Only the last 10 should be returned
        last_10_messages = messages[-10:]

        conversation_query = Mock()
        conversation_query.filter.return_value.first.return_value = mock_conversation

        messages_query = Mock()
        # ORDER BY DESC with LIMIT 10 returns last 10 in reverse
        messages_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = list(reversed(last_10_messages))

        mock_db_session.query.side_effect = [conversation_query, messages_query]

        # Act
        result = generation_service.get_conversation_context(
            conversation_id=sample_conversation_id,
            user_id=sample_user_id,
            db_session=mock_db_session
        )

        # Assert
        # Should have messages 5-14 (the last 10)
        assert "Message 5" in result
        assert "Message 14" in result
        # Should NOT have messages 0-4 (older than last 10)
        assert "Message 0" not in result
        assert "Message 4" not in result

    def test_unauthorized_user_raises_error(
        self, generation_service, mock_db_session, sample_conversation_id
    ):
        """Test that mismatched user_id raises ValueError."""
        # Arrange
        wrong_user_id = str(uuid4())

        # Mock conversation not found for this user
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="not found or access denied"):
            generation_service.get_conversation_context(
                conversation_id=sample_conversation_id,
                user_id=wrong_user_id,
                db_session=mock_db_session
            )

    def test_nonexistent_conversation_raises_error(
        self, generation_service, mock_db_session, sample_user_id
    ):
        """Test that nonexistent conversation ID raises ValueError."""
        # Arrange
        fake_conversation_id = str(uuid4())

        # Mock conversation not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="not found or access denied"):
            generation_service.get_conversation_context(
                conversation_id=fake_conversation_id,
                user_id=sample_user_id,
                db_session=mock_db_session
            )

    def test_skips_system_messages(
        self, generation_service, mock_db_session, sample_conversation_id, sample_user_id
    ):
        """Test that system role messages are excluded from context."""
        # Arrange
        conv_uuid = UUID(sample_conversation_id)
        user_uuid = UUID(sample_user_id)

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.id = conv_uuid
        mock_conversation.user_id = user_uuid

        messages = [
            Mock(role="user", content="Hello", created_at=datetime(2024, 1, 1, 10, 0)),
            Mock(role="system", content="System notification", created_at=datetime(2024, 1, 1, 10, 1)),
            Mock(role="assistant", content="Hi there", created_at=datetime(2024, 1, 1, 10, 2)),
        ]

        conversation_query = Mock()
        conversation_query.filter.return_value.first.return_value = mock_conversation

        messages_query = Mock()
        messages_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = list(reversed(messages))

        mock_db_session.query.side_effect = [conversation_query, messages_query]

        # Act
        result = generation_service.get_conversation_context(
            conversation_id=sample_conversation_id,
            user_id=sample_user_id,
            db_session=mock_db_session
        )

        # Assert
        assert "User: Hello" in result
        assert "Assistant: Hi there" in result
        assert "System notification" not in result
        assert "system" not in result.lower()


class TestGenerateWithConversationHistory:
    """Test generate() method with conversation_history parameter."""

    @pytest.fixture
    def generation_service(self, monkeypatch):
        """Create a GenerationService instance with mocked OpenAI client."""
        monkeypatch.setenv("OPENAI_API_KEY", "fake-key-for-testing")
        return GenerationService()

    def test_generate_accepts_conversation_history(self, generation_service, monkeypatch):
        """Test that generate() accepts and uses conversation_history parameter."""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(total_tokens=100, prompt_tokens=80, completion_tokens=20)

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        monkeypatch.setattr(generation_service, "client", mock_client)

        # Arrange
        query = "Can you elaborate?"
        chunks = [
            {
                'content': 'Sample content',
                'metadata': {
                    'book_title': 'Test Book',
                    'authors': ['Author Name'],
                    'chapter_number': 1,
                    'chapter_title': 'Test Chapter',
                    'page_start': 10,
                    'page_end': 15
                }
            }
        ]
        conversation_history = "User: What is a PLC?\n\nAssistant: A PLC is a Professional Learning Community."

        # Act
        result = generation_service.generate(
            query=query,
            retrieved_chunks=chunks,
            conversation_history=conversation_history
        )

        # Assert
        assert 'response' in result
        assert result['response'] == "Test response"

        # Verify conversation history was included in prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']

        assert "Previous conversation:" in user_message
        assert "What is a PLC?" in user_message
        assert "Professional Learning Community" in user_message

    def test_generate_works_without_conversation_history(self, generation_service, monkeypatch):
        """Test that generate() still works when conversation_history is None."""
        # Mock OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(total_tokens=100, prompt_tokens=80, completion_tokens=20)

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        monkeypatch.setattr(generation_service, "client", mock_client)

        # Arrange
        query = "What is assessment?"
        chunks = [
            {
                'content': 'Sample content',
                'metadata': {
                    'book_title': 'Test Book',
                    'authors': ['Author Name'],
                    'chapter_number': 1,
                    'chapter_title': 'Test Chapter',
                    'page_start': 10,
                    'page_end': 15
                }
            }
        ]

        # Act
        result = generation_service.generate(
            query=query,
            retrieved_chunks=chunks,
            conversation_history=None
        )

        # Assert
        assert 'response' in result
        assert result['response'] == "Test response"

        # Verify NO conversation history in prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']

        assert "Previous conversation:" not in user_message
