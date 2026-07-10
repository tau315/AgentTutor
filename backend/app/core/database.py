from collections.abc import AsyncGenerator


async def get_db_session() -> AsyncGenerator[None, None]:
    """Placeholder dependency for a future SQLAlchemy async session."""
    yield None

