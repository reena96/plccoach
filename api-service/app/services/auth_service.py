"""Authentication service for OAuth and session management."""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.session import Session as UserSession


# Initialize OAuth client
oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Register Clever OAuth
oauth.register(
    name='clever',
    client_id=settings.clever_client_id,
    client_secret=settings.clever_client_secret,
    server_metadata_url='https://clever.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


def get_or_create_user(
    db: Session,
    email: str,
    name: str,
    sso_provider: str,
    sso_id: str,
    role: Optional[str] = None,
    organization_id: Optional[uuid.UUID] = None
) -> User:
    """
    Get existing user or create new user from SSO data (JIT provisioning).

    Args:
        db: Database session
        email: User email from SSO provider
        name: User full name from SSO provider
        sso_provider: SSO provider name (e.g., 'google', 'clever')
        sso_id: Unique user ID from SSO provider
        role: User role (optional, defaults to 'educator')
        organization_id: Organization ID (optional, for Clever district mapping)

    Returns:
        User: Created or existing user record
    """
    # Try to find existing user by SSO provider and SSO ID
    user = db.query(User).filter(
        User.sso_provider == sso_provider,
        User.sso_id == sso_id
    ).first()

    if user:
        # Update existing user's last_login and profile info (in case it changed)
        user.last_login = datetime.utcnow()
        user.email = email  # Update email if changed
        user.name = name    # Update name if changed
        if role:
            user.role = role  # Update role if provided
        if organization_id:
            user.organization_id = organization_id  # Update organization if provided
        db.commit()
        db.refresh(user)
        return user

    # Create new user (JIT provisioning)
    new_user = User(
        email=email,
        name=name,
        role=role or 'educator',  # Use provided role or default to 'educator'
        sso_provider=sso_provider,
        sso_id=sso_id,
        organization_id=organization_id,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_session(db: Session, user_id: uuid.UUID) -> UserSession:
    """
    Create new session for user with 24-hour expiry.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        UserSession: Created session record
    """
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=settings.session_max_age)

    session = UserSession(
        user_id=user_id,
        expires_at=expires_at,
        created_at=now,
        last_accessed_at=now
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session
