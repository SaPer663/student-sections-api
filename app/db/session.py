from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)

from app.core.config import settings


engine: AsyncEngine = create_async_engine(
    settings.database.DATABASE_URL,
    echo=settings.database.DB_ECHO,
    pool_size=settings.database.DB_POOL_SIZE,
    max_overflow=settings.database.DB_MAX_OVERFLOW,
    pool_timeout=settings.database.DB_POOL_TIMEOUT,
    pool_recycle=settings.database.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)


async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения database session."""

    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
