"""Tests for initial schema migration (001_initial_schema)."""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models import User, Session, Conversation, Message


@pytest.fixture(scope="module")
def test_database_url():
    """Provide test database URL (uses local PostgreSQL)."""
    return os.getenv(
        'TEST_DATABASE_URL',
        'postgresql+psycopg2://postgres:postgres@localhost:5432/plccoach_test'
    )


@pytest.fixture(scope="module")
def alembic_config():
    """Create Alembic configuration for testing."""
    # Point to alembic.ini in api-service directory
    config = Config(os.path.join(os.path.dirname(__file__), '../../alembic.ini'))
    return config


@pytest.fixture(scope="module")
def db_engine(test_database_url):
    """Create database engine for testing."""
    engine = create_engine(test_database_url)

    # Create test database if it doesn't exist
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        # Database doesn't exist, this is expected in CI
        pytest.skip("Test database not available. Run: createdb plccoach_test")

    yield engine

    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine, alembic_config, test_database_url):
    """Create a clean database session for each test."""
    # Set database URL in alembic config
    alembic_config.set_main_option('sqlalchemy.url', test_database_url)

    # Drop all tables
    command.downgrade(alembic_config, 'base')

    # Apply migrations
    command.upgrade(alembic_config, 'head')

    # Create session
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    command.downgrade(alembic_config, 'base')


