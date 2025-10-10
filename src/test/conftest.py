from typing import Any, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from src.db.schema import Base


@pytest.fixture(scope="session")
def pg_url() -> Generator[str, Any, None]:
    """Set up a PostgreSQL test container and provide the database URL."""
    with PostgresContainer("postgres:18-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="function")
def db(pg_url: str) -> Generator[Session, Any, None]:
    """Create a database engine and session for testing."""
    engine = create_engine(pg_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
