# Story 1.3 Handoff: Backend API Service Foundation

**Story:** 1.3 - Backend API Service Foundation
**Epic:** 1 - Foundation & Authentication
**Status:** Ready to Start
**Created:** 2025-11-13
**Prerequisites:** Story 1.2 Complete ✅

---

## Quick Start

### Context
We've successfully completed Stories 1.1 (Infrastructure) and 1.2 (Database Schema). The AWS RDS PostgreSQL database is deployed with all tables, indexes, and the pgvector extension. Now we need to build the FastAPI backend service that will connect to this database and provide API endpoints.

### Goal
Create a production-ready FastAPI application with:
- Structured directory layout
- Health check endpoints
- Database connection pooling
- CORS middleware
- Structured logging
- Docker containerization

### Estimated Time
**4-6 hours** of focused development

---

## What's Already Done

### ✅ Completed (Stories 1.1 & 1.2)
- AWS infrastructure deployed (VPC, RDS, S3, ECS, etc.)
- Database schema created with all tables:
  - `users`, `sessions`, `conversations`, `messages`
  - All indexes and foreign keys
  - `pgvector` extension installed
- Alembic migrations configured and tested
- Python environment with psycopg3
- `.env` file with database connection string
- Documentation reorganized with new structure

### 📁 Current Project Structure
```
plccoach/
├── api-service/
│   ├── alembic/                    # ✅ Migration system
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── venv/                       # ✅ Virtual environment
│   ├── .env                        # ✅ Environment config
│   ├── requirements.txt            # ✅ Dependencies listed
│   ├── alembic.ini                # ✅ Alembic config
│   └── db_config.py               # ✅ Database config
└── docs/                          # ✅ New organized structure
```

---

## What Needs to Be Built (Story 1.3)

### Directory Structure to Create
```
api-service/
├── app/                           # 🆕 Main application package
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── config.py                  # Configuration management
│   │
│   ├── routers/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py              # Health check endpoints
│   │   ├── auth.py                # Authentication (placeholder)
│   │   ├── conversations.py       # Conversations (placeholder)
│   │   └── messages.py            # Messages (placeholder)
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── database.py            # DB connection & session
│   │   └── auth_service.py        # Auth logic (placeholder)
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   ├── session.py             # Session model
│   │   ├── conversation.py        # Conversation model
│   │   └── message.py             # Message model
│   │
│   ├── middleware/                # Request/response middleware
│   │   ├── __init__.py
│   │   ├── request_id.py          # Request ID tracking
│   │   └── logging.py             # Structured logging
│   │
│   └── schemas/                   # Pydantic schemas (API models)
│       ├── __init__.py
│       ├── health.py              # Health check responses
│       └── base.py                # Base schemas
│
├── tests/                         # 🆕 Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── test_health.py             # Health endpoint tests
│   └── test_database.py           # Database connection tests
│
├── Dockerfile                     # 🆕 Container definition
├── .dockerignore                  # 🆕 Docker ignore rules
└── docker-compose.yml             # 🆕 Local development setup
```

---

## Implementation Checklist

### Phase 1: Basic FastAPI Application (1-2 hours)
- [ ] Create `app/` directory structure
- [ ] Create `app/main.py` with FastAPI initialization
- [ ] Create `app/config.py` for configuration management
- [ ] Add basic CORS middleware
- [ ] Add request ID middleware
- [ ] Test: Run `uvicorn app.main:app --reload`

### Phase 2: Database Integration (1-2 hours)
- [ ] Create `app/services/database.py` with SQLAlchemy setup
- [ ] Create `app/models/` with ORM models (User, Session, Conversation, Message)
- [ ] Configure connection pooling (20 connections)
- [ ] Add database dependency injection
- [ ] Test: Connect to RDS and query tables

### Phase 3: Health Endpoints (30 min)
- [ ] Create `app/routers/health.py`
- [ ] Implement `GET /health` - basic service status
- [ ] Implement `GET /ready` - database connectivity check
- [ ] Create Pydantic schemas for responses
- [ ] Test: Curl both endpoints

### Phase 4: Structured Logging (30 min)
- [ ] Create `app/middleware/logging.py`
- [ ] Configure JSON logging format
- [ ] Add request/response logging
- [ ] Add request ID to all logs
- [ ] Test: Check log output format

### Phase 5: Docker Setup (1-2 hours)
- [ ] Create `Dockerfile` for production deployment
- [ ] Create `docker-compose.yml` with volume mounts for hot reload
- [ ] Configure environment variables for container
- [ ] Test: `docker-compose up` works with auto-reload
- [ ] Test: Can connect to RDS from container

**Note:** Docker is the PRIMARY development method:
- Same environment locally and in ECS Fargate production
- Volume mounts enable hot reload (code changes apply immediately)
- Native Python (uvicorn directly) available as backup for debugging

### Phase 6: Testing (30-45 min)
- [ ] Create basic tests in `tests/`
- [ ] Add pytest configuration
- [ ] Test: `docker-compose exec api pytest` runs tests
- [ ] Verify health endpoints work in container

### Phase 6: Documentation (30 min)
- [ ] Update `requirements.txt` with new dependencies
- [ ] Create API documentation in `docs/06-api/`
- [ ] Create runbook for running the service
- [ ] Update Story 1.3 status

---

## Technical Requirements

### Dependencies to Add
```python
# FastAPI and server
fastapi==0.109.0          # Already in requirements.txt
uvicorn[standard]==0.27.0  # Already in requirements.txt
pydantic==2.5.3           # Already in requirements.txt
pydantic-settings==2.1.0   # Already in requirements.txt

# Database (already have)
SQLAlchemy==2.0.44
psycopg[binary]==3.2.12
alembic==1.17.1

# New additions needed:
python-multipart==0.0.6   # For form data
python-jose[cryptography]==3.3.0  # For JWT (future)
passlib[bcrypt]==1.7.4    # For password hashing (future)
```

