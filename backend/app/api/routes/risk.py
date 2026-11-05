"""Risk assessment endpoint.

POST /risk/predict — score an entity's risk with feature-level explanations.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from backend.app.api.rbac import require_role
from backend.app.api.throttle import throttle
from backend.app.services.risk_model import predict_risk

router = APIRouter(prefix="/risk", tags=["Risk Model"])


class RiskRequest(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=200)
    features: dict = Field(..., description="Feature values for the entity")


class RiskResponse(BaseModel):
    entity_id: str
    risk_score: float
    risk_level: str
    explanations: list[dict]


@router.post("/predict", response_model=RiskResponse)
async def predict(
    request: RiskRequest,
    user: dict = Depends(require_role("analyst")),
    _throttle=throttle("strict"),
) -> RiskResponse:
    """Predict risk for an entity and explain the result."""
    result = predict_risk(request.entity_id, request.features)
    return RiskResponse(
        entity_id=result.entity_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        explanations=result.explanations,
    )
