"""Tests for Step 26 — Pagination, Filtering & Audit Log API.

Tests cover:
  - PaginationParams defaults and offset calculation
  - PaginatedResponse.create builds correct envelope
  - Audit log creation via API
  - Audit log listing with pagination
  - Audit log filtering by action and actor
  - Approvals pending endpoint returns paginated response
  - Pagination query params (page, page_size) respected
  - Empty result set returns correct pagination metadata
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db.base import Base
from backend.app.db.session import engine


@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.fixture
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_pagination_params_defaults():
    from backend.app.api.pagination import PaginationParams
    params = PaginationParams(page=1, page_size=20)
    assert params.page == 1
    assert params.page_size == 20
    assert params.offset == 0


def test_pagination_params_offset():
    from backend.app.api.pagination import PaginationParams
    params = PaginationParams(page=3, page_size=10)
    assert params.offset == 20


def test_paginated_response_create():
    from backend.app.api.pagination import PaginatedResponse
    resp = PaginatedResponse.create(items=["a", "b"], total=5, page=1, page_size=2)
    assert resp.items == ["a", "b"]
    assert resp.total == 5
    assert resp.page == 1
    assert resp.page_size == 2
    assert resp.total_pages == 3


def test_paginated_response_single_page():
    from backend.app.api.pagination import PaginatedResponse
    resp = PaginatedResponse.create(items=["x"], total=1, page=1, page_size=20)
    assert resp.total_pages == 1


@pytest.mark.asyncio
async def test_audit_log_create(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/audit/log",
            json={"action": "user.login", "actor": "admin", "detail": "Logged in"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "user.login"
    assert data["actor"] == "admin"
    assert data["id"] >= 1


@pytest.mark.asyncio
async def test_audit_log_list_paginated(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(5):
            await client.post(
                "/audit/log",
                json={"action": f"action_{i}", "actor": "bot"},
            )
        resp = await client.get("/audit/logs?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


@pytest.mark.asyncio
async def test_audit_log_filter_by_action(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/audit/log", json={"action": "user.login", "actor": "a"})
        await client.post("/audit/log", json={"action": "user.logout", "actor": "a"})
        resp = await client.get("/audit/logs?action=user.login")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "user.login"


@pytest.mark.asyncio
async def test_audit_log_filter_by_actor(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/audit/log", json={"action": "test", "actor": "alice"})
        await client.post("/audit/log", json={"action": "test", "actor": "bob"})
        resp = await client.get("/audit/logs?actor=bob")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["actor"] == "bob"


@pytest.mark.asyncio
async def test_audit_log_empty_list(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/audit/logs")
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["total_pages"] == 1


@pytest.mark.asyncio
async def test_approvals_pending_paginated(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(3):
            await client.post("/approvals/", json={
                "action": f"action_{i}",
                "description": "test",
                "agent_name": "bot",
            })
        resp = await client.get("/approvals/pending?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2


@pytest.mark.asyncio
async def test_v1_audit_log_reachable(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/audit/logs")
    assert resp.status_code == 200
    assert "items" in resp.json()