### Environment Variables
```bash
# Database (already in .env)
DATABASE_URL="postgresql+psycopg://..."

# Application (to add)
APP_NAME="PLC Coach API"
APP_VERSION="0.1.0"
ENVIRONMENT="development"
LOG_LEVEL="INFO"
CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

# AWS (already available)
AWS_REGION="us-east-1"
DB_SECRET_NAME="plccoach-db-password"
```

---

## Acceptance Criteria (from Epic)

### Must Have (Story 1.3)
✅ **AC1:** Directory structure matches specification
✅ **AC2:** Health endpoints implemented and working
- `GET /health` returns 200 with service status
- `GET /ready` returns 200 when DB connected, 503 otherwise

✅ **AC3:** Database connection pooling configured
- SQLAlchemy engine with pool_size=20
- Connection validation on checkout

✅ **AC4:** CORS middleware configured
- Allow frontend origins
- Proper headers set

✅ **AC5:** Structured logging implemented
- JSON format
- Request ID tracking
- CloudWatch compatible

✅ **AC6:** Docker container builds and runs
- Dockerfile creates working image
- Container can connect to RDS
- Health checks pass

✅ **AC7:** Environment variables from .env
- Config loads from environment
- Secrets not hardcoded

---

## Key Decisions & Patterns

### Application Structure
```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health
from app.middleware.request_id import RequestIDMiddleware

app = FastAPI(
    title="PLC Coach API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix="/api", tags=["health"])
```

### Database Session Management
```python
# app/services/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Validate connections
    echo=False
)

SessionLocal = sessionmaker(bind=engine)

def get_db() -> Session:
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Health Check Implementation
```python
# app/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check - service is running"""
    return {
        "status": "healthy",
        "service": "plccoach-api",
        "version": "0.1.0"
    }

@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check - can connect to database"""
    try:
        db.execute("SELECT 1")
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_readiness_check():
    response = client.get("/api/ready")
    assert response.status_code in [200, 503]
```

### Manual Testing

**Recommended: Using Docker**
```bash
# Start services (with hot reload)
docker-compose up

# In another terminal:
# Test health endpoint
curl http://localhost:8000/api/health

# Test readiness endpoint
curl http://localhost:8000/api/ready

# Check OpenAPI docs
open http://localhost:8000/docs

# Run tests in container
docker-compose exec api pytest -v

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

**Alternative: Direct Python (for debugging)**
```bash
# If you need to debug without Docker
source venv/bin/activate
source .env
uvicorn app.main:app --reload --port 8000
```

---

## Common Issues & Solutions

### Issue: Import errors with psycopg
**Solution:** Make sure using `psycopg` not `psycopg2` in DATABASE_URL

### Issue: Database connection timeout
**Solution:** Check `.env` file is loaded, verify RDS security group allows access

### Issue: CORS errors in browser
**Solution:** Configure proper origins in CORS middleware, don't use `*` in production

### Issue: Docker can't connect to RDS
**Solution:** Docker needs to use host network or proper networking setup

---

## Resources & References

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### Project Documents
- [Story 1.3 Details](../02-planning/stories/1-3-backend-api-foundation.md) (to be created)
- [Technical Architecture](../01-project/TECHNICAL_ARCHITECTURE.md)
- [Database Schema](../02-planning/stories/1-2-database-schema-creation.md)

### Code Examples
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Project Structure](https://github.com/tiangolo/full-stack-fastapi-postgresql)

---

## Success Criteria

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Health endpoints return correct responses
- [ ] Database connection working
- [ ] CORS configured
- [ ] Logging outputs JSON format
- [ ] Docker container builds successfully
- [ ] Basic tests pass
- [ ] Documentation updated
- [ ] Code committed to git

### Demo Script
```bash
# 1. Start services with Docker
cd api-service
docker-compose up -d

# 2. Check services are running
docker-compose ps

# 3. Test health endpoint
curl http://localhost:8000/api/health
# Expected: {"status": "healthy", "service": "plccoach-api", "version": "0.1.0"}

# 4. Test readiness endpoint
curl http://localhost:8000/api/ready
# Expected: {"status": "ready", "database": "connected"}

# 5. View API docs
open http://localhost:8000/docs

# 6. Run tests in container
docker-compose exec api pytest -v

# 7. View logs
docker-compose logs -f api

# 8. Test hot reload - edit app/main.py and see changes apply automatically

# 9. Stop services
docker-compose down

# 10. Production build test
docker build -t plccoach-api:latest .
docker run -p 8000:8000 --env-file .env plccoach-api:latest
```

---

## Next Steps After 1.3

### Story 1.4: Google OIDC Authentication
- Implement OAuth 2.0 flow
- Add auth endpoints
- Create session management
- JIT user provisioning

### Story 1.5: Clever SSO Authentication
- Similar to Google but with Clever
- Role mapping from Clever data
- Organization extraction

---

## Questions & Blockers

### Before Starting
- [ ] Is RDS publicly accessible? (Yes, temporarily)
- [ ] Do we have `.env` file? (Yes, configured in 1.2)
- [ ] Is venv activated? (Should be)
- [ ] Can we connect to RDS? (Yes, verified in 1.2)

### During Development
- Stuck? Check the [troubleshooting guide](../05-operations/troubleshooting/common-issues.md)
- Need help? Review [architecture docs](../01-project/TECHNICAL_ARCHITECTURE.md)
- API questions? Check [FastAPI docs](https://fastapi.tiangolo.com/)

---

## Handoff Complete

**Ready to start Story 1.3!** 🚀

Use the resume prompt below to get started.
