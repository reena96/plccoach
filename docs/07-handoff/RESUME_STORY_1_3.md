# Resume Prompt for Story 1.3

**Copy and paste this prompt when you're ready to start Story 1.3**

---

## 📋 Resume Prompt

```
I'm ready to start Story 1.3: Backend API Service Foundation for the PLC Coach project.

CONTEXT:
- Story 1.1 (Infrastructure) ✅ Complete
- Story 1.2 (Database Schema) ✅ Complete
- AWS RDS PostgreSQL deployed with all tables
- Database connection working from local machine
- Python 3.14 environment with psycopg3
- Documentation reorganized with new structure

CURRENT STATE:
- Working directory: /Users/reena/plccoach/api-service
- Virtual environment: venv/ (activated)
- Database config: .env file with DATABASE_URL
- Git branch: epic-1-foundation-authentication
- Recent commit: ab819be (Story 1.2 complete)

STORY 1.3 GOAL:
Create a FastAPI backend service with:
1. Structured application layout (app/ directory)
2. Health check endpoints (/health and /ready)
3. Database connection pooling with SQLAlchemy
4. CORS middleware for frontend
5. Structured JSON logging
6. Docker containerization
7. Basic test suite

HANDOFF DOCUMENT:
Please read: docs/07-handoff/story-1-3-backend-api-foundation.md

ACCEPTANCE CRITERIA:
- Directory structure matches specification
- GET /api/health returns service status
- GET /api/ready checks database connectivity
- SQLAlchemy connection pooling configured (20 connections)
- CORS middleware configured
- JSON structured logging implemented
- Docker container builds and runs
- Basic pytest tests pass

TECHNICAL STACK:
- FastAPI 0.109.0
- SQLAlchemy 2.0.44
- Psycopg 3.2.12
- Uvicorn with standard extras
- Pydantic for schemas

Please help me implement Story 1.3 by:
1. Reviewing the handoff document
2. Creating the directory structure
3. Implementing the components step by step
4. Testing as we go
5. Creating Docker configuration
6. Writing basic tests
7. Updating documentation

Let's start with Phase 1: Basic FastAPI Application setup.
```

---

## 🔍 Quick Reference

### File Locations
- **Handoff Doc:** `docs/07-handoff/story-1-3-backend-api-foundation.md`
- **Epic Doc:** `docs/02-planning/epics/epic-1-foundation-authentication.md`
- **Story Doc:** `docs/02-planning/stories/1-3-backend-api-foundation.md` (to be created)
- **Working Dir:** `/Users/reena/plccoach/api-service`

### Environment Setup
```bash
cd /Users/reena/plccoach/api-service
source venv/bin/activate
source .env
```

### Key Commands
```bash
# Run development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Build Docker image
docker build -t plccoach-api:latest .

# Check database connection
python3 -c "from dotenv import load_dotenv; load_dotenv(); from sqlalchemy import create_engine, text; import os; engine = create_engine(os.environ['DATABASE_URL']); print('✅ Connected!' if engine.connect() else '❌ Failed')"
```

### Database Connection
```
Host: plccoach-db.crws0amqe1e3.us-east-1.rds.amazonaws.com
Port: 5432
Database: plccoach
User: plccoach_admin
Connection String: In .env file
```

---

## 📊 Implementation Phases

### Phase 1: Basic FastAPI App (30-45 min)
- [ ] Create app/ directory structure
- [ ] Create app/main.py with FastAPI init
- [ ] Create app/config.py
- [ ] Add CORS middleware
- [ ] Test: Run server

### Phase 2: Database Integration (45-60 min)
- [ ] Create app/services/database.py
- [ ] Create app/models/ (User, Session, Conversation, Message)
- [ ] Configure connection pooling
- [ ] Test: Query database

### Phase 3: Health Endpoints (20-30 min)
- [ ] Create app/routers/health.py
- [ ] Implement /health and /ready
- [ ] Create Pydantic schemas
- [ ] Test: Curl endpoints

### Phase 4: Structured Logging (20-30 min)
- [ ] Create app/middleware/logging.py
- [ ] Configure JSON logging
- [ ] Add request ID tracking
- [ ] Test: Check logs

### Phase 5: Docker & Tests (45-60 min)
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Write basic tests
- [ ] Test: Build and run

### Phase 6: Documentation (15-20 min)
- [ ] Update requirements.txt
- [ ] Create validation doc
- [ ] Update story status
- [ ] Commit changes

**Total Estimated Time:** 3-4 hours focused work

---

## ✅ Pre-flight Checklist

Before starting, verify:
- [ ] In correct directory: `pwd` shows `/Users/reena/plccoach/api-service`
- [ ] Virtual env activated: `(venv)` in prompt
- [ ] Database accessible: Can run query in Story 1.2 validation
- [ ] Git branch correct: `epic-1-foundation-authentication`
- [ ] Latest changes committed: `git status` clean
- [ ] Handoff doc reviewed: Read the full handoff document

---

## 🚀 Ready to Start?

**Copy the resume prompt above and paste it into a new Claude Code conversation.**

The assistant will:
1. Review the handoff document
2. Guide you through each phase
3. Help you implement the code
4. Test as you build
5. Create documentation
6. Help you commit when done

**Good luck! 🎉**