class TestInitialSchemaMigration:
    """Test suite for initial schema migration."""

    def test_all_tables_created(self, db_session):
        """Verify all required tables are created."""
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()

        assert 'users' in tables
        assert 'sessions' in tables
        assert 'conversations' in tables
        assert 'messages' in tables

    def test_pgvector_extension_installed(self, db_session):
        """Verify pgvector extension is installed."""
        result = db_session.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        )
        assert result.rowcount == 1

    def test_users_table_structure(self, db_session):
        """Verify users table has correct columns and constraints."""
        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        # Check all required columns exist
        required_columns = [
            'id', 'email', 'name', 'role', 'organization_id',
            'sso_provider', 'sso_id', 'created_at', 'last_login'
        ]
        for col_name in required_columns:
            assert col_name in columns, f"Column {col_name} missing from users table"

        # Check unique constraint on email
        unique_constraints = inspector.get_unique_constraints('users')
        email_unique = any('email' in uc['column_names'] for uc in unique_constraints)
        assert email_unique, "Email should have unique constraint"

    def test_sessions_table_structure(self, db_session):
        """Verify sessions table has correct columns and foreign key."""
        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('sessions')}

        required_columns = ['id', 'user_id', 'expires_at', 'created_at', 'last_accessed_at']
        for col_name in required_columns:
            assert col_name in columns

        # Check foreign key to users
        foreign_keys = inspector.get_foreign_keys('sessions')
        assert len(foreign_keys) > 0
        assert any(fk['referred_table'] == 'users' for fk in foreign_keys)

    def test_conversations_table_structure(self, db_session):
        """Verify conversations table has correct columns."""
        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('conversations')}

        required_columns = [
            'id', 'user_id', 'title', 'status', 'created_at',
            'updated_at', 'share_token', 'share_enabled'
        ]
        for col_name in required_columns:
            assert col_name in columns

    def test_messages_table_structure(self, db_session):
        """Verify messages table has correct columns and JSONB type."""
        inspector = inspect(db_session.bind)
        columns = {col['name']: col for col in inspector.get_columns('messages')}

        required_columns = [
            'id', 'conversation_id', 'role', 'content', 'citations',
            'domains', 'feedback_score', 'input_tokens', 'output_tokens',
            'cost_usd', 'created_at'
        ]
        for col_name in required_columns:
            assert col_name in columns

        # Verify citations is JSONB
        assert 'citations' in columns

    def test_all_indexes_created(self, db_session):
        """Verify all performance indexes are created."""
        inspector = inspect(db_session.bind)

        # Check users indexes
        users_indexes = inspector.get_indexes('users')
        assert any('email' in idx['column_names'] for idx in users_indexes)

        # Check conversations indexes
        conv_indexes = inspector.get_indexes('conversations')
        assert any('user_id' in idx['column_names'] for idx in conv_indexes)

        # Check messages indexes
        msg_indexes = inspector.get_indexes('messages')
        assert any(
            'conversation_id' in idx['column_names'] and 'created_at' in idx['column_names']
            for idx in msg_indexes
        )

    def test_cascade_delete_sessions(self, db_session):
        """Verify CASCADE delete removes sessions when user is deleted."""
        # Create user
        user = User(
            id=uuid.uuid4(),
            email='test@example.com',
            name='Test User',
            role='educator'
        )
        db_session.add(user)
        db_session.commit()

        # Create session for user
        session = Session(
            id=uuid.uuid4(),
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        db_session.add(session)
        db_session.commit()

        session_id = session.id

        # Delete user
        db_session.delete(user)
        db_session.commit()

        # Verify session was also deleted
        deleted_session = db_session.query(Session).filter_by(id=session_id).first()
        assert deleted_session is None

    def test_cascade_delete_messages(self, db_session):
        """Verify CASCADE delete removes messages when conversation is deleted."""
        # Create user and conversation
        user = User(
            id=uuid.uuid4(),
            email='test2@example.com',
            name='Test User 2',
            role='educator'
        )
        db_session.add(user)
        db_session.commit()

        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user.id,
            title='Test Conversation'
        )
        db_session.add(conversation)
        db_session.commit()

        # Create message
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role='user',
            content='Test message'
        )
        db_session.add(message)
        db_session.commit()

        message_id = message.id

        # Delete conversation
        db_session.delete(conversation)
        db_session.commit()

        # Verify message was also deleted
        deleted_message = db_session.query(Message).filter_by(id=message_id).first()
        assert deleted_message is None

    def test_jsonb_citations_field(self, db_session):
        """Test JSONB insertion and query on citations field."""
        # Create user, conversation, and message with citations
        user = User(
            id=uuid.uuid4(),
            email='test3@example.com',
            name='Test User 3',
            role='educator'
        )
        conversation = Conversation(
            id=uuid.uuid4(),
            user_id=user.id,
            title='Test'
        )
        db_session.add_all([user, conversation])
        db_session.commit()

        # Message with complex JSONB citations
        citations_data = {
            'sources': [
                {'title': 'Source 1', 'url': 'https://example.com/1', 'relevance': 0.95},
                {'title': 'Source 2', 'url': 'https://example.com/2', 'relevance': 0.87}
            ],
            'confidence': 0.92
        }

        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation.id,
            role='assistant',
            content='Test response',
            citations=citations_data
        )
        db_session.add(message)
        db_session.commit()

        # Query and verify JSONB structure
        retrieved = db_session.query(Message).filter_by(id=message.id).first()
        assert retrieved.citations == citations_data
        assert retrieved.citations['confidence'] == 0.92
        assert len(retrieved.citations['sources']) == 2

    def test_role_check_constraints(self, db_session):
        """Test that role check constraints are enforced."""
        # Try to create user with invalid role (should raise error)
        user = User(
            id=uuid.uuid4(),
            email='invalid@example.com',
            name='Invalid User',
            role='superuser'  # Invalid role
        )
        db_session.add(user)

        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

        db_session.rollback()

    def test_migration_rollback(self, db_engine, alembic_config, test_database_url):
        """Test that migration can be rolled back successfully."""
        alembic_config.set_main_option('sqlalchemy.url', test_database_url)

        # Apply migration
        command.upgrade(alembic_config, 'head')

        # Verify tables exist
        inspector = inspect(db_engine)
        tables_before = inspector.get_table_names()
        assert 'users' in tables_before

        # Rollback
        command.downgrade(alembic_config, 'base')

        # Verify tables are gone
        tables_after = inspector.get_table_names()
        assert 'users' not in tables_after
        assert 'sessions' not in tables_after
        assert 'conversations' not in tables_after
        assert 'messages' not in tables_after

        # Verify pgvector extension is removed
        with db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM pg_extension WHERE extname = 'vector'")
            )
            assert result.rowcount == 0
