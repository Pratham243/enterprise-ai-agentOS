"""Tests for the database layer."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.base import Base
from backend.app.db.session import async_session, engine
from backend.app.models.audit_log import AuditLog


@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_database_connection():
    """Verify we can connect and run a simple query."""
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


async def test_create_audit_log():
    """Insert an AuditLog row and read it back."""
    async with async_session() as session:
        log = AuditLog(action="test.action", actor="test-suite", detail="Step 3 test")
        session.add(log)
        await session.commit()

        result = await session.execute(select(AuditLog))
        rows = result.scalars().all()

    assert len(rows) == 1
    assert rows[0].action == "test.action"
    assert rows[0].actor == "test-suite"
    assert rows[0].created_at is not None
