"""Approval service — manages the human-in-the-loop review flow.

Provides create / list / resolve operations for approval requests.
Agents call create_approval() when they need human sign-off.
Humans call resolve_approval() to approve or reject.
"""

import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.approval import ApprovalRequest


async def create_approval(
    db: AsyncSession,
    action: str,
    description: str,
    agent_name: str,
) -> ApprovalRequest:
    """Create a new approval request (status: pending)."""
    request = ApprovalRequest(
        action=action,
        description=description,
        agent_name=agent_name,
        status="pending",
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def list_pending(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[ApprovalRequest], int]:
    """Return paginated pending approval requests.

    Returns (approvals, total_count).
    """
    base = select(ApprovalRequest).where(ApprovalRequest.status == "pending")
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    result = await db.execute(
        base.order_by(ApprovalRequest.created_at.desc()).offset(offset).limit(limit)
    )
    return list(result.scalars().all()), total


async def resolve_approval(
    db: AsyncSession,
    approval_id: int,
    status: str,
    reviewer: str,
    note: str | None = None,
) -> ApprovalRequest | None:
    """Approve or reject a pending request.

    Args:
        status: "approved" or "rejected"
    """
    result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    )
    request = result.scalar_one_or_none()
    if not request or request.status != "pending":
        return None

    request.status = status
    request.reviewer = reviewer
    request.review_note = note
    request.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
    await db.commit()
    await db.refresh(request)
    return request
