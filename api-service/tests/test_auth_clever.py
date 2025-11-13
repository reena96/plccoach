"""Tests for Clever OAuth authentication flow."""
import pytest
import uuid
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use PostgreSQL test database (defined in .env)
os.environ['DATABASE_URL'] = os.getenv('TEST_DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@db:5432/plccoach_test')

from app.main import app
from app.services.database import Base, get_db, engine as default_engine
from app.models.user import User
from app.models.session import Session as UserSession


# Use the existing test database engine
engine = default_engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


# Test 1: Clever login initiation
def test_clever_login_redirects_to_clever():
    """Test that /auth/clever/login redirects to Clever OAuth consent screen."""
    with patch('app.routers.auth.oauth.clever.authorize_redirect') as mock_authorize:
        # Mock the authorize_redirect response
        mock_response = MagicMock()
        mock_response.headers = {'location': 'https://clever.com/oauth/authorize?state=test-state&scope=openid+email+profile'}
        mock_authorize.return_value = mock_response

        response = client.get("/auth/clever/login", follow_redirects=False)

        assert response.status_code == 307  # Redirect status
        assert 'clever.com' in response.headers['location']
        assert 'oauth_state' in response.cookies


def test_clever_login_sets_state_cookie():
    """Test that state parameter is stored in httpOnly cookie."""
    with patch('app.routers.auth.oauth.clever.authorize_redirect') as mock_authorize:
        mock_response = MagicMock()
        mock_response.headers = {'location': 'https://clever.com/oauth/authorize?state=test'}
        mock_authorize.return_value = mock_response

        response = client.get("/auth/clever/login", follow_redirects=False)

        # Verify state cookie attributes
        assert 'oauth_state' in response.cookies


# Test 2: OAuth callback - state validation
def test_callback_rejects_missing_state():
    """Test callback rejects request without state parameter."""
    response = client.get("/auth/clever/callback?code=test-code")
    assert response.status_code == 403
    assert "Invalid state parameter" in response.json()['detail']


def test_callback_rejects_mismatched_state():
    """Test callback rejects request with mismatched state."""
    # Set state cookie
    client.cookies.set('oauth_state', 'cookie-state')

    # Send different state in query param
    response = client.get("/auth/clever/callback?code=test-code&state=different-state")
    assert response.status_code == 403
    assert "Invalid state parameter" in response.json()['detail']


# Test 3: OAuth callback - successful authentication (new teacher user)
def test_callback_creates_new_teacher_user(db_session):
    """Test callback creates new teacher user with JIT provisioning."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # Mock Clever OAuth token response for teacher
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-123',
                'email': 'teacher@example.com',
                'name': 'Jane Teacher',
                'type': 'teacher'
            }
        }

        # Set state cookie
        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302
        assert response.headers['location'] == '/dashboard'
        assert 'plc_session' in response.cookies

        # Verify user was created in database with 'educator' role
        user = db_session.query(User).filter(User.email == 'teacher@example.com').first()
        assert user is not None
        assert user.name == 'Jane Teacher'
        assert user.role == 'educator'  # teacher → educator
        assert user.sso_provider == 'clever'
        assert user.sso_id == 'clever-user-123'
        assert user.last_login is not None


# Test 4: Role mapping - district admin → admin
def test_callback_maps_district_admin_to_admin_role(db_session):
    """Test callback maps Clever district_admin to 'admin' role."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # Mock Clever OAuth token response for district admin
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-admin-456',
                'email': 'admin@district.edu',
                'name': 'District Admin',
                'type': 'district_admin'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify user was created with 'admin' role
        user = db_session.query(User).filter(User.email == 'admin@district.edu').first()
        assert user is not None
        assert user.role == 'admin'
        assert user.sso_provider == 'clever'


# Test 5: Role mapping - school admin → admin
def test_callback_maps_school_admin_to_admin_role(db_session):
    """Test callback maps Clever school_admin to 'admin' role."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # Mock Clever OAuth token response for school admin
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-school-admin-789',
                'email': 'principal@school.edu',
                'name': 'School Principal',
                'type': 'school_admin'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify user was created with 'admin' role
        user = db_session.query(User).filter(User.email == 'principal@school.edu').first()
        assert user is not None
        assert user.role == 'admin'


# Test 6: Organization ID extraction
def test_callback_extracts_organization_id(db_session):
    """Test callback extracts organization_id from Clever district data."""
    state = str(uuid.uuid4())
    district_uuid = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # Mock Clever OAuth token response with district ID
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-999',
                'email': 'teacher@district.edu',
                'name': 'District Teacher',
                'type': 'teacher',
                'district': district_uuid
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify organization_id was set
        user = db_session.query(User).filter(User.email == 'teacher@district.edu').first()
        assert user is not None
        assert user.organization_id is not None
        assert str(user.organization_id) == district_uuid


# Test 7: Organization ID - invalid format handled gracefully
def test_callback_handles_invalid_organization_id(db_session):
    """Test callback handles invalid district ID gracefully."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # Mock Clever OAuth token response with invalid district ID
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-888',
                'email': 'teacher2@district.edu',
                'name': 'Another Teacher',
                'type': 'teacher',
                'district': 'not-a-uuid'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify user was created without organization_id
        user = db_session.query(User).filter(User.email == 'teacher2@district.edu').first()
        assert user is not None
        assert user.organization_id is None


