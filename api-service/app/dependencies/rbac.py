"""Role-Based Access Control (RBAC) dependencies for admin endpoints."""
import logging
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.session import get_current_session
from app.models.session import Session as UserSession
from app.services.database import get_db
from app.services.auth_service import get_user_by_id

logger = logging.getLogger(__name__)


async def require_admin(
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db)
) -> UserSession:
    """
    Require admin role for endpoint access.

    This dependency validates that the authenticated user has admin privileges.
    It builds on top of get_current_session() to ensure session is valid first.

    Args:
        session: Valid user session (from get_current_session dependency)
        db: Database session

    Raises:
        HTTPException: 403 Forbidden if user is not admin

    Returns:
        UserSession: Valid session object (for downstream use)
    """
    # Get user from session
    user = get_user_by_id(db, session.user_id)

    if not user:
        logger.warning(f"RBAC check failed: User not found for session {session.id}")
        raise HTTPException(status_code=403, detail="Admin privileges required")

    # Check if user has admin role
    if user.role != "admin":
        logger.warning(f"RBAC check failed: User {user.id} ({user.email}) has role '{user.role}', not 'admin'")
        raise HTTPException(status_code=403, detail="Admin privileges required")

    logger.info(f"RBAC check passed: Admin user {user.id} ({user.email}) accessing protected endpoint")
    return session
