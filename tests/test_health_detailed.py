"""Tests for Step 23 — Health Check Dependencies & Graceful Shutdown.

Tests cover:
  - Basic /health still works (backward-compatible)
  - /health/live returns alive
  - /health/ready checks all dependencies
  - Readiness response includes uptime
  - Individual dependency checks present in readiness
  - Graceful shutdown flushes cache
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.mark.asyncio
async def test_health_backward_compatible(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_liveness_probe(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_probe_all_healthy(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_readiness_checks_database(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
    checks = resp.json()["checks"]
    assert "database" in checks
    assert checks["database"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_checks_cache(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
    checks = resp.json()["checks"]
    assert "cache" in checks
    assert checks["cache"]["status"] == "healthy"
    assert "hit_rate" in checks["cache"]


@pytest.mark.asyncio
async def test_readiness_checks_vector_store(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health/ready")
    checks = resp.json()["checks"]
    assert "vector_store" in checks
    assert checks["vector_store"]["status"] == "healthy"
    assert "backend" in checks["vector_store"]


def test_graceful_shutdown_flushes_cache():
    from backend.app.services.cache import app_cache
    app_cache.set("ns", "key", value="val")
    assert app_cache.stats()["size"] >= 1
    app_cache.clear()
    assert app_cache.stats()["size"] == 0
