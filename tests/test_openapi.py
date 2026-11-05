"""Tests for OpenAPI schema enrichment — tags, descriptions, examples."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.fixture
async def openapi_schema():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        return resp.json()


@pytest.mark.asyncio
async def test_openapi_info(openapi_schema):
    info = openapi_schema["info"]
    assert info["title"] == "Enterprise AI AgentOS"
    assert info["version"] == "1.0.0"
    assert "Multi-Agent" in info["description"]
    assert "RAG" in info["description"]


@pytest.mark.asyncio
async def test_openapi_tags_present(openapi_schema):
    tags = openapi_schema.get("tags", [])
    tag_names = [t["name"] for t in tags]
    assert "Health" in tag_names
    assert "Agent" in tag_names
    assert "Workflow" in tag_names
    assert "RAG" in tag_names
    assert "Approvals" in tag_names
    assert "Risk Model" in tag_names
    assert "Background Tasks" in tag_names


@pytest.mark.asyncio
async def test_openapi_tags_have_descriptions(openapi_schema):
    tags = openapi_schema.get("tags", [])
    for tag in tags:
        assert "description" in tag, f"Tag '{tag['name']}' missing description"
        assert len(tag["description"]) > 10


@pytest.mark.asyncio
async def test_agent_query_schema_has_examples(openapi_schema):
    schemas = openapi_schema["components"]["schemas"]
    agent_req = schemas.get("AgentQueryRequest", {})
    assert "examples" in agent_req


@pytest.mark.asyncio
async def test_workflow_schema_has_examples(openapi_schema):
    schemas = openapi_schema["components"]["schemas"]
    wf_req = schemas.get("WorkflowRequest", {})
    assert "examples" in wf_req


@pytest.mark.asyncio
async def test_v1_paths_in_schema(openapi_schema):
    paths = openapi_schema["paths"]
    assert "/api/v1/agent/query" in paths
    assert "/api/v1/workflow/run" in paths
    assert "/api/v1/tasks/submit" in paths
    assert "/api/v1/rag/query" in paths


@pytest.mark.asyncio
async def test_swagger_ui_accessible():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/docs")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_redoc_accessible():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/redoc")
        assert resp.status_code == 200
