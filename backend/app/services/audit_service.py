"""Audit service — manages the audit log for compliance and traceability.

Provides create / list operations with pagination and filtering.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_log import AuditLog


async def create_entry(
    db: AsyncSession,
    action: str,
    actor: str,
    detail: str | None = None,
) -> AuditLog:
    """Record a new audit log entry."""
    entry = AuditLog(action=action, actor=actor, detail=detail)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_entries(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 20,
    action: str | None = None,
    actor: str | None = None,
) -> tuple[list[AuditLog], int]:
    """Return paginated audit log entries with optional filters.

    Returns (entries, total_count).
    """
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if actor:
        query = query.where(AuditLog.actor == actor)
        count_query = count_query.where(AuditLog.actor == actor)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)

    return list(result.scalars().all()), total
