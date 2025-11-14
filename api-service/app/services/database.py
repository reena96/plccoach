"""Database connection service with AWS Secrets Manager integration."""
import json
import os
from typing import Dict, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.config import settings

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# SQLAlchemy Base for model definitions
Base = declarative_base()


def get_secret(secret_name: str, region_name: str = "us-east-1") -> Dict:
    """Retrieve secret from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret in Secrets Manager
        region_name: AWS region (default: us-east-1)

    Returns:
        Dict containing secret values

    Raises:
        RuntimeError: If boto3 is not available or secret cannot be retrieved
    """
    if not BOTO3_AVAILABLE:
        raise RuntimeError(
            "boto3 is not installed. Install it with: pip install boto3"
        )

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret '{secret_name}': {e}") from e

    # Parse and return the secret
    secret_string = get_secret_value_response['SecretString']
    return json.loads(secret_string)


def get_database_url() -> str:
    """Get database connection URL from environment or AWS Secrets Manager.

    Priority:
    1. DATABASE_URL environment variable (settings)
    2. AWS Secrets Manager (production)
    3. Fallback local connection string (development only)

    Returns:
        PostgreSQL connection URL string
    """
    # Check settings/environment variable first (for local development)
    if settings.database_url:
        return settings.database_url

    # Try to get from Secrets Manager (production)
    try:
        secret = get_secret(settings.db_secret_name, settings.aws_region)

        # Construct connection URL from secret components
        username = secret['username']
        password = secret['password']
        host = secret['host']
        port = secret.get('port', 5432)
        dbname = secret.get('dbname', secret.get('db_name', 'plccoach'))

        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}"

    except Exception as e:
        # Fallback for local development (not recommended for production)
        print(f"Warning: Could not retrieve database credentials from Secrets Manager: {e}")
        print("Using fallback local connection. Set DATABASE_URL environment variable for local dev.")

        # Default local PostgreSQL connection
        return "postgresql+psycopg2://postgres:postgres@localhost:5432/plccoach"


# Create engine with connection pooling
database_url = get_database_url()
engine_kwargs = {"echo": False}

# Only add pooling args for non-SQLite databases
if "sqlite" not in database_url:
    engine_kwargs.update({
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": settings.db_pool_pre_ping,
    })

engine = create_engine(database_url, **engine_kwargs)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session.

    Yields:
        SQLAlchemy Session instance

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
