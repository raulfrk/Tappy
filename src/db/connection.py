"""
Database connection helpers for the application.

This module provides a small convenience utility to create new SQLAlchemy Session
objects using the application's configured database URL (src.config.config.database_url).
The get_session function constructs a SQLAlchemy Engine and Session factory on each call
and returns a new Session instance bound to that Engine.

Notes:
- The application configuration (src.config.config) must be initialized before calling
    get_session; otherwise a ValueError is raised.
- The returned Session must be closed by the caller (session.close() or using a context
    manager) to release database connections.
- For long-running applications or high call volumes, consider reusing a single Engine
    and sessionmaker at module level to avoid the overhead of creating an Engine on every call.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import src.config as cfg


def get_session() -> Session:
    """Create and return a new SQLAlchemy Session using the configured database URL.

    This function:
    - Verifies that the application configuration (src.config.config) is initialized.
    - Creates a SQLAlchemy Engine from cfg.config.database_url.
    - Constructs a sessionmaker bound to that Engine and returns a fresh Session
      instance.

    Returns:
        sqlalchemy.orm.Session: A new SQLAlchemy Session bound to the configured Engine.

    Raises:
        ValueError: If the application configuration (src.config.config) is None.

    Usage:
        session = get_session()
        try:
            # use session
            ...
        finally:
            session.close()
    """
    if cfg.config is None:
        raise ValueError(
            "Config is not set. Please initialize the config before getting a session."
        )
    engine = create_engine(cfg.config.database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
