"""SQLAlchemy async database engine and session factory.

Uses asyncpg driver for PostgreSQL. Provides engine lifecycle management
for startup/shutdown.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Module-level engine and session factory (initialized at startup)
_engine = None
_session_factory = None


def get_engine(database_url: str, echo: bool = False) -> object:
    """Get or create the async SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection string with asyncpg dialect.
        echo: Enable SQL echo logging.

    Returns:
        AsyncEngine instance.
    """
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def get_session_factory(database_url: str, echo: bool = False) -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory.

    Args:
        database_url: PostgreSQL connection string with asyncpg dialect.
        echo: Enable SQL echo logging.

    Returns:
        Async session maker instance.
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine(database_url, echo)
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def init_db(database_url: str, echo: bool = False) -> None:
    """Initialize database engine and create tables.

    Args:
        database_url: PostgreSQL connection string with asyncpg dialect.
        echo: Enable SQL echo logging.
    """
    from app.db.base import Base
    from app.models.user import User  # noqa: F401 -- ensure model is registered

    engine = get_engine(database_url, echo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the database engine and close all connections."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
