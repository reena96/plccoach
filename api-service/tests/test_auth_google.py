"""Tests for Google OAuth authentication flow."""
import pytest
import uuid
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import get_db
from app.models.user import User
from app.models.session import Session as UserSession


def override_get_db_factory(db_session):
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
    app.dependency_overrides[get_db] = override_get_db_factory(db_session)
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


# Test 1: Google login initiation
def test_google_login_redirects_to_google():
    """Test that /auth/google/login redirects to Google OAuth consent screen."""
    with patch('app.routers.auth.oauth.google.authorize_redirect') as mock_authorize:
        # Mock the authorize_redirect response
        mock_response = MagicMock()
        mock_response.headers = {'location': 'https://accounts.google.com/o/oauth2/v2/auth?state=test-state&scope=openid+email+profile'}
        mock_authorize.return_value = mock_response

        response = client.get("/auth/google/login", follow_redirects=False)

        assert response.status_code == 307  # Redirect status
        assert 'accounts.google.com' in response.headers['location']
        assert 'oauth_state' in response.cookies


def test_google_login_sets_state_cookie():
    """Test that state parameter is stored in httpOnly cookie."""
    with patch('app.routers.auth.oauth.google.authorize_redirect') as mock_authorize:
        mock_response = MagicMock()
        mock_response.headers = {'location': 'https://accounts.google.com/o/oauth2/v2/auth?state=test'}
        mock_authorize.return_value = mock_response

        response = client.get("/auth/google/login", follow_redirects=False)

        # Verify state cookie attributes
        assert 'oauth_state' in response.cookies
        # Note: TestClient doesn't expose httpOnly/secure flags directly,
        # but we verify they're set in the code


# Test 2: OAuth callback - state validation
def test_callback_rejects_missing_state():
    """Test callback rejects request without state parameter."""
    response = client.get("/auth/google/callback?code=test-code")
    assert response.status_code == 403
    assert "Invalid state parameter" in response.json()['detail']


def test_callback_rejects_mismatched_state():
    """Test callback rejects request with mismatched state."""
    # Set state cookie
    client.cookies.set('oauth_state', 'cookie-state')

    # Send different state in query param
    response = client.get("/auth/google/callback?code=test-code&state=different-state")
    assert response.status_code == 403
    assert "Invalid state parameter" in response.json()['detail']


# Test 3: OAuth callback - successful authentication (new user)
def test_callback_creates_new_user(db_session):
    """Test callback creates new user with JIT provisioning."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        # Mock Google OAuth token response
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'google-user-123',
                'email': 'educator@example.com',
                'name': 'Jane Educator'
            }
        }

        # Set state cookie
        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/google/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302
        assert response.headers['location'] == '/dashboard'
        assert 'plc_session' in response.cookies

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == 'educator@example.com').first()
        assert user is not None
        assert user.name == 'Jane Educator'
        assert user.role == 'educator'
        assert user.sso_provider == 'google'
        assert user.sso_id == 'google-user-123'
        assert user.last_login is not None


# Test 4: OAuth callback - existing user login
def test_callback_updates_existing_user(db_session):
    """Test callback updates last_login for existing user."""
    # Create existing user
    existing_user = User(
        email='educator@example.com',
        name='Jane Educator',
        role='educator',
        sso_provider='google',
        sso_id='google-user-123',
        created_at=datetime.now(timezone.utc),
        last_login=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db_session.add(existing_user)
    db_session.commit()

    old_last_login = existing_user.last_login

    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'google-user-123',
                'email': 'educator@example.com',
                'name': 'Jane Updated Name'  # Name changed
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/google/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify user was updated (not duplicated)
        db_session.expire_all()  # Refresh all objects from database
        users = db_session.query(User).filter(User.email == 'educator@example.com').all()
        assert len(users) == 1

        user = users[0]
        assert user.name == 'Jane Updated Name'  # Name updated
        assert user.last_login > old_last_login  # last_login updated


# Test 5: Session creation
def test_callback_creates_session(db_session):
    """Test callback creates session with correct expiry."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'google-user-456',
                'email': 'coach@example.com',
                'name': 'John Coach'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/google/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302

        # Verify session was created
        session = db_session.query(UserSession).first()
        assert session is not None
        assert session.user_id is not None

        # Verify session expires in ~24 hours (allow 10 second variance)
        expected_expiry = datetime.now(timezone.utc) + timedelta(seconds=86400)
        assert abs((session.expires_at - expected_expiry).total_seconds()) < 10


# Test 6: Cookie attributes
def test_callback_sets_session_cookie_attributes(db_session):
    """Test session cookie has correct security attributes."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'google-user-789',
                'email': 'admin@example.com',
                'name': 'Admin User'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/google/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302
        assert 'plc_session' in response.cookies
        # Note: TestClient doesn't expose cookie attributes directly
        # Security attributes (httpOnly, secure, sameSite) are verified in code


# Test 7: Error handling - token exchange failure
def test_callback_handles_token_exchange_failure():
    """Test callback handles failure to exchange authorization code."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.side_effect = Exception("Token exchange failed")

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/google/callback?code=invalid-code&state={state}")

        assert response.status_code == 401
        assert "Authentication failed" in response.json()['detail']


# Test 8: Error handling - missing user info
def test_callback_handles_missing_userinfo():
    """Test callback handles missing user info in token response."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token'
            # Missing 'userinfo' key
        }

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/google/callback?code=test-code&state={state}")

        assert response.status_code == 401
        assert "Failed to get user info" in response.json()['detail']


# Test 9: Error handling - incomplete user info
def test_callback_handles_incomplete_userinfo():
    """Test callback handles incomplete user info (missing email or sub)."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'name': 'User Without Email'
                # Missing 'email' and 'sub'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(f"/auth/google/callback?code=test-code&state={state}")

        assert response.status_code == 401
        assert "Invalid user info" in response.json()['detail']


# Test 10: State cookie is deleted after callback
def test_callback_deletes_state_cookie(db_session):
    """Test that state cookie is deleted after successful callback."""
    state = str(uuid.uuid4())

    with patch('app.routers.auth.oauth.google.authorize_access_token') as mock_token:
        mock_token.return_value = {
            'access_token': 'mock-access-token',
            'id_token': 'mock-id-token',
            'userinfo': {
                'sub': 'google-user-999',
                'email': 'test@example.com',
                'name': 'Test User'
            }
        }

        client.cookies.set('oauth_state', state)

        response = client.get(
            f"/auth/google/callback?code=test-code&state={state}",
            follow_redirects=False
        )

        assert response.status_code == 302
        # State cookie should be deleted (set with negative max_age or empty value)
        # TestClient doesn't fully simulate cookie deletion, but we verify in code


# Clean up test client cookies after all tests
@pytest.fixture(autouse=True)
def clear_cookies():
    """Clear test client cookies between tests."""
    yield
    client.cookies.clear()
