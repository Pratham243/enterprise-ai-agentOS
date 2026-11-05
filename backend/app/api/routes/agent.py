"""Agent API endpoint — ask a question and get an AI-routed answer.

POST /agent/query sends a natural-language question through the
agent router, which picks the right tool (document search or SQL)
and returns the result with full transparency of what happened.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.agents.router import route_query
from backend.app.api.throttle import throttle
from backend.app.services.cache import app_cache

router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000, description="Question to ask the agent")

    model_config = {
        "json_schema_extra": {
            "examples": [{"question": "What is our total revenue for Q3?"}]
        }
    }


class AgentQueryResponse(BaseModel):
    question: str
    answer: str
    tool_used: str | None
    steps: list[dict]
    cached: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What is our total revenue for Q3?",
                    "answer": "Total Q3 revenue is $2.4M across all segments.",
                    "tool_used": "sql_tool",
                    "steps": [{"agent": "analyst", "action": "sql_query"}],
                    "cached": False,
                }
            ]
        }
    }


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    request: AgentQueryRequest,
    _throttle=throttle("strict"),
) -> AgentQueryResponse:
    """Route a question to the appropriate agent and return the answer."""
    cached = app_cache.get("agent", request.question)
    if cached:
        return AgentQueryResponse(**{**cached, "cached": True})

    result = await route_query(request.question)
    response = AgentQueryResponse(
        question=request.question,
        answer=result.answer,
        tool_used=result.tool_used,
        steps=result.steps,
    )
    app_cache.set("agent", request.question, value=response.model_dump())
    return response
