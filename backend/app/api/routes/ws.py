"""WebSocket endpoint — real-time streaming for agent workflows.

WS /ws/agent accepts a JSON message with a question, runs the
workflow graph, and streams each step back as it completes. This
gives the client live visibility into the AI's reasoning process.

Protocol:
  Client sends:   {"question": "..."}
  Server streams: {"type": "step",     "node": "classify", "data": {...}}
                  {"type": "step",     "node": "retrieve_documents", "data": {...}}
                  {"type": "step",     "node": "synthesize", "data": {...}}
                  {"type": "complete", "answer": "...", "category": "..."}
  On error:       {"type": "error",    "detail": "..."}
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.app.workflows.graph import build_default_workflow

logger = logging.getLogger("agentos.ws")

router = APIRouter()


class ConnectionManager:
    """Track active WebSocket connections."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._active.remove(ws)

    @property
    def active_count(self) -> int:
        return len(self._active)


manager = ConnectionManager()


@router.websocket("/ws/agent")
async def agent_stream(ws: WebSocket):
    """Stream workflow execution steps over WebSocket."""
    await manager.connect(ws)
    logger.info("WebSocket connected (active: %d)", manager.active_count)

    try:
        while True:
            raw = await ws.receive_text()

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            question = payload.get("question", "").strip()
            if not question:
                await ws.send_json({"type": "error", "detail": "Missing question"})
                continue

            if len(question) > 5000:
                await ws.send_json({"type": "error", "detail": "Question too long (max 5000 chars)"})
                continue

            async def on_step(node_name, node_output, state):
                step_data = {k: v for k, v in node_output.items() if k != "steps"}
                await ws.send_json({
                    "type": "step",
                    "node": node_name,
                    "data": step_data,
                })

            try:
                graph = build_default_workflow()
                result = await graph.run(
                    {"question": question}, on_step=on_step,
                )

                await ws.send_json({
                    "type": "complete",
                    "question": question,
                    "answer": result.get("answer", "No answer produced."),
                    "category": result.get("category", "unknown"),
                    "steps": result.get("steps", []),
                })
            except Exception as exc:
                logger.exception("Workflow error during WebSocket stream")
                await ws.send_json({"type": "error", "detail": str(exc)})

    except WebSocketDisconnect:
        manager.disconnect(ws)
        logger.info("WebSocket disconnected (active: %d)", manager.active_count)
