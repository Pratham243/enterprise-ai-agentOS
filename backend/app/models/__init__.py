"""Database models package.

Import all models here so that Alembic and Base.metadata
can discover every table in one place.
"""

from backend.app.models.approval import ApprovalRequest  # noqa: F401
from backend.app.models.audit_log import AuditLog  # noqa: F401
