"""Tests for the human-in-the-loop approval system."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_create_and_list_approval():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create an approval
        response = await client.post("/approvals/", json={
            "action": "delete_records",
            "description": "Agent wants to delete 500 old records",
            "agent_name": "analyst_agent",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["action"] == "delete_records"
        approval_id = data["id"]

        # List pending
        response = await client.get("/approvals/pending")
        assert response.status_code == 200
        pending = response.json()["items"]
        assert len(pending) >= 1
        assert any(a["id"] == approval_id for a in pending)


async def test_approve_request():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        response = await client.post("/approvals/", json={
            "action": "send_email",
            "description": "Send quarterly report to client",
            "agent_name": "research_agent",
        })
        approval_id = response.json()["id"]

        # Approve
        response = await client.post(f"/approvals/{approval_id}/resolve", json={
            "status": "approved",
            "reviewer": "Pratham243",
            "note": "Looks good, send it.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["reviewer"] == "Pratham243"

        # Should no longer appear in pending
        response = await client.get("/approvals/pending")
        pending = response.json()["items"]
        assert all(a["id"] != approval_id for a in pending)


async def test_reject_request():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/approvals/", json={
            "action": "dangerous_action",
            "description": "Agent wants to drop a table",
            "agent_name": "sql_agent",
        })
        approval_id = response.json()["id"]

        response = await client.post(f"/approvals/{approval_id}/resolve", json={
            "status": "rejected",
            "reviewer": "Pratham243",
            "note": "Too risky.",
        })
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
