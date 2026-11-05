"""Human-in-the-loop approval endpoints.

POST /approvals/         — create a new approval request
GET  /approvals/pending  — list all pending requests
POST /approvals/{id}/resolve — approve or reject a request
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.pagination import PaginatedResponse, PaginationParams
from backend.app.db.session import get_db
from backend.app.exceptions import NotFoundError
from backend.app.services import approval_service

router = APIRouter(prefix="/approvals", tags=["Human-in-the-Loop"])


class CreateApprovalRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    agent_name: str = Field(default="system", max_length=100)


class ResolveRequest(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")
    reviewer: str = Field(..., min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=2000)


class ApprovalResponse(BaseModel):
    id: int
    action: str
    description: str
    agent_name: str
    status: str
    reviewer: str | None
    review_note: str | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=ApprovalResponse)
async def create_approval(
    request: CreateApprovalRequest,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """Create a new approval request from an agent."""
    approval = await approval_service.create_approval(
        db, request.action, request.description, request.agent_name
    )
    return ApprovalResponse.model_validate(approval)


@router.get("/pending", response_model=PaginatedResponse)
async def list_pending(
    params: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List pending approval requests with pagination."""
    approvals, total = await approval_service.list_pending(
        db, offset=params.offset, limit=params.page_size
    )
    items = [ApprovalResponse.model_validate(a) for a in approvals]
    return PaginatedResponse.create(items, total, params.page, params.page_size)


@router.post("/{approval_id}/resolve", response_model=ApprovalResponse)
async def resolve_approval(
    approval_id: int,
    request: ResolveRequest,
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """Approve or reject a pending request."""
    approval = await approval_service.resolve_approval(
        db, approval_id, request.status, request.reviewer, request.note
    )
    if not approval:
        raise NotFoundError("Approval", str(approval_id))
    return ApprovalResponse.model_validate(approval)
