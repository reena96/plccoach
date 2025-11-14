"""Authentication service for OAuth and session management."""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.session import Session as UserSession

logger = logging.getLogger(__name__)


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
    now = datetime.now(timezone.utc)
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

    # Log session creation for audit trail (AC6)
    logger.info(f"Session created - user_id: {user_id}, session_id: {session.id}, expires_at: {expires_at}")

    return session


def get_session_by_id(db: Session, session_id: uuid.UUID) -> Optional[UserSession]:
    """
    Retrieve session from database by session ID.

    Args:
        db: Database session
        session_id: UUID of the session

    Returns:
        UserSession or None if not found
    """
    return db.query(UserSession).filter(UserSession.id == session_id).first()


def update_session_activity(db: Session, session: UserSession) -> None:
    """
    Update session activity timestamp and potentially extend expiry.

    Args:
        db: Database session
        session: UserSession object to update
    """
    now = datetime.now(timezone.utc)
    session.last_accessed_at = now

    # Extend expiry if within 6 hours of expiration (AC3)
    hours_until_expiry = (session.expires_at - now).total_seconds() / 3600
    if hours_until_expiry < 6:
        session.expires_at = now + timedelta(seconds=settings.session_max_age)
        logger.info(f"Session expiry extended - session_id: {session.id}, new_expires_at: {session.expires_at}")

    db.commit()

    # Log session refresh (AC6)
    logger.info(f"Session activity updated - session_id: {session.id}, user_id: {session.user_id}, last_accessed_at: {now}")


def delete_session(db: Session, session_id: uuid.UUID) -> bool:
    """
    Delete session from database (logout).

    Args:
        db: Database session
        session_id: UUID of the session to delete

    Returns:
        bool: True if session was deleted, False if not found
    """
    session = get_session_by_id(db, session_id)
    if session:
        user_id = session.user_id
        db.delete(session)
        db.commit()

        # Log session deletion for audit trail (AC6)
        logger.info(f"Session deleted (logout) - session_id: {session_id}, user_id: {user_id}")
        return True

    return False


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """
    Retrieve user from database by user ID.

    Args:
        db: Database session
        user_id: UUID of the user

    Returns:
        User or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session, offset: int, limit: int) -> list[User]:
    """
    List users from database with pagination.

    Args:
        db: Database session
        offset: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of User objects ordered by created_at descending
    """
    return db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()


def update_user_role(db: Session, user_id: uuid.UUID, new_role: str) -> Optional[User]:
    """
    Update user's role in database.

    Args:
        db: Database session
        user_id: UUID of the user
        new_role: New role value ("educator", "coach", or "admin")

    Returns:
        Updated User object or None if not found
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user
    return None
