"""Evaluation endpoint — score AI response quality.

POST /evaluation/score — evaluate a question-answer pair.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.services.evaluation import evaluate_response

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class EvalRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    answer: str = Field(..., min_length=1, max_length=50000)
    context: str = Field(default="", max_length=50000)


class EvalResponse(BaseModel):
    relevance_score: float
    completeness_score: float
    safety_score: float
    overall_score: float
    feedback: list[str]


@router.post("/score", response_model=EvalResponse)
async def score_response(request: EvalRequest) -> EvalResponse:
    """Evaluate the quality of an AI-generated response."""
    result = evaluate_response(request.question, request.answer, request.context)
    return EvalResponse(
        relevance_score=result.relevance_score,
        completeness_score=result.completeness_score,
        safety_score=result.safety_score,
        overall_score=result.overall_score,
        feedback=result.feedback,
    )
