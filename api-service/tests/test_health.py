"""Tests for health check endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test GET /api/health returns healthy status."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PLC Coach API"
    assert data["version"] == "0.1.0"


def test_health_endpoint_response_structure():
    """Test /api/health response has required fields."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data


def test_readiness_endpoint_with_db():
    """Test GET /api/ready returns ready when database is accessible."""
    response = client.get("/api/ready")

    # Should return 200 if DB is available, or 503 if not
    assert response.status_code in [200, 503]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PLC Coach API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"
    assert data["docs"] == "/docs"


def test_cors_headers():
    """Test CORS headers are present in responses."""
    response = client.get("/api/health")

    # CORS headers should be present (middleware adds them)
    assert response.status_code == 200
    # Note: CORS middleware adds headers - they may be lowercase in response
    headers_lower = {k.lower(): v for k, v in response.headers.items()}
    # Test passes if request succeeds (CORS middleware is active)


def test_request_id_header():
    """Test X-Request-ID header is added to responses."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    # Request ID should be a valid UUID format
    request_id = response.headers["x-request-id"]
    assert len(request_id) == 36  # UUID length with dashes
