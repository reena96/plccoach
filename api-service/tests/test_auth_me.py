"""Tests for GET /auth/me endpoint (Story 1.8)."""
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.session import Session as UserSession
from app.services.database import get_db


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


client = TestClient(app)


def test_get_me_valid_session(db_session: Session):
    """AC1: GET /auth/me returns 200 with user profile for valid session."""
    # Create test user
    user = User(
        email="test@example.com",
        name="Test User",
        role="educator",
        sso_provider="google",
        sso_id="google_123",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create valid session
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
        last_accessed_at=datetime.now(timezone.utc)
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Make request with session cookie
    response = client.get(
        "/auth/me",
        cookies={"plc_session": str(session.id)}
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user.id)
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert data["role"] == "educator"
    assert data["sso_provider"] == "google"
    assert "sso_id" not in data  # AC1: Exclude sensitive fields
    assert "created_at" in data
    assert "last_login" in data


def test_get_me_no_session_cookie(db_session: Session):
    """AC2: GET /auth/me returns 401 for missing session cookie."""
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert "Unauthorized" in response.json()["detail"]


def test_get_me_invalid_session_id(db_session: Session):
    """AC2: GET /auth/me returns 401 for invalid session ID format."""
    response = client.get(
        "/auth/me",
        cookies={"plc_session": "invalid-uuid"}
    )

    assert response.status_code == 401
    assert "Invalid session" in response.json()["detail"]


def test_get_me_nonexistent_session(db_session: Session):
    """AC2: GET /auth/me returns 401 for non-existent session."""
    fake_session_id = str(uuid.uuid4())

    response = client.get(
        "/auth/me",
        cookies={"plc_session": fake_session_id}
    )

    assert response.status_code == 401
    assert "Session not found" in response.json()["detail"]


def test_get_me_expired_session(db_session: Session):
    """AC2: GET /auth/me returns 401 for expired session."""
    # Create test user
    user = User(
        email="test@example.com",
        name="Test User",
        role="educator",
        sso_provider="google",
        sso_id="google_123",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create expired session (expires_at in the past)
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired 1 hour ago
        created_at=datetime.now(timezone.utc) - timedelta(hours=25),
        last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Make request with expired session cookie
    response = client.get(
        "/auth/me",
        cookies={"plc_session": str(session.id)}
    )

    # Assert 401 Unauthorized
    assert response.status_code == 401
    assert "Session expired" in response.json()["detail"]


def test_get_me_datetime_timezone_aware(db_session: Session):
    """AC1: GET /auth/me datetime fields are timezone-aware and serialize correctly."""
    # Create test user with explicit timezone-aware datetimes
    now = datetime.now(timezone.utc)
    user = User(
        email="test@example.com",
        name="Test User",
        role="coach",
        sso_provider="clever",
        sso_id="clever_456",
        created_at=now,
        last_login=now
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create valid session
    session = UserSession(
        user_id=user.id,
        expires_at=now + timedelta(hours=24),
        created_at=now,
        last_accessed_at=now
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Make request
    response = client.get(
        "/auth/me",
        cookies={"plc_session": str(session.id)}
    )

    # Assert datetime fields are present and in ISO 8601 format
    assert response.status_code == 200
    data = response.json()
    assert "created_at" in data
    assert "last_login" in data

    # Verify ISO 8601 format (ends with Z for UTC)
    assert data["created_at"].endswith("Z") or "+" in data["created_at"]
    assert data["last_login"].endswith("Z") or "+" in data["last_login"]


def test_get_me_session_activity_updated(db_session: Session):
    """AC8: GET /auth/me updates session last_accessed_at timestamp."""
    # Create test user
    user = User(
        email="test@example.com",
        name="Test User",
        role="educator",
        sso_provider="google",
        sso_id="google_123",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create session with last_accessed_at in the past
    old_access_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=old_access_time,
        last_accessed_at=old_access_time
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Make request (should update last_accessed_at)
    response = client.get(
        "/auth/me",
        cookies={"plc_session": str(session.id)}
    )

    # Assert request succeeded
    assert response.status_code == 200

    # Refresh session from database and check last_accessed_at was updated
    db_session.refresh(session)
    assert session.last_accessed_at > old_access_time
    # Should be within last 5 seconds
    time_diff = datetime.now(timezone.utc) - session.last_accessed_at
    assert time_diff.total_seconds() < 5
