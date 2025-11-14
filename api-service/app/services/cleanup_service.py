"""Background cleanup service for expired sessions."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.session import Session as UserSession

logger = logging.getLogger(__name__)


def delete_expired_sessions(db: Session) -> int:
    """
    Delete all expired sessions from the database.

    AC5: Background Session Cleanup
    - Deletes sessions where expires_at < current time
    - Logs cleanup results

    Args:
        db: Database session

    Returns:
        int: Number of sessions deleted
    """
    now = datetime.now(timezone.utc)

    # Query expired sessions
    expired_sessions = db.query(UserSession).filter(
        UserSession.expires_at < now
    ).all()

    count = len(expired_sessions)

    # Delete expired sessions
    for session in expired_sessions:
        db.delete(session)

    db.commit()

    # Log cleanup results (AC5, AC6)
    logger.info(f"Session cleanup completed - deleted {count} expired sessions at {now}")

    return count
