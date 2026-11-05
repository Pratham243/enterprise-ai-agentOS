"""Tests for Step 19 — Rate Limiting & API Security Hardening.

Tests cover:
  - RateLimiter sliding window logic
  - SecurityHeadersMiddleware response headers
  - Input validation (max_length enforcement via Pydantic)
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.rate_limiter import RateLimiter


# ---------------------------------------------------------------------------
# Rate limiter unit tests
# ---------------------------------------------------------------------------

def test_rate_limiter_allows_within_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    allowed, remaining = limiter.is_allowed("client-a")
    assert allowed is True
    assert remaining == 2


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("client-b")
    limiter.is_allowed("client-b")
    allowed, remaining = limiter.is_allowed("client-b")
    assert allowed is False
    assert remaining == 0


def test_rate_limiter_separate_keys():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("client-x")
    allowed, _ = limiter.is_allowed("client-y")
    assert allowed is True


def test_rate_limiter_remaining_decrements():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    _, r1 = limiter.is_allowed("c")
    _, r2 = limiter.is_allowed("c")
    _, r3 = limiter.is_allowed("c")
    assert r1 == 4
    assert r2 == 3
    assert r3 == 2


# ---------------------------------------------------------------------------
# Security headers integration tests
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.mark.asyncio
async def test_security_headers_present(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-XSS-Protection"] == "1; mode=block"
    assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in resp.headers["Permissions-Policy"]


@pytest.mark.asyncio
async def test_request_id_header_returned(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_query_rejects_oversized_input(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agent/query", json={"question": "x" * 5001})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_workflow_rejects_oversized_input(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/workflow/run", json={"question": "x" * 5001})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rag_ingest_rejects_oversized_text(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/rag/ingest", json={"text": "x" * 100001})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_rejects_oversized_entity_id(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/risk/predict",
            json={"entity_id": "x" * 201, "features": {"a": 1}},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_approval_rejects_oversized_action(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/approvals/",
            json={
                "action": "x" * 201,
                "description": "test",
            },
        )
    assert resp.status_code == 422
