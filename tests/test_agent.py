"""Tests for the agent system — routing, tools, and the API endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.agents.router import _classify, route_query
from backend.app.main import app
from backend.app.tools.sql_tool import SQLTool


def test_classify_sql_question():
    assert _classify("How many orders were placed?") == "sql"
    assert _classify("What is the total revenue?") == "sql"
    assert _classify("Count all active users") == "sql"


def test_classify_rag_question():
    assert _classify("What does the refund policy say?") == "rag"
    assert _classify("Summarize the Q3 report") == "rag"


async def test_sql_tool_rejects_writes():
    """SQL tool must block INSERT/UPDATE/DELETE for safety."""
    tool = SQLTool()
    result = await tool.run("DELETE FROM users")
    assert "not allowed" in result.lower()

    result = await tool.run("DROP TABLE users")
    assert "not allowed" in result.lower()


async def test_agent_route_rag(reset_vector_store):
    """A document question should route to the RAG agent."""
    result = await route_query("What does our policy say about returns?")
    assert result.tool_used == "document_search"
    assert any(step.get("category") == "rag" for step in result.steps)


async def test_agent_endpoint():
    """POST /agent/query should return a structured response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/agent/query", json={
            "question": "What is in our documents?",
        })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "steps" in data
    assert data["question"] == "What is in our documents?"


@pytest.fixture
def reset_vector_store():
    from backend.app.services.vector_store import vector_store
    vector_store._vectors.clear()
