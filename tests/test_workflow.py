"""Tests for the LangGraph-style workflow orchestration."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.workflows.graph import build_default_workflow


@pytest.fixture(autouse=True)
def reset_vector_store():
    from backend.app.services.vector_store import vector_store
    vector_store._vectors.clear()


async def test_workflow_rag_path():
    """A document question should follow classify → retrieve → synthesize."""
    graph = build_default_workflow()
    result = await graph.run({"question": "What is our refund policy?"})

    assert result["category"] == "rag"
    assert "answer" in result
    node_names = [s["node"] for s in result["steps"]]
    assert node_names == ["classify", "retrieve_documents", "synthesize"]


async def test_workflow_sql_path():
    """A data question should follow classify → query_database → synthesize."""
    graph = build_default_workflow()
    result = await graph.run({"question": "How many orders were placed?"})

    assert result["category"] == "sql"
    assert "answer" in result
    node_names = [s["node"] for s in result["steps"]]
    assert node_names == ["classify", "query_database", "synthesize"]


async def test_workflow_endpoint():
    """POST /workflow/run should return the full pipeline result."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/workflow/run", json={
            "question": "Explain the return policy",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "rag"
    assert "answer" in data
    assert len(data["steps"]) == 3
