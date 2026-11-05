"""Tests for the multi-agent orchestration system."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.agents.registry import get_orchestrator
from backend.app.main import app


@pytest.fixture(autouse=True)
def reset_vector_store():
    from backend.app.services.vector_store import vector_store
    vector_store._vectors.clear()


async def test_orchestrator_routes_to_research():
    orch = get_orchestrator()
    result = await orch.run("What does the refund policy say?")
    assert "research_agent" in result.agents_used
    assert any(s.get("action") == "orchestrate" for s in result.steps)


async def test_orchestrator_routes_to_analyst():
    orch = get_orchestrator()
    result = await orch.run("How many users are there?")
    assert "analyst_agent" in result.agents_used


async def test_orchestrator_lists_agents():
    orch = get_orchestrator()
    assert "rag" in orch.available_agents
    assert "sql" in orch.available_agents


async def test_multi_agent_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/multi-agent/query", json={
            "question": "Summarize the latest report",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Summarize the latest report"
    assert "answer" in data
    assert len(data["agents_used"]) >= 1
    assert len(data["steps"]) >= 1
