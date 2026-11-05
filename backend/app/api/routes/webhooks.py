"""Webhook endpoints for workflow automation (n8n, Zapier, etc.).

External automation platforms send HTTP requests to these endpoints
to trigger agent workflows. For example, n8n can be configured to:
- Call POST /webhooks/trigger when a new support ticket arrives
- Call POST /webhooks/trigger when a scheduled report is due
- Call POST /webhooks/trigger when a document is uploaded

The webhook payload describes what event happened, and the system
routes it to the appropriate agent workflow.
"""

import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.workflows.graph import build_default_workflow

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class WebhookPayload(BaseModel):
    """Incoming webhook from an automation platform."""

    event: str = Field(..., max_length=200, description="Event type, e.g. 'new_ticket', 'scheduled_report'")
    source: str = Field(default="n8n", max_length=100, description="Which platform sent this")
    data: dict = Field(default_factory=dict, description="Event-specific payload")
    question: str | None = Field(default=None, max_length=5000, description="Optional question to process")


class WebhookResponse(BaseModel):
    received: bool = True
    event: str
    source: str
    timestamp: str
    result: dict | None = None


@router.post("/trigger", response_model=WebhookResponse)
async def trigger_webhook(payload: WebhookPayload) -> WebhookResponse:
    """Receive a webhook and optionally trigger a workflow."""
    result = None

    # If a question is included, run it through the workflow
    if payload.question:
        graph = build_default_workflow()
        workflow_result = await graph.run({"question": payload.question})
        result = {
            "answer": workflow_result.get("answer"),
            "category": workflow_result.get("category"),
        }

    return WebhookResponse(
        event=payload.event,
        source=payload.source,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        result=result,
    )
