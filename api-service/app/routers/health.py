"""Health check endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.database import get_db
from app.services.cleanup_service import delete_expired_sessions
from app.dependencies.rbac import require_admin
from app.models.session import Session as UserSession
from app.schemas.health import HealthResponse
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check - service is running.

    Returns:
        HealthResponse with service status, name, and version
    """
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - can connect to database.

    Args:
        db: Database session dependency

    Returns:
        HealthResponse with database connection status

    Raises:
        HTTPException: 503 if database is not available
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return HealthResponse(
            status="ready",
            database="connected"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database not available: {str(e)}"
        )


@router.post("/admin/cleanup-sessions")
async def manual_session_cleanup(
    session: UserSession = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Manually trigger expired session cleanup (admin only).

    **AC9: Role-Based Access Control**
    - Admin-only endpoint (enforced by require_admin dependency)
    - Returns 403 for non-admin users

    **AC5: Background Session Cleanup**
    - Deletes all expired sessions
    - Returns count of deleted sessions

    Returns:
        dict: Number of sessions deleted and status message
    """
    count = delete_expired_sessions(db)
    return {
        "status": "completed",
        "sessions_deleted": count,
        "message": f"Successfully deleted {count} expired sessions"
    }
