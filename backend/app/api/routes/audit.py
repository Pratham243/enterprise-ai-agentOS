"""Audit log endpoints — compliance and traceability.

POST /audit/log   — record an auditable event
GET  /audit/logs  — paginated, filterable audit trail
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.pagination import PaginatedResponse, PaginationParams
from backend.app.api.rbac import require_role
from backend.app.db.session import get_db
from backend.app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Audit"])


class AuditLogRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=255, description="Action performed")
    actor: str = Field(..., min_length=1, max_length=255, description="Who performed the action")
    detail: str | None = Field(default=None, max_length=5000, description="Additional details")


class AuditLogResponse(BaseModel):
    id: int
    action: str
    actor: str
    detail: str | None
    created_at: str

    model_config = {"from_attributes": True}


@router.post("/log", response_model=AuditLogResponse)
async def create_audit_log(
    request: AuditLogRequest,
    db: AsyncSession = Depends(get_db),
) -> AuditLogResponse:
    """Record an auditable event."""
    entry = await audit_service.create_entry(
        db, request.action, request.actor, request.detail
    )
    return AuditLogResponse(
        id=entry.id,
        action=entry.action,
        actor=entry.actor,
        detail=entry.detail,
        created_at=str(entry.created_at),
    )


@router.get("/logs", response_model=PaginatedResponse)
async def list_audit_logs(
    params: PaginationParams = Depends(),
    action: str | None = Query(None, max_length=255, description="Filter by action"),
    actor: str | None = Query(None, max_length=255, description="Filter by actor"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role("admin")),
) -> PaginatedResponse:
    """List audit log entries with pagination and optional filters."""
    entries, total = await audit_service.list_entries(
        db,
        offset=params.offset,
        limit=params.page_size,
        action=action,
        actor=actor,
    )
    items = [
        AuditLogResponse(
            id=e.id,
            action=e.action,
            actor=e.actor,
            detail=e.detail,
            created_at=str(e.created_at),
        )
        for e in entries
    ]
    return PaginatedResponse.create(items, total, params.page, params.page_size)
