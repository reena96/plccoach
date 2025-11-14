"""Unit tests for authentication service functions."""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

from app.config import settings


# Mock the models to avoid SQLAlchemy circular dependency issues
@patch('app.services.auth_service.User')
@patch('app.services.auth_service.UserSession')
def test_get_or_create_user_creates_new_user(mock_session_class, mock_user_class):
    """Test that get_or_create_user creates a new user when none exists."""
    from app.services.auth_service import get_or_create_user

    # Mock database session
    db = MagicMock()
    db.query().filter().first.return_value = None  # No existing user

    # Mock User instance
    mock_user = MagicMock()
    mock_user_class.return_value = mock_user

    # Call function
    user = get_or_create_user(
        db=db,
        email="new@example.com",
        name="New User",
        sso_provider="google",
        sso_id="google-123"
    )

    # Verify User was instantiated with correct parameters
    mock_user_class.assert_called_once()
    call_kwargs = mock_user_class.call_args[1]
    assert call_kwargs['email'] == "new@example.com"
    assert call_kwargs['name'] == "New User"
    assert call_kwargs['role'] == "educator"
    assert call_kwargs['sso_provider'] == "google"
    assert call_kwargs['sso_id'] == "google-123"

    # Verify database operations
    assert db.add.called
    assert db.commit.called
    assert db.refresh.called
    assert user == mock_user


@patch('app.services.auth_service.User')
def test_get_or_create_user_updates_existing_user(mock_user_class):
    """Test that get_or_create_user updates existing user's last_login and profile."""
    from app.services.auth_service import get_or_create_user

    # Mock existing user
    existing_user = MagicMock()
    existing_user.email = "old@example.com"
    existing_user.name = "Old Name"
    existing_user.last_login = datetime.now(timezone.utc) - timedelta(days=1)
    old_last_login = existing_user.last_login

    # Mock database session
    db = MagicMock()
    db.query().filter().first.return_value = existing_user

    # Call function with updated info
    user = get_or_create_user(
        db=db,
        email="new@example.com",  # Email changed
        name="New Name",  # Name changed
        sso_provider="google",
        sso_id="google-123"
    )

    # Verify user was updated (not created)
    mock_user_class.assert_not_called()  # Should not create new user
    assert db.commit.called
    assert user == existing_user
    assert existing_user.email == "new@example.com"
    assert existing_user.name == "New Name"
    # last_login should be updated (though we can't check exact value due to mocking)


@patch('app.services.auth_service.UserSession')
def test_create_session_with_correct_expiry(mock_session_class):
    """Test that create_session creates session with 24-hour expiry."""
    from app.services.auth_service import create_session

    # Mock database session
    db = MagicMock()

    # Mock UserSession instance
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    user_id = uuid.uuid4()
    before_creation = datetime.now(timezone.utc)

    # Call function
    session = create_session(db=db, user_id=user_id)

    after_creation = datetime.now(timezone.utc)

    # Verify UserSession was instantiated
    mock_session_class.assert_called_once()
    call_kwargs = mock_session_class.call_args[1]

    # Verify session parameters
    assert call_kwargs['user_id'] == user_id
    assert isinstance(call_kwargs['expires_at'], datetime)
    assert isinstance(call_kwargs['created_at'], datetime)
    assert isinstance(call_kwargs['last_accessed_at'], datetime)

    # Verify expiry is approximately 24 hours from now
    expected_expiry = before_creation + timedelta(seconds=settings.session_max_age)
    assert abs((call_kwargs['expires_at'] - expected_expiry).total_seconds()) < 2

    # Verify database operations
    assert db.add.called
    assert db.commit.called
    assert db.refresh.called
    assert session == mock_session


@patch('app.services.auth_service.UserSession')
def test_create_session_sets_timestamps(mock_session_class):
    """Test that create_session sets created_at and last_accessed_at."""
    from app.services.auth_service import create_session

    # Mock database session
    db = MagicMock()

    # Mock UserSession instance
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    user_id = uuid.uuid4()
    before_creation = datetime.now(timezone.utc)

    # Call function
    session = create_session(db=db, user_id=user_id)

    after_creation = datetime.now(timezone.utc)

    # Get the arguments passed to UserSession()
    call_kwargs = mock_session_class.call_args[1]

    # Verify timestamps are set
    assert call_kwargs['created_at'] >= before_creation
    assert call_kwargs['created_at'] <= after_creation
    assert call_kwargs['last_accessed_at'] >= before_creation
    assert call_kwargs['last_accessed_at'] <= after_creation


@patch('app.services.auth_service.User')
def test_get_or_create_user_sets_default_role(mock_user_class):
    """Test that new users get default role='educator'."""
    from app.services.auth_service import get_or_create_user

    # Mock database session
    db = MagicMock()
    db.query().filter().first.return_value = None  # No existing user

    # Mock User instance
    mock_user = MagicMock()
    mock_user_class.return_value = mock_user

    # Call function
    user = get_or_create_user(
        db=db,
        email="educator@example.com",
        name="New Educator",
        sso_provider="google",
        sso_id="google-456"
    )

    # Get the arguments passed to User()
    call_kwargs = mock_user_class.call_args[1]

    # Verify default role
    assert call_kwargs['role'] == "educator"
    assert call_kwargs['sso_provider'] == "google"
    assert call_kwargs['sso_id'] == "google-456"
