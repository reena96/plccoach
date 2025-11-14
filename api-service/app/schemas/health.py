"""Health check response schemas."""
from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: Optional[str] = None
    version: Optional[str] = None
    database: Optional[str] = None


class HealthStatus(BaseModel):
    """Detailed health status."""
    healthy: bool
    database_connected: bool
    message: Optional[str] = None
