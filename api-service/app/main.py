"""FastAPI application initialization."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.logging import LoggingMiddleware
from app.routers import health, auth, admin, coach
from app.services.database import SessionLocal
from app.services.cleanup_service import delete_expired_sessions

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


def run_session_cleanup():
    """
    Background job to delete expired sessions.
    Runs daily at configured hour (default: 2 AM UTC).
    """
    db = SessionLocal()
    try:
        count = delete_expired_sessions(db)
        logger.info(f"Background session cleanup completed: {count} sessions deleted")
    except Exception as e:
        logger.error(f"Background session cleanup failed: {str(e)}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Starts background scheduler on startup, stops on shutdown.
    """
    # Startup: Initialize background scheduler
    logger.info("Starting background session cleanup scheduler")
    scheduler.add_job(
        run_session_cleanup,
        trigger=CronTrigger(hour=settings.cleanup_schedule_hour, minute=0),
        id="session_cleanup",
        name="Daily session cleanup",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Session cleanup scheduled daily at {settings.cleanup_schedule_hour}:00 UTC")

    yield

    # Shutdown: Stop scheduler
    logger.info("Stopping background scheduler")
    scheduler.shutdown()


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    description="AI-Powered PLC at Work Virtual Coach API",
    lifespan=lifespan  # Add lifespan handler for scheduler
)

# Add middleware (order matters - first added = outermost layer)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# SessionMiddleware for OAuth state storage (required by authlib)
# Must be added after CORS to access session in auth endpoints
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key or "dev-secret-key-change-in-production",
    session_cookie="oauth_session",
    max_age=600,  # OAuth state expires in 10 minutes
    same_site="lax",
    https_only=settings.environment == "production"
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(coach.router, tags=["coach"])  # Epic 2: AI Coach endpoint


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }
