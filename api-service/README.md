# PLC Coach API Service

FastAPI backend service for AI Powered PLC at Work Virtual Coach.

## Overview

This service provides the backend API for the PLC Coach application, handling:
- User authentication (Google OIDC, Clever SSO)
- Session management
- Conversation and message storage
- AI coach interactions
- Analytics and feedback

## Database

### Schema

The application uses PostgreSQL 15 with the following tables:

- **users**: User accounts with SSO integration
- **sessions**: Authentication sessions with expiration tracking
- **conversations**: Chat sessions between users and AI coach
- **messages**: Individual messages with JSONB citations and cost tracking

### Migrations

Database migrations are managed with Alembic. See [migrations/README.md](migrations/README.md) for detailed procedures.

**Quick Start:**

```bash
# Apply all migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Setup

#### Local Development

1. **Install Dependencies**
   ```bash
   cd api-service
   pip install -r requirements.txt
   ```

2. **Set Up Local PostgreSQL** (with pgvector)
   ```bash
   docker run -d \
     --name plccoach-db \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=plccoach \
     -p 5432:5432 \
     pgvector/pgvector:pg15
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

#### Production (AWS RDS)

Migrations automatically retrieve database credentials from AWS Secrets Manager.

```bash
# Ensure AWS credentials are configured
aws configure

# Run migrations (will auto-fetch from Secrets Manager)
alembic upgrade head
```

## Testing

### Run Tests

```bash
# All tests
pytest

# Migration tests only
pytest tests/migrations/

# With coverage
pytest --cov=. --cov-report=html
```

### Test Database Setup

```bash
# Create test database
createdb plccoach_test

# Or use Docker
docker run -d \
  --name plccoach-db-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=plccoach_test \
  -p 5433:5432 \
  pgvector/pgvector:pg15
```

## Project Structure

```
api-service/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration scripts
│   └── env.py               # Alembic environment
├── models/                  # SQLAlchemy models
│   ├── user.py
│   ├── session.py
│   ├── conversation.py
│   └── message.py
├── tests/                   # Test suite
│   └── migrations/          # Migration tests
├── migrations/              # Migration documentation
│   └── README.md            # Rollback procedures
├── db_config.py             # Database configuration
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Models

### User

Represents educators, coaches, and administrators.

**Fields:**
- `id` (UUID): Primary key
- `email` (String): Unique email address
- `name` (String): Display name
- `role` (Enum): educator, coach, or admin
- `sso_provider` (String): google or clever
- `sso_id` (String): SSO user ID
- `created_at`, `last_login` (DateTime)

### Session

Authentication sessions with automatic expiration.

**Fields:**
- `id` (UUID): Session ID
- `user_id` (UUID): Foreign key to users
- `expires_at` (DateTime): Session expiration
- `created_at`, `last_accessed_at` (DateTime)

**Cascade:** Deleting a user deletes their sessions

### Conversation

Chat sessions between users and the AI coach.

**Fields:**
- `id` (UUID): Conversation ID
- `user_id` (UUID): Foreign key to users
- `title` (String): Conversation title
- `status` (String): active, archived, or deleted
- `share_token` (String): Unique token for sharing
- `share_enabled` (Boolean): Allow public access
- `created_at`, `updated_at` (DateTime)

### Message

Individual messages within conversations.

**Fields:**
- `id` (UUID): Message ID
- `conversation_id` (UUID): Foreign key to conversations
- `role` (Enum): user, assistant, or system
- `content` (String): Message text
- `citations` (JSONB): Structured citation data
- `domains` (Array): Knowledge domains
- `feedback_score` (Integer): User feedback (-1, 0, 1)
- `input_tokens`, `output_tokens` (Integer): Token counts
- `cost_usd` (Decimal): API cost
- `created_at` (DateTime)

**Cascade:** Deleting a conversation deletes its messages

## Database Indexes

Performance indexes created by initial migration:

- `idx_users_email`: Fast email lookup for login
- `idx_sessions_id`: Partial index for active sessions only
- `idx_conversations_user`: User's conversation list
- `idx_conversations_share_token`: Public sharing lookups
- `idx_messages_conversation`: Message retrieval ordered by time

## Dependencies

- **Alembic 1.13.1**: Database migration framework
- **SQLAlchemy 2.0.25**: ORM and query builder
- **psycopg2-binary 2.9.9**: PostgreSQL adapter
- **pgvector 0.2.4**: Vector embeddings extension
- **boto3 1.34.34**: AWS SDK for Secrets Manager
- **pytest**: Testing framework

## Security

- Database credentials stored in AWS Secrets Manager (production)
- KMS-encrypted RDS instance
- Connection pooling (20 connections per service)
- CASCADE delete for dependent records
- Check constraints on enum fields

## Development Notes

### Adding a Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add user preferences"

# Review generated migration
# Edit if needed
# Test locally
alembic upgrade head

# Commit to git
git add alembic/versions/*
git commit -m "Add user preferences migration"
```

### pgvector Extension

The pgvector extension is installed via the initial migration (`CREATE EXTENSION IF NOT EXISTS vector`). It's not in the RDS parameter group, so it must be installed as a PostgreSQL extension.

**Usage** (for future epics):

```python
from pgvector.sqlalchemy import Vector

class ContentChunk(Base):
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
```

## Troubleshooting

### Connection to RDS Fails

Check security groups allow connection from your IP/ECS tasks:
```bash
aws ec2 describe-security-groups \
  --group-ids sg-xxx \
  --query 'SecurityGroups[*].IpPermissions'
```

### pgvector Not Available

Manually install the extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Migration Fails

Check Alembic version table:
```sql
SELECT * FROM alembic_version;
```

Manually stamp if needed:
```bash
alembic stamp <revision>
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Story 1.2: Database Schema Creation](../docs/stories/1-2-database-schema-creation.md)
