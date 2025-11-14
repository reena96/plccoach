"""Session validation dependency for protected endpoints."""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.database import get_db
from app.services.auth_service import get_session_by_id, update_session_activity
from app.config import settings
from app.models.session import Session as UserSession

logger = logging.getLogger(__name__)


async def get_current_session(
    request: Request,
    db: Session = Depends(get_db)
) -> UserSession:
    """
    Validate and retrieve current user session from cookie.

    This dependency implements AC2, AC3, and AC4:
    - AC2: Checks inactivity timeout (30 minutes)
    - AC3: Updates last_accessed_at and extends expiry
    - AC4: Validates session exists, not expired, within activity window

    Raises:
        HTTPException: 401 Unauthorized if session is invalid/expired

    Returns:
        UserSession: Valid, refreshed session object
    """
    # Extract session ID from cookie
    session_cookie = request.cookies.get(settings.session_cookie_name)

    if not session_cookie:
        logger.warning("Session validation failed: No session cookie present")
        raise HTTPException(status_code=401, detail="Unauthorized - No active session")

    # Parse session ID
    try:
        session_id = uuid.UUID(session_cookie)
    except (ValueError, AttributeError):
        logger.warning(f"Session validation failed: Invalid session ID format: {session_cookie}")
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid session")

    # Retrieve session from database (AC4: Check existence)
    session = get_session_by_id(db, session_id)
    if not session:
        logger.warning(f"Session validation failed: Session not found in database: {session_id}")
        raise HTTPException(status_code=401, detail="Unauthorized - Session not found")

    now = datetime.now(timezone.utc)

    # Check absolute expiry (AC4: expires_at > current time)
    if session.expires_at <= now:
        logger.info(f"Session expired (absolute expiry) - session_id: {session_id}, expired_at: {session.expires_at}")
        raise HTTPException(status_code=401, detail="Unauthorized - Session expired")

    # Check inactivity timeout (AC2, AC4: last_accessed_at within 30 minutes)
    inactivity_limit = timedelta(minutes=30)
    time_since_last_access = now - session.last_accessed_at

    if time_since_last_access > inactivity_limit:
        logger.info(f"Session expired (inactivity timeout) - session_id: {session_id}, last_accessed: {session.last_accessed_at}")
        raise HTTPException(status_code=401, detail="Unauthorized - Session expired due to inactivity")

    # Session is valid - update activity timestamp and potentially extend expiry (AC3)
    update_session_activity(db, session)

    return session


async def get_optional_session(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[UserSession]:
    """
    Get current session if valid, None otherwise.

    Useful for endpoints that work with or without authentication.
    Does not raise exception for invalid/missing sessions.

    Returns:
        UserSession or None
    """
    try:
        return await get_current_session(request, db)
    except HTTPException:
        return None
