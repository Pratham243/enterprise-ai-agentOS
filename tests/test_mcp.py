"""Tests for the MCP tool registry and endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.mcp.registry import mcp_registry


async def test_registry_has_tools():
    assert mcp_registry.count >= 2
    tools = mcp_registry.list_tools()
    names = [t["name"] for t in tools]
    assert "document_search" in names
    assert "sql_query" in names


async def test_registry_tool_has_schema():
    tools = mcp_registry.list_tools()
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"


async def test_execute_unknown_tool():
    result = await mcp_registry.execute("nonexistent", {})
    assert "error" in result


async def test_mcp_list_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/mcp/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 2


async def test_mcp_execute_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/mcp/execute", json={
            "tool_name": "document_search",
            "arguments": {"query": "test"},
        })
    assert response.status_code == 200
    data = response.json()
    assert data["tool_name"] == "document_search"
    # Either result or a "no documents" message
    assert data["result"] is not None or data["error"] is not None