# Test 8: OAuth callback - existing user login
def test_callback_updates_existing_user(db_session):
    """Test callback updates last_login and role for existing user."""
    # Create existing user as teacher
    existing_user = User(
        email='teacher@example.com',
        name='Jane Teacher',
        role='educator',
        sso_provider='clever',
        sso_id='clever-user-123',
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow() - timedelta(days=1)
    )
    db_session.add(existing_user)
    db_session.commit()

    old_last_login = existing_user.last_login

    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        # User promoted to district admin
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-123',
                'email': 'teacher@example.com',
                'name': 'Jane Admin',  # Name changed
                'type': 'district_admin'  # Promoted to admin
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify user was updated (not duplicated)
        db_session.expire_all()  # Refresh all objects from database
        users = db_session.query(User).filter(User.email == 'teacher@example.com').all()
        assert len(users) == 1

        user = users[0]
        assert user.name == 'Jane Admin'  # Name updated
        assert user.role == 'admin'  # Role updated
        assert user.last_login > old_last_login  # last_login updated


# Test 9: Session creation
def test_callback_creates_session(db_session):
    """Test callback creates session with correct expiry."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-456',
                'email': 'coach@example.com',
                'name': 'John Coach',
                'type': 'teacher'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify session was created
        session = db_session.query(UserSession).first()
        assert session is not None
        assert session.user_id is not None

        # Verify session expires in ~24 hours (allow 10 second variance)
        # Note: session.expires_at is timezone-aware, so we need to compare with timezone-aware datetime
        from datetime import timezone
        expected_expiry = datetime.now(timezone.utc) + timedelta(seconds=86400)
        # Convert to naive UTC for comparison
        expires_naive = session.expires_at.replace(tzinfo=None) if session.expires_at.tzinfo else session.expires_at
        expected_naive = expected_expiry.replace(tzinfo=None) if expected_expiry.tzinfo else expected_expiry
        assert abs((expires_naive - expected_naive).total_seconds()) < 10


# Test 10: Cookie attributes
def test_callback_sets_session_cookie_attributes(db_session):
    """Test session cookie has correct security attributes."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-789',
                'email': 'admin@example.com',
                'name': 'Admin User',
                'type': 'district_admin'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302
        assert 'plc_session' in response.cookies


# Test 11: Error handling - token exchange failure
def test_callback_handles_token_exchange_failure():
    """Test callback handles failure to exchange authorization code."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.side_effect = Exception("Token exchange failed")

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/clever/callback?code=invalid-code&state={state}")

        assert response.status_code == 401
        assert "Authentication failed" in response.json()['detail']


# Test 12: Error handling - missing user info
def test_callback_handles_missing_userinfo():
    """Test callback handles missing user info in token response."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token'
            # Missing 'userinfo' key
        }

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/clever/callback?code=test-code&state={state}")

        assert response.status_code == 401
        # Generic error message for security (actual error logged server-side)
        assert "Authentication failed" in response.json()['detail']


# Test 13: Error handling - incomplete user info
def test_callback_handles_incomplete_userinfo():
    """Test callback handles incomplete user info (missing email or sub)."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'name': 'User Without Email',
                'type': 'teacher'
                # Missing 'email' and 'sub'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/clever/callback?code=test-code&state={state}")

        assert response.status_code == 401
        # Generic error message for security (actual error logged server-side)
        assert "Authentication failed" in response.json()['detail']


# Test 14: State cookie is deleted after callback
def test_callback_deletes_state_cookie(db_session):
    """Test that state cookie is deleted after successful callback."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.clever.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'clever-user-999',
                'email': 'test@example.com',
                'name': 'Test User',
                'type': 'teacher'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/clever/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302


# Clean up test client cookies after all tests
@pytest.fixture(autouse=True)
def clear_cookies():
    """Clear test client cookies between tests."""
    yield
    client.cookies.clear()
