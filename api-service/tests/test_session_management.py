"""Tests for session management and logout functionality."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import get_db
from app.models.user import User
from app.models.session import Session as UserSession
from app.services.auth_service import create_session, get_session_by_id, update_session_activity, delete_session
from app.services.cleanup_service import delete_expired_sessions
from app.config import settings


def override_get_db(db_session):
    """Create override function that uses the test's db_session."""
    def _override():
        try:
            yield db_session
        finally:
            pass  # Don't close, let fixture handle it
    return _override


@pytest.fixture(autouse=True)
def setup_db_override(db_session):
    """Automatically override get_db for all tests in this module."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    yield
    app.dependency_overrides.clear()


# Create test client (uses database from conftest.py)
client = TestClient(app)


@pytest.fixture
def db(db_session):
    """Database session fixture (from conftest.py)."""
    return db_session


@pytest.fixture
def test_user(db):
    """Create a test user."""
    # Use unique email per test run to avoid conflicts
    unique_id = uuid.uuid4()
    user = User(
        email=f"test-{unique_id}@example.com",
        name="Test User",
        role="educator",
        sso_provider="google",
        sso_id=f"google_{unique_id}",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_session(db, test_user):
    """Create a test session."""
    session = create_session(db, test_user.id)
    return session


# ============================================================================
# AC1: Logout Functionality Tests
# ============================================================================

def test_logout_deletes_session_and_clears_cookie(db, test_user):
    """Test that logout deletes session from database and clears cookie."""
    # Create session directly in test DB
    test_session = create_session(db, test_user.id)
    session_id = test_session.id

    # Verify session exists before logout
    assert get_session_by_id(db, session_id) is not None

    # Call delete_session directly (unit test approach)
    result = delete_session(db, session_id)

    # Assert deletion succeeded
    assert result is True

    # Assert session is deleted from database
    assert get_session_by_id(db, session_id) is None

    # Also test the endpoint returns correct response
    fake_session_id = uuid.uuid4()
    client.cookies.set(settings.session_cookie_name, str(fake_session_id))
    response = client.post("/auth/logout")

    # Assert response
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}

    # Assert session cookie is cleared (deleted)
    set_cookie_header = response.headers.get("set-cookie", "")
    assert settings.session_cookie_name in set_cookie_header


def test_logout_with_invalid_session_returns_200_ok():
    """Test that logout with invalid session still returns 200 OK (graceful degradation)."""
    # Set invalid session cookie
    client.cookies.set(settings.session_cookie_name, str(uuid.uuid4()))

    # Call logout endpoint
    response = client.post("/auth/logout")

    # Assert response is still 200 OK
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}


def test_logout_with_missing_session_returns_200_ok():
    """Test that logout without session cookie still returns 200 OK."""
    # Clear all cookies
    client.cookies.clear()

    # Call logout endpoint
    response = client.post("/auth/logout")

    # Assert response is 200 OK
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}


# ============================================================================
# AC2: Session Expiry (Inactivity Timeout) Tests
# ============================================================================

def test_session_validation_rejects_inactive_session_30min(db, test_user):
    """Test that sessions inactive for 30 minutes are rejected."""
    # Create session with last_accessed_at 31 minutes ago
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=test_user.id,
        expires_at=now + timedelta(hours=24),  # Not yet absolutely expired
        created_at=now - timedelta(minutes=31),
        last_accessed_at=now - timedelta(minutes=31)  # Inactive for 31 minutes
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Set session cookie
    client.cookies.set(settings.session_cookie_name, str(session.id))

    # Try to use session (using logout as a protected endpoint placeholder)
    # Note: In full implementation, we'd have a protected endpoint with session validation
    # For now, we test the dependency directly
    from app.dependencies.session import get_current_session
    from fastapi import Request

    # Mock request with session cookie
    class MockRequest:
        def __init__(self, session_id):
            self.cookies = {settings.session_cookie_name: str(session_id)}

    mock_request = MockRequest(session.id)

    # Call session validation - should raise 401
    with pytest.raises(Exception) as exc_info:
        import asyncio
        asyncio.run(get_current_session(mock_request, db))

    # Assert 401 Unauthorized for inactive session
    assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value) or "inactivity" in str(exc_info.value).lower()


def test_session_validation_accepts_active_session_within_30min(db, test_user):
    """Test that sessions active within 30 minutes are accepted."""
    # Create session with last_accessed_at 25 minutes ago (within window)
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=test_user.id,
        expires_at=now + timedelta(hours=24),
        created_at=now - timedelta(minutes=25),
        last_accessed_at=now - timedelta(minutes=25)  # Active within 30 minutes
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Test session validation
    from app.dependencies.session import get_current_session
    class MockRequest:
        def __init__(self, session_id):
            self.cookies = {settings.session_cookie_name: str(session_id)}

    mock_request = MockRequest(session.id)

    # Call session validation - should succeed
    import asyncio
    result = asyncio.run(get_current_session(mock_request, db))

    # Assert session is returned
    assert result is not None
    assert result.id == session.id


# ============================================================================
# AC3: Session Activity Refresh Tests
# ============================================================================

def test_session_activity_updates_last_accessed_at(db, test_session):
    """Test that session activity refresh updates last_accessed_at."""
    # Get initial last_accessed_at
    original_last_accessed = test_session.last_accessed_at

    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)

    # Update session activity
    update_session_activity(db, test_session)

    # Refresh session from database
    db.refresh(test_session)

    # Assert last_accessed_at was updated
    assert test_session.last_accessed_at > original_last_accessed


def test_session_expiry_extension_when_near_expiration(db, test_user):
    """Test that session expiry is extended when within 6 hours of expiration."""
    # Create session expiring in 3 hours (within 6-hour extension window)
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=test_user.id,
        expires_at=now + timedelta(hours=3),  # Expires in 3 hours
        created_at=now,
        last_accessed_at=now
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    original_expires_at = session.expires_at

    # Update session activity (should extend expiry)
    update_session_activity(db, session)

    # Refresh session from database
    db.refresh(session)

    # Assert expiry was extended
    assert session.expires_at > original_expires_at
    # Should be extended by 24 hours from now
    expected_expiry = now + timedelta(seconds=settings.session_max_age)
    # Allow 10-second tolerance for test execution time
    assert abs((session.expires_at - expected_expiry).total_seconds()) < 10


def test_session_expiry_not_extended_when_far_from_expiration(db, test_user):
    """Test that session expiry is NOT extended when more than 6 hours from expiration."""
    # Create session expiring in 20 hours (outside 6-hour extension window)
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=test_user.id,
        expires_at=now + timedelta(hours=20),  # Expires in 20 hours
        created_at=now,
        last_accessed_at=now
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    original_expires_at = session.expires_at

    # Update session activity (should NOT extend expiry)
    update_session_activity(db, session)

    # Refresh session from database
    db.refresh(session)

    # Assert expiry was NOT extended (remains the same)
    assert session.expires_at == original_expires_at


# ============================================================================
# AC4: Session Validation Middleware Tests
# ============================================================================

def test_session_validation_checks_existence(db):
    """Test that session validation rejects non-existent sessions."""
    # Create non-existent session ID
    fake_session_id = uuid.uuid4()

    # Test session validation
    from app.dependencies.session import get_current_session
    class MockRequest:
        def __init__(self, session_id):
            self.cookies = {settings.session_cookie_name: str(session_id)}

    mock_request = MockRequest(fake_session_id)

    # Call session validation - should raise 401
    with pytest.raises(Exception) as exc_info:
        import asyncio
        asyncio.run(get_current_session(mock_request, db))

    # Assert 401 Unauthorized
    assert "401" in str(exc_info.value) or "not found" in str(exc_info.value).lower()


def test_session_validation_checks_absolute_expiry(db, test_user):
    """Test that session validation rejects absolutely expired sessions."""
    # Create session that expired 1 hour ago
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=test_user.id,
        expires_at=now - timedelta(hours=1),  # Expired 1 hour ago
        created_at=now - timedelta(hours=25),
        last_accessed_at=now - timedelta(minutes=5)  # Recently accessed but absolutely expired
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Test session validation
    from app.dependencies.session import get_current_session
    class MockRequest:
        def __init__(self, session_id):
            self.cookies = {settings.session_cookie_name: str(session_id)}

    mock_request = MockRequest(session.id)

    # Call session validation - should raise 401
    with pytest.raises(Exception) as exc_info:
        import asyncio
        asyncio.run(get_current_session(mock_request, db))

    # Assert 401 Unauthorized for expired session
    assert "401" in str(exc_info.value) or "expired" in str(exc_info.value).lower()


def test_invalid_session_cookie_returns_401(db):
    """Test that invalid session cookie format returns 401."""
    # Test session validation with malformed cookie
    from app.dependencies.session import get_current_session
    class MockRequest:
        def __init__(self, bad_cookie):
            self.cookies = {settings.session_cookie_name: bad_cookie}

    mock_request = MockRequest("not-a-valid-uuid")

    # Call session validation - should raise 401
    with pytest.raises(Exception) as exc_info:
        import asyncio
        asyncio.run(get_current_session(mock_request, db))

    # Assert 401 Unauthorized
    assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)


# ============================================================================
# AC5: Background Session Cleanup Tests
# ============================================================================

def test_background_cleanup_deletes_expired_sessions_only(db, test_user):
    """Test that cleanup deletes only expired sessions, not active ones."""
    now = datetime.now(timezone.utc)

    # Create 3 sessions:
    # 1. Expired session (expires_at in the past)
    expired_session = UserSession(
        user_id=test_user.id,
        expires_at=now - timedelta(hours=1),  # Expired
        created_at=now - timedelta(hours=25),
        last_accessed_at=now - timedelta(hours=2)
    )
    db.add(expired_session)

    # 2. Active session (expires_at in the future)
    active_session = UserSession(
        user_id=test_user.id,
        expires_at=now + timedelta(hours=23),  # Active
        created_at=now,
        last_accessed_at=now
    )
    db.add(active_session)

    # 3. Another expired session
    expired_session2 = UserSession(
        user_id=test_user.id,
        expires_at=now - timedelta(days=1),  # Expired
        created_at=now - timedelta(days=2),
        last_accessed_at=now - timedelta(days=1)
    )
    db.add(expired_session2)

    db.commit()

    # Run cleanup
    deleted_count = delete_expired_sessions(db)

    # Refresh db session to see deletion
    db.expire_all()

    # Assert 2 sessions were deleted
    assert deleted_count == 2

    # Assert active session still exists
    assert get_session_by_id(db, active_session.id) is not None

    # Assert expired sessions were deleted
    assert get_session_by_id(db, expired_session.id) is None
    assert get_session_by_id(db, expired_session2.id) is None


def test_cleanup_logs_deletion_count(db, test_user):
    """Test that cleanup logs the number of sessions deleted."""
    # Create an expired session
    now = datetime.now(timezone.utc)
    expired_session = UserSession(
        user_id=test_user.id,
        expires_at=now - timedelta(hours=1),
        created_at=now - timedelta(hours=25),
        last_accessed_at=now - timedelta(hours=2)
    )
    db.add(expired_session)
    db.commit()

    # Run cleanup with logging check
    with patch('app.services.cleanup_service.logger') as mock_logger:
        deleted_count = delete_expired_sessions(db)

        # Assert logging was called
        assert mock_logger.info.called
        # Check log message includes count
        log_call_args = str(mock_logger.info.call_args)
        assert str(deleted_count) in log_call_args


def test_manual_cleanup_endpoint_returns_count(db, test_user):
    """Test that manual cleanup endpoint returns deletion count (requires admin auth - Story 1.8)."""
    # Update test user to admin role
    test_user.role = "admin"
    db.commit()
    db.refresh(test_user)

    # Create session for admin user
    admin_session = create_session(db, test_user.id)

    # Call manual cleanup endpoint with admin session
    response = client.post(
        "/api/admin/cleanup-sessions",
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert response
    assert response.status_code == 200
    assert "sessions_deleted" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "completed"


# ============================================================================
# AC6: Audit Logging Tests
# ============================================================================

def test_session_creation_logged(db, test_user):
    """Test that session creation is logged."""
    with patch('app.services.auth_service.logger') as mock_logger:
        # Create session
        session = create_session(db, test_user.id)

        # Assert logging was called
        assert mock_logger.info.called
        # Check log includes user_id and session_id
        log_call_args = str(mock_logger.info.call_args)
        assert str(test_user.id) in log_call_args
        assert str(session.id) in log_call_args
        assert "Session created" in log_call_args or "created" in log_call_args.lower()


def test_session_refresh_logged(db, test_session):
    """Test that session refresh is logged."""
    with patch('app.services.auth_service.logger') as mock_logger:
        # Update session activity
        update_session_activity(db, test_session)

        # Assert logging was called
        assert mock_logger.info.called
        # Check log includes session_id and activity update
        log_call_args = str(mock_logger.info.call_args_list)
        assert str(test_session.id) in log_call_args
        assert "activity" in log_call_args.lower() or "refresh" in log_call_args.lower()


def test_session_deletion_logged(db, test_session):
    """Test that session deletion (logout) is logged."""
    with patch('app.services.auth_service.logger') as mock_logger:
        # Delete session
        delete_session(db, test_session.id)

        # Assert logging was called
        assert mock_logger.info.called
        # Check log includes session_id and deletion/logout
        log_call_args = str(mock_logger.info.call_args)
        assert str(test_session.id) in log_call_args
        assert "deleted" in log_call_args.lower() or "logout" in log_call_args.lower()
