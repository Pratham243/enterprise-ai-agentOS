"""Multi-agent API endpoint.

POST /multi-agent/query runs the orchestrator, which delegates
to the right specialist agent and returns a unified response with
full transparency into which agents were involved and what each did.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.agents.registry import get_orchestrator

router = APIRouter(prefix="/multi-agent", tags=["Multi-Agent"])


class MultiAgentRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)


class MultiAgentResponse(BaseModel):
    question: str
    answer: str
    agents_used: list[str]
    agent_results: list[dict]
    steps: list[dict]


@router.post("/query", response_model=MultiAgentResponse)
async def multi_agent_query(request: MultiAgentRequest) -> MultiAgentResponse:
    """Route a question through the multi-agent orchestrator."""
    orchestrator = get_orchestrator()
    result = await orchestrator.run(request.question)
    return MultiAgentResponse(
        question=result.question,
        answer=result.answer,
        agents_used=result.agents_used,
        agent_results=result.agent_results,
        steps=result.steps,
    )
