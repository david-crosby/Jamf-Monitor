from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings
from typing import AsyncGenerator

settings = get_settings()

Base = declarative_base()


def get_database_url() -> str:
    """
    Returns the appropriate database URL based on environment.
    Uses SQLite for development and MySQL for production.
    """
    if settings.environment == "development":
        return f"sqlite+aiosqlite:///{settings.database_path}"
    else:
        return (
            f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}"
            f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        )


engine = create_async_engine(
    get_database_url(),
    echo=settings.environment == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialise database tables.
    Only use in development. Use Alembic migrations in production.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
