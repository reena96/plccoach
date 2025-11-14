"""Structured logging middleware."""
import json
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.config import settings

# Configure JSON logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging of requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response in JSON format.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler
        """
        start_time = time.time()

        # Get request ID from state (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request
        request_log = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
        }
        logger.info(json.dumps(request_log))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        response_log = {
            "event": "response",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        logger.info(json.dumps(response_log))

        return response
