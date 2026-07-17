from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# creates async driver for PostgreSQL database using asyncpg
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
)

# creates async session factory for PostgreSQL database
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# returns a session from session factory to be used, and closes the session after use
# one session per request so that requests are isolated from each other and do not interfere 
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session