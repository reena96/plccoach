"""Tests for admin user management endpoints (Story 1.8)."""
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


@pytest.fixture
def admin_user_with_session(db_session: Session):
    """Create admin user with valid session."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        role="admin",
        sso_provider="google",
        sso_id="google_admin",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
        last_accessed_at=datetime.now(timezone.utc)
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    return user, session


@pytest.fixture
def educator_user_with_session(db_session: Session):
    """Create educator user with valid session."""
    user = User(
        email="educator@example.com",
        name="Educator User",
        role="educator",
        sso_provider="clever",
        sso_id="clever_educator",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
        last_accessed_at=datetime.now(timezone.utc)
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    return user, session


def test_list_users_admin_success(db_session: Session, admin_user_with_session):
    """AC3: GET /admin/users returns 200 with user list for admin."""
    admin_user, admin_session = admin_user_with_session

    # Create additional test users
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            name=f"User {i}",
            role="educator",
            sso_provider="google",
            sso_id=f"google_{i}",
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
            last_login=datetime.now(timezone.utc)
        )
        db_session.add(user)
    db_session.commit()

    # Make request as admin
    response = client.get(
        "/admin/users",
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert len(data["users"]) >= 4  # Admin + 3 test users
    assert data["page"] == 1
    assert data["limit"] == 50


def test_list_users_pagination(db_session: Session, admin_user_with_session):
    """AC3: GET /admin/users pagination works correctly."""
    admin_user, admin_session = admin_user_with_session

    # Create 10 test users
    for i in range(10):
        user = User(
            email=f"user{i}@example.com",
            name=f"User {i}",
            role="educator",
            sso_provider="google",
            sso_id=f"google_{i}",
            created_at=datetime.now(timezone.utc) - timedelta(days=i),
            last_login=datetime.now(timezone.utc)
        )
        db_session.add(user)
    db_session.commit()

    # Test pagination: page 2, limit 5
    response = client.get(
        "/admin/users?page=2&limit=5",
        cookies={"plc_session": str(admin_session.id)}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["limit"] == 5
    assert len(data["users"]) <= 5


def test_list_users_ordered_by_created_at_desc(db_session: Session, admin_user_with_session):
    """AC3: GET /admin/users orders by created_at descending (newest first)."""
    admin_user, admin_session = admin_user_with_session

    # Create users with different created_at times
    user1 = User(
        email="old@example.com",
        name="Old User",
        role="educator",
        sso_provider="google",
        sso_id="google_old",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
        last_login=datetime.now(timezone.utc)
    )
    user2 = User(
        email="new@example.com",
        name="New User",
        role="educator",
        sso_provider="google",
        sso_id="google_new",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add_all([user1, user2])
    db_session.commit()

    # Make request
    response = client.get(
        "/admin/users",
        cookies={"plc_session": str(admin_session.id)}
    )

    assert response.status_code == 200
    data = response.json()

    # Find our test users in the list
    users = data["users"]
    new_user_in_list = next((u for u in users if u["email"] == "new@example.com"), None)
    old_user_in_list = next((u for u in users if u["email"] == "old@example.com"), None)

    # New user should appear before old user (descending order)
    assert new_user_in_list is not None
    assert old_user_in_list is not None
    new_index = users.index(new_user_in_list)
    old_index = users.index(old_user_in_list)
    assert new_index < old_index


def test_list_users_forbidden_for_educator(db_session: Session, educator_user_with_session):
    """AC4: GET /admin/users returns 403 for non-admin users (educator)."""
    educator_user, educator_session = educator_user_with_session

    # Make request as educator
    response = client.get(
        "/admin/users",
        cookies={"plc_session": str(educator_session.id)}
    )

    # Assert 403 Forbidden
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_list_users_forbidden_for_coach(db_session: Session):
    """AC4: GET /admin/users returns 403 for non-admin users (coach)."""
    # Create coach user
    user = User(
        email="coach@example.com",
        name="Coach User",
        role="coach",
        sso_provider="google",
        sso_id="google_coach",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
        last_accessed_at=datetime.now(timezone.utc)
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    # Make request as coach
    response = client.get(
        "/admin/users",
        cookies={"plc_session": str(session.id)}
    )

    # Assert 403 Forbidden
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_update_user_role_admin_success(db_session: Session, admin_user_with_session):
    """AC5: PATCH /admin/users/:id updates role and returns 200."""
    admin_user, admin_session = admin_user_with_session

    # Create target user
    target_user = User(
        email="target@example.com",
        name="Target User",
        role="educator",
        sso_provider="google",
        sso_id="google_target",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(target_user)
    db_session.commit()
    db_session.refresh(target_user)

    # Update role from educator to coach
    response = client.patch(
        f"/admin/users/{target_user.id}",
        json={"role": "coach"},
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(target_user.id)
    assert data["role"] == "coach"

    # Verify database was updated
    db_session.refresh(target_user)
    assert target_user.role == "coach"


def test_update_user_role_invalid_role_400(db_session: Session, admin_user_with_session):
    """AC6: PATCH /admin/users/:id returns 400 for invalid role."""
    admin_user, admin_session = admin_user_with_session

    # Create target user
    target_user = User(
        email="target@example.com",
        name="Target User",
        role="educator",
        sso_provider="google",
        sso_id="google_target",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(target_user)
    db_session.commit()
    db_session.refresh(target_user)

    # Try to update with invalid role
    response = client.patch(
        f"/admin/users/{target_user.id}",
        json={"role": "superadmin"},  # Invalid role
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert 400 Bad Request (Pydantic validation error)
    assert response.status_code == 422  # FastAPI/Pydantic validation error
    assert "validation" in response.json()["detail"][0]["type"].lower() or "literal" in response.json()["detail"][0]["type"].lower()

    # Verify database was NOT modified
    db_session.refresh(target_user)
    assert target_user.role == "educator"


def test_update_user_role_not_found_404(db_session: Session, admin_user_with_session):
    """AC6: PATCH /admin/users/:id returns 404 for non-existent user."""
    admin_user, admin_session = admin_user_with_session

    fake_user_id = str(uuid.uuid4())

    # Try to update non-existent user
    response = client.patch(
        f"/admin/users/{fake_user_id}",
        json={"role": "coach"},
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert 404 Not Found
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


def test_update_user_role_forbidden_for_non_admin(db_session: Session, educator_user_with_session):
    """AC6: PATCH /admin/users/:id returns 403 for non-admin users."""
    educator_user, educator_session = educator_user_with_session

    # Create target user
    target_user = User(
        email="target@example.com",
        name="Target User",
        role="educator",
        sso_provider="google",
        sso_id="google_target",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(target_user)
    db_session.commit()
    db_session.refresh(target_user)

    # Try to update as non-admin
    response = client.patch(
        f"/admin/users/{target_user.id}",
        json={"role": "coach"},
        cookies={"plc_session": str(educator_session.id)}
    )

    # Assert 403 Forbidden
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_update_user_role_audit_logging(db_session: Session, admin_user_with_session, caplog):
    """AC10: PATCH /admin/users/:id logs role change with admin info."""
    admin_user, admin_session = admin_user_with_session

    # Create target user
    target_user = User(
        email="target@example.com",
        name="Target User",
        role="educator",
        sso_provider="google",
        sso_id="google_target",
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc)
    )
    db_session.add(target_user)
    db_session.commit()
    db_session.refresh(target_user)

    # Update role (should trigger audit log)
    with caplog.at_level("INFO"):
        response = client.patch(
            f"/admin/users/{target_user.id}",
            json={"role": "admin"},
            cookies={"plc_session": str(admin_session.id)}
        )

    # Assert success
    assert response.status_code == 200

    # Verify audit log was created
    log_messages = [record.message for record in caplog.records if "Role change" in record.message]
    assert len(log_messages) > 0

    log_message = log_messages[0]
    # Verify log contains required fields (AC10)
    assert str(admin_user.id) in log_message
    assert admin_user.email in log_message
    assert str(target_user.id) in log_message
    assert target_user.email in log_message
    assert "educator" in log_message  # old role
    assert "admin" in log_message  # new role


def test_cleanup_sessions_admin_success(db_session: Session, admin_user_with_session):
    """AC9: POST /api/admin/cleanup-sessions works for admin users."""
    admin_user, admin_session = admin_user_with_session

    # Create expired session
    expired_session = UserSession(
        user_id=admin_user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        created_at=datetime.now(timezone.utc) - timedelta(hours=25),
        last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    db_session.add(expired_session)
    db_session.commit()

    # Make request as admin
    response = client.post(
        "/api/admin/cleanup-sessions",
        cookies={"plc_session": str(admin_session.id)}
    )

    # Assert response
    assert response.status_code == 200
    data = response.json()
    assert "sessions_deleted" in data
    assert data["sessions_deleted"] >= 1  # At least the expired session


def test_cleanup_sessions_forbidden_for_non_admin(db_session: Session, educator_user_with_session):
    """AC9: POST /api/admin/cleanup-sessions returns 403 for non-admin users."""
    educator_user, educator_session = educator_user_with_session

    # Make request as educator
    response = client.post(
        "/api/admin/cleanup-sessions",
        cookies={"plc_session": str(educator_session.id)}
    )

    # Assert 403 Forbidden
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]
