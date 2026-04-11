"""
Database Connection Module

Handles database connection, session management, and initialization.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger

from src.database.models import Base

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'strategyhub.db'

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine(db_path: str = None, echo: bool = False):
    """
    Get or create the database engine.

    Args:
        db_path: Path to SQLite database file. Defaults to data/strategyhub.db
        echo: If True, log all SQL statements

    Returns:
        SQLAlchemy engine
    """
    global _engine

    if _engine is not None:
        return _engine

    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Ensure directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Create engine
    # Using StaticPool for SQLite to handle multi-threading
    _engine = create_engine(
        f'sqlite:///{db_path}',
        echo=echo,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    logger.info(f"Database engine created: {db_path}")
    return _engine


def get_session_factory(engine=None) -> sessionmaker:
    """
    Get or create the session factory.

    Args:
        engine: SQLAlchemy engine (uses default if not provided)

    Returns:
        Session factory
    """
    global _SessionLocal

    if _SessionLocal is not None:
        return _SessionLocal

    if engine is None:
        engine = get_engine()

    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    return _SessionLocal


def get_session() -> Session:
    """
    Get a new database session.

    Remember to close the session when done:
        session = get_session()
        try:
            # do work
        finally:
            session.close()

    Or use the session_scope context manager.
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Automatically handles commit/rollback and closing.

    Usage:
        with session_scope() as session:
            session.add(obj)
            # commits automatically on success
            # rolls back on exception
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: str = None, drop_existing: bool = False) -> None:
    """
    Initialize the database.

    Creates all tables defined in models.

    Args:
        db_path: Path to database file
        drop_existing: If True, drop all existing tables first
    """
    engine = get_engine(db_path)

    if drop_existing:
        logger.warning("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def reset_db(db_path: str = None) -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data!
    """
    init_db(db_path, drop_existing=True)


def close_db() -> None:
    """
    Close database connections and reset global state.

    Call this when shutting down the application.
    """
    global _engine, _SessionLocal

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("Database connections closed")


if __name__ == '__main__':
    # Test database initialization
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), format='{message}\n', level='INFO')

    # Initialize database
    print("Initializing database...")
    init_db()

    # Test session
    with session_scope() as session:
        from src.database.models import Strategy

        # Create test strategy
        test_strategy = Strategy(
            name='Test SMA',
            strategy_type='trend',
            description='Test strategy',
            default_params={'fast': 20, 'slow': 100}
        )
        session.add(test_strategy)

    # Verify
    with session_scope() as session:
        strategies = session.query(Strategy).all()
        print(f"Strategies in database: {len(strategies)}")
        for s in strategies:
            print(f"  - {s}")

    print("Database test completed!")
