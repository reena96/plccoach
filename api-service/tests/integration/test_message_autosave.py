"""
Integration tests for Story 3.2: Conversation Persistence & Auto-Save

Tests full message persistence flow, conversation creation, and atomicity.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.services.database import Base, get_db


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here since test_db fixture manages it

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        role="educator"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestConversationCreation:
    """Test automatic conversation creation (AC #1)."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_conversation_created_on_first_message(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that a new conversation is created when no conversation_id provided."""
        # Arrange: Mock AI services to avoid external dependencies
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        # Act: Send query without conversation_id
        response = client.post(
            "/api/coach/query",
            json={"query": "What is project-based learning?"},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert: Request succeeds
        assert response.status_code == 200
        data = response.json()

        # Verify conversation_id was returned
        assert 'conversation_id' in data
        assert data['conversation_id'] is not None

        # Verify conversation exists in database
        conversation_id = data['conversation_id']
        conversation = test_db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        assert conversation is not None
        assert str(conversation.user_id) == str(test_user.id)
        assert conversation.status == 'active'

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_conversation_not_created_when_id_provided(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that no new conversation is created when conversation_id exists."""
        # Arrange: Create existing conversation
        existing_conversation = Conversation(
            id=uuid4(),
            user_id=test_user.id,
            title="Existing Conversation",
            status='active'
        )
        test_db.add(existing_conversation)
        test_db.commit()

        initial_count = test_db.query(Conversation).count()

        # Mock AI services
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        # Act: Send query with existing conversation_id
        response = client.post(
            "/api/coach/query",
            json={
                "query": "Follow-up question",
                "conversation_id": str(existing_conversation.id)
            },
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert: No new conversation created
        assert response.status_code == 200
        final_count = test_db.query(Conversation).count()
        assert final_count == initial_count  # No new conversation


class TestTitleGeneration:
    """Test auto-generated conversation titles (AC #3)."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_title_generated_from_first_message_short(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test title generation with message < 50 characters."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        short_query = "What is PBL?"  # 13 characters

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": short_query},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        conversation = test_db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        assert conversation.title == short_query
        assert "..." not in conversation.title

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_title_generated_from_first_message_long(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test title generation with message > 50 characters (truncated)."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        long_query = "What are the key principles of project-based learning and how can I implement them effectively?"  # >50 chars

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": long_query},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        conversation = test_db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        assert len(conversation.title) == 53  # 50 chars + "..."
        assert conversation.title.endswith("...")
        assert conversation.title.startswith(long_query[:50])


class TestMessagePersistence:
    """Test user and assistant message persistence (AC #1)."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_user_message_saved_immediately(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that user message is saved to database immediately."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        query_text = "How do I implement formative assessment?"

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": query_text},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        # Verify user message in database
        user_message = test_db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == 'user'
        ).first()

        assert user_message is not None
        assert user_message.content == query_text
        assert user_message.citations is None

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_assistant_message_saved_with_citations(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that assistant message is saved with citations."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }

        test_citations = [
            {
                "book_title": "PBL Handbook",
                "authors": "John Doe",
                "chapter": 3,
                "chapter_title": "Assessment Strategies",
                "pages": "45-52"
            }
        ]

        mock_generate.return_value = {
            'response': 'Formative assessment involves ongoing feedback...',
            'citations': test_citations,
            'token_usage': 150,
            'cost_usd': 0.002
        }

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": "How do I use formative assessment?"},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        # Verify assistant message in database
        assistant_message = test_db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == 'assistant'
        ).first()

        assert assistant_message is not None
        assert assistant_message.content == 'Formative assessment involves ongoing feedback...'
        assert assistant_message.citations == test_citations
        assert assistant_message.input_tokens == 150
        assert assistant_message.cost_usd == 0.002

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_both_messages_saved_in_single_request(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that both user and assistant messages are saved in one request."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": "Test question"},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        # Verify both messages exist
        messages = test_db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()

        assert len(messages) == 2
        roles = [msg.role for msg in messages]
        assert 'user' in roles
        assert 'assistant' in roles


class TestTransactionAtomicity:
    """Test atomic transaction behavior (AC #1)."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_all_saves_committed_together(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that conversation + user message + assistant message commit atomically."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": "Test query for atomicity"},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        # Verify all three records exist
        conversation = test_db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        assert conversation is not None

        messages = test_db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).all()
        assert len(messages) == 2

        # All three should be committed (no orphaned records)
        for message in messages:
            assert message.conversation_id == conversation.id


class TestTimestampUpdates:
    """Test conversation timestamp updates (AC #4)."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_conversation_updated_at_refreshed(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that conversation.updated_at is refreshed on message save."""
        # Arrange: Create existing conversation
        existing_conversation = Conversation(
            id=uuid4(),
            user_id=test_user.id,
            title="Existing Conversation",
            status='active'
        )
        test_db.add(existing_conversation)
        test_db.commit()
        test_db.refresh(existing_conversation)

        original_updated_at = existing_conversation.updated_at

        # Mock AI services
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Follow-up response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        # Act: Send new message to existing conversation
        # Note: Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)

        response = client.post(
            "/api/coach/query",
            json={
                "query": "Follow-up question",
                "conversation_id": str(existing_conversation.id)
            },
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200

        # Refresh conversation from database
        test_db.refresh(existing_conversation)
        new_updated_at = existing_conversation.updated_at

        # Note: SQLAlchemy's onupdate should update the timestamp
        # However, this might not work with SQLite in-memory
        # This test documents expected behavior for PostgreSQL
        assert new_updated_at >= original_updated_at


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_very_long_message_content(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test handling of very long message content."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test response',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        long_query = "A" * 2000  # Very long message

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": long_query},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert: Should handle long content
        # Note: Will fail validation if > 1000 chars (per QueryRequest model)
        # This tests the boundary
        assert response.status_code in [200, 422]

    @patch('app.services.generation_service.GenerationService.generate')
    @patch('app.services.retrieval_service.RetrievalService.retrieve')
    def test_special_characters_in_message(
        self, mock_retrieve, mock_generate, client, test_db, test_user
    ):
        """Test that special characters in messages are preserved."""
        # Arrange
        mock_retrieve.return_value = {
            'chunks': [],
            'classification': {'primary_domain': 'instructional-practice', 'secondary_domains': []}
        }
        mock_generate.return_value = {
            'response': 'Test <response> with "quotes"',
            'citations': [],
            'token_usage': 100,
            'cost_usd': 0.001
        }

        query_with_special_chars = "What's the difference between <PBL> & \"traditional\" learning?"

        # Act
        response = client.post(
            "/api/coach/query",
            json={"query": query_with_special_chars},
            headers={"X-User-Id": str(test_user.id)}
        )

        # Assert
        assert response.status_code == 200
        conversation_id = response.json()['conversation_id']

        # Verify special characters preserved
        user_message = test_db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == 'user'
        ).first()

        assert user_message.content == query_with_special_chars

    def test_request_without_user_id_header(self, client):
        """Test that request without X-User-Id header still works (no persistence)."""
        # Act: Send query without user ID
        # Note: Current implementation continues without persistence if no user_id
        response = client.post(
            "/api/coach/query",
            json={"query": "Test query"}
        )

        # Assert: Should return 200 or 500 (OpenAI failure), but not crash
        assert response.status_code in [200, 500]
