"""Database engine and session factory.

SQLAlchemy's async engine manages a connection pool to the database.
The session factory creates short-lived sessions for each request —
one session per request, committed or rolled back when it's done.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL statements when debug is on
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields a database session per request.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session() as session:
        yield session
