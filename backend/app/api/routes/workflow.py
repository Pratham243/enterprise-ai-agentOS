"""Workflow API endpoint — run the full LangGraph-style pipeline.

POST /workflow/run sends a question through the multi-step graph:
classify → retrieve/query → synthesize → answer

The response includes the full trace of which nodes ran and what
each one did, providing transparency into the AI's reasoning.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.api.throttle import throttle
from backend.app.workflows.graph import build_default_workflow
from backend.app.services.cache import app_cache

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class WorkflowRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)

    model_config = {
        "json_schema_extra": {
            "examples": [{"question": "Analyze our top risk factors this quarter"}]
        }
    }


class WorkflowResponse(BaseModel):
    question: str
    category: str
    answer: str
    steps: list[dict]
    cached: bool = False

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "Analyze our top risk factors this quarter",
                    "category": "analytics",
                    "answer": "Three key risk factors identified...",
                    "steps": [
                        {"node": "classify", "result": "analytics"},
                        {"node": "retrieve", "result": "3 documents found"},
                    ],
                    "cached": False,
                }
            ]
        }
    }


@router.post("/run", response_model=WorkflowResponse)
async def run_workflow(
    request: WorkflowRequest,
    _throttle=throttle("strict"),
) -> WorkflowResponse:
    """Run a question through the full orchestration workflow."""
    cached = app_cache.get("workflow", request.question)
    if cached:
        return WorkflowResponse(**{**cached, "cached": True})

    graph = build_default_workflow()
    result = await graph.run({"question": request.question})
    response = WorkflowResponse(
        question=request.question,
        category=result.get("category", "unknown"),
        answer=result.get("answer", "No answer produced."),
        steps=result.get("steps", []),
    )
    app_cache.set("workflow", request.question, value=response.model_dump())
    return response
