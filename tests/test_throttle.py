"""Tests for per-endpoint request throttling and rate-limit headers."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.api.throttle import _TIERS, throttle
from backend.app.main import app


# ---------------------------------------------------------------------------
# Unit tests — tier configuration
# ---------------------------------------------------------------------------

def test_tiers_exist():
    assert "strict" in _TIERS
    assert "default" in _TIERS
    assert "relaxed" in _TIERS


def test_strict_tier_limit():
    assert _TIERS["strict"].max_requests == 10
    assert _TIERS["strict"].window_seconds == 60


def test_default_tier_limit():
    assert _TIERS["default"].max_requests == 60


def test_relaxed_tier_limit():
    assert _TIERS["relaxed"].max_requests == 200


def test_unknown_tier_raises():
    with pytest.raises(ValueError, match="Unknown throttle tier"):
        throttle("nonexistent")


# ---------------------------------------------------------------------------
# Integration tests — headers on throttled endpoints
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_agent_query_has_rate_limit_headers():
    """Strict-tier endpoint returns X-RateLimit-* headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agent/query", json={"question": "What is revenue?"})
        assert resp.status_code == 200
        assert "x-ratelimit-limit" in resp.headers
        assert "x-ratelimit-remaining" in resp.headers
        assert "x-ratelimit-reset" in resp.headers
        assert resp.headers["x-ratelimit-limit"] == "10"


@pytest.mark.asyncio
async def test_workflow_run_has_rate_limit_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/workflow/run", json={"question": "Analyze trends"})
        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == "10"


@pytest.mark.asyncio
async def test_task_stats_has_relaxed_headers():
    """Relaxed-tier endpoint gets higher limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tasks/stats")
        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == "200"


@pytest.mark.asyncio
async def test_remaining_decrements():
    """Each request decrements the remaining count."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp1 = await client.get("/tasks/stats")
        remaining1 = int(resp1.headers["x-ratelimit-remaining"])

        resp2 = await client.get("/tasks/stats")
        remaining2 = int(resp2.headers["x-ratelimit-remaining"])

        assert remaining2 < remaining1


@pytest.mark.asyncio
async def test_reset_header_value():
    """Reset header matches the window duration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agent/query", json={"question": "test"})
        assert resp.headers["x-ratelimit-reset"] == "60"


@pytest.mark.asyncio
async def test_v1_throttled_endpoints():
    """Versioned endpoints also carry throttle headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/agent/query", json={"question": "v1 test"})
        assert resp.status_code == 200
        assert "x-ratelimit-limit" in resp.headers

        resp = await client.get("/api/v1/tasks/stats")
        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == "200"


@pytest.mark.asyncio
async def test_risk_predict_strict_throttle():
    """Risk predict uses strict tier."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/risk/predict", json={
            "entity_id": "vendor-99",
            "features": {"days_since_last_audit": 100, "compliance_score": 80, "open_incidents": 1},
        })
        assert resp.status_code == 200
        assert resp.headers["x-ratelimit-limit"] == "10"
