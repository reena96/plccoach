"""Pytest configuration for testing."""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test database URL before any imports
# Use 'db' service in docker-compose, fallback to localhost for local testing
db_host = os.environ.get('DB_HOST', 'db' if os.environ.get('ENVIRONMENT') == 'development' else 'localhost')
os.environ['DATABASE_URL'] = f'postgresql+psycopg2://postgres:postgres@{db_host}:5432/plccoach'
os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'

from app.services.database import Base
from app.models.user import User
from app.models.session import Session as UserSession


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    # Create a test engine with connection pooling
    engine = create_engine(
        os.environ['DATABASE_URL'],
        pool_pre_ping=True
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Create a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
