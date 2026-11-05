"""Tests for Step 21 — Caching Layer.

Tests cover:
  - InMemoryCache get/set/TTL/LRU eviction
  - Cache stats tracking
  - Cache integration in endpoints (agent, workflow)
  - Cache admin endpoints (stats, clear)
"""

import time
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.services.cache import InMemoryCache, app_cache


# ---------------------------------------------------------------------------
# Unit tests — InMemoryCache
# ---------------------------------------------------------------------------

def test_cache_get_miss():
    cache = InMemoryCache()
    assert cache.get("ns", "key") is None


def test_cache_set_and_get():
    cache = InMemoryCache()
    cache.set("ns", "key", value={"answer": "42"})
    assert cache.get("ns", "key") == {"answer": "42"}


def test_cache_ttl_expiry():
    cache = InMemoryCache(default_ttl=0)
    cache.set("ns", "key", value={"a": 1}, ttl=0)
    time.sleep(0.01)
    assert cache.get("ns", "key") is None


def test_cache_lru_eviction():
    cache = InMemoryCache(max_size=2)
    cache.set("ns", "a", value=1)
    cache.set("ns", "b", value=2)
    cache.set("ns", "c", value=3)
    assert cache.get("ns", "a") is None
    assert cache.get("ns", "b") == 2
    assert cache.get("ns", "c") == 3


def test_cache_delete():
    cache = InMemoryCache()
    cache.set("ns", "x", value="val")
    assert cache.delete("ns", "x") is True
    assert cache.get("ns", "x") is None
    assert cache.delete("ns", "x") is False


def test_cache_clear_all():
    cache = InMemoryCache()
    cache.set("a", "1", value=1)
    cache.set("b", "2", value=2)
    count = cache.clear()
    assert count == 2
    assert cache.get("a", "1") is None


def test_cache_stats():
    cache = InMemoryCache()
    cache.set("ns", "k", value=1)
    cache.get("ns", "k")
    cache.get("ns", "missing")
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1
    assert stats["hit_rate"] == 0.5


def test_cache_multiple_args_key():
    cache = InMemoryCache()
    cache.set("rag", "question", 5, value={"results": []})
    assert cache.get("rag", "question", 5) == {"results": []}
    assert cache.get("rag", "question", 10) is None


# ---------------------------------------------------------------------------
# Integration tests — endpoints use cache
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.fixture(autouse=True)
def clear_app_cache():
    app_cache.clear()
    yield
    app_cache.clear()


@pytest.mark.asyncio
async def test_agent_endpoint_caches_result(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/agent/query", json={"question": "What is AI?"})
        r2 = await client.post("/agent/query", json={"question": "What is AI?"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["cached"] is False
    assert r2.json()["cached"] is True
    assert r1.json()["answer"] == r2.json()["answer"]


@pytest.mark.asyncio
async def test_workflow_endpoint_caches_result(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/workflow/run", json={"question": "Show revenue"})
        r2 = await client.post("/workflow/run", json={"question": "Show revenue"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["cached"] is False
    assert r2.json()["cached"] is True


# ---------------------------------------------------------------------------
# Cache admin endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_stats_endpoint(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/cache/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "hits" in data
    assert "misses" in data
    assert "size" in data


@pytest.mark.asyncio
async def test_cache_clear_endpoint(app):
    app_cache.set("test", "key", value="val")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/cache/clear", json={})
    assert resp.status_code == 200
    assert resp.json()["cleared"] >= 1
    assert app_cache.stats()["size"] == 0
