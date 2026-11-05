"""Tests for Step 24 — API Versioning & OpenAPI Documentation.

Tests cover:
  - All v1 endpoints are reachable under /api/v1 prefix
  - Root-level health endpoints remain accessible (not versioned)
  - Root-level backward-compatible routes still work
  - OpenAPI schema includes versioned paths
  - API metadata (title, version) is present
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.mark.asyncio
async def test_v1_agent_query(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/agent/query",
            json={"question": "What is revenue?"},
        )
    assert resp.status_code == 200
    assert "answer" in resp.json()


@pytest.mark.asyncio
async def test_v1_rag_query(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/rag/query",
            json={"question": "test query"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_v1_workflow_run(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/workflow/run",
            json={"question": "Analyze sales"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_v1_mcp_tools(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/mcp/tools")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_v1_risk_predict(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/risk/predict",
            json={"entity_id": "test", "features": {"revenue": 1000}},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_v1_evaluation_score(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/evaluation/score",
            json={"question": "Q?", "answer": "A."},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_v1_cache_stats(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/cache/stats")
    assert resp.status_code == 200
    assert "size" in resp.json()


@pytest.mark.asyncio
async def test_health_not_versioned(app):
    """Health endpoints must stay at root level for orchestrators."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_backward_compatible(app):
    """Root-level endpoints still work for existing clients."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/agent/query",
            json={"question": "backward compat test"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema_has_versioned_paths(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    paths = list(schema["paths"].keys())
    versioned = [p for p in paths if p.startswith("/api/v1/")]
    assert len(versioned) >= 5


@pytest.mark.asyncio
async def test_openapi_metadata(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    schema = resp.json()
    assert schema["info"]["title"] == "Enterprise AI AgentOS"
    assert schema["info"]["version"] == "1.0.0"
