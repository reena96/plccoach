"""Database configuration for PLC Coach API - retrieves credentials from AWS Secrets Manager."""
import json
import os
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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


def get_database_url(use_env: bool = True) -> str:
    """Get database connection URL from environment or AWS Secrets Manager.

    Priority:
    1. DATABASE_URL environment variable (if use_env=True)
    2. AWS Secrets Manager (production)
    3. Fallback local connection string (development only)

    Args:
        use_env: Whether to check environment variables first

    Returns:
        PostgreSQL connection URL string
    """
    # Check environment variable first (for local development)
    if use_env:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return database_url

    # Try to get from Secrets Manager (production)
    secret_name = os.getenv('DB_SECRET_NAME', 'plccoach-db-password')
    region = os.getenv('AWS_REGION', 'us-east-1')

    try:
        secret = get_secret(secret_name, region)

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


# Create engine instance (for migrations and testing)
def create_db_engine(**kwargs):
    """Create SQLAlchemy engine with database URL.

    Args:
        **kwargs: Additional arguments to pass to create_engine

    Returns:
        SQLAlchemy Engine instance
    """
    database_url = get_database_url()
    return create_engine(database_url, **kwargs)


# Create session maker (for application use)
def get_session_maker():
    """Get SQLAlchemy SessionMaker configured for the database.

    Returns:
        SQLAlchemy sessionmaker instance
    """
    engine = create_db_engine(pool_size=20, max_overflow=0)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
