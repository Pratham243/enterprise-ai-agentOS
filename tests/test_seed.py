"""Tests for the database seed script."""

import pytest

from backend.app.db.base import Base
from backend.app.db.session import engine, async_session
from backend.app.models.audit_log import AuditLog
from backend.app.models.approval import ApprovalRequest
from backend.app.seed import seed_database, AUDIT_ENTRIES, APPROVAL_REQUESTS, DEMO_DOCUMENTS
from sqlalchemy import func, select


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_seed_creates_audit_entries():
    await seed_database()
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(AuditLog))
        count = result.scalar()
        assert count == len(AUDIT_ENTRIES)


@pytest.mark.asyncio
async def test_seed_creates_approval_requests():
    await seed_database()
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(ApprovalRequest))
        count = result.scalar()
        assert count == len(APPROVAL_REQUESTS)


@pytest.mark.asyncio
async def test_seed_approvals_are_pending():
    await seed_database()
    async with async_session() as session:
        result = await session.execute(
            select(ApprovalRequest).where(ApprovalRequest.status == "pending")
        )
        pending = result.scalars().all()
        assert len(pending) == len(APPROVAL_REQUESTS)


@pytest.mark.asyncio
async def test_seed_is_idempotent():
    """Running seed twice does not duplicate data."""
    await seed_database()
    await seed_database()
    async with async_session() as session:
        result = await session.execute(select(func.count()).select_from(AuditLog))
        count = result.scalar()
        assert count == len(AUDIT_ENTRIES)


@pytest.mark.asyncio
async def test_seed_demo_documents_defined():
    assert len(DEMO_DOCUMENTS) >= 3
    for doc in DEMO_DOCUMENTS:
        assert "content" in doc
        assert "source" in doc
        assert len(doc["content"]) > 50
