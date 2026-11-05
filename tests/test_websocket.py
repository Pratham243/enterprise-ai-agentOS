"""Tests for Step 20 — WebSocket Streaming.

Tests cover:
  - WebSocket connection lifecycle
  - Streaming a workflow question and receiving step + complete events
  - Error handling for bad payloads
  - Graph on_step callback integration
"""

import json
import pytest
from starlette.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_websocket_connection(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text(json.dumps({"question": "What is the refund policy?"}))
        messages = []
        while True:
            data = json.loads(ws.receive_text())
            messages.append(data)
            if data["type"] in ("complete", "error"):
                break
    assert len(messages) >= 2
    assert messages[-1]["type"] == "complete"
    assert "answer" in messages[-1]


def test_websocket_streams_steps(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text(json.dumps({"question": "Show me revenue data"}))
        step_nodes = []
        while True:
            data = json.loads(ws.receive_text())
            if data["type"] == "step":
                step_nodes.append(data["node"])
            if data["type"] == "complete":
                break
    assert "classify" in step_nodes
    assert "synthesize" in step_nodes


def test_websocket_invalid_json(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text("not json at all")
        data = json.loads(ws.receive_text())
    assert data["type"] == "error"
    assert "Invalid JSON" in data["detail"]


def test_websocket_missing_question(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text(json.dumps({"wrong_key": "value"}))
        data = json.loads(ws.receive_text())
    assert data["type"] == "error"
    assert "Missing question" in data["detail"]


def test_websocket_oversized_question(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text(json.dumps({"question": "x" * 5001}))
        data = json.loads(ws.receive_text())
    assert data["type"] == "error"
    assert "too long" in data["detail"]


def test_websocket_complete_has_category(client):
    with client.websocket_connect("/ws/agent") as ws:
        ws.send_text(json.dumps({"question": "What is the refund policy?"}))
        final = None
        while True:
            data = json.loads(ws.receive_text())
            if data["type"] == "complete":
                final = data
                break
    assert "category" in final
    assert final["category"] in ("rag", "sql")


# ---------------------------------------------------------------------------
# Graph on_step callback unit test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_graph_on_step_callback():
    from backend.app.workflows.graph import build_default_workflow

    captured = []

    async def capture(node_name, node_output, state):
        captured.append(node_name)

    graph = build_default_workflow()
    await graph.run({"question": "test question"}, on_step=capture)
    assert "classify" in captured
    assert "synthesize" in captured
    assert len(captured) >= 3
