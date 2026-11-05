"""Database seed script — populate with realistic demo data.

Run standalone:
    python -m backend.app.seed

Inserts sample audit logs, approval requests, and RAG documents
so the platform has data to showcase immediately after setup.
"""

import asyncio
import logging

from backend.app.db.base import Base
from backend.app.db.session import engine, async_session
from backend.app.models.audit_log import AuditLog
from backend.app.models.approval import ApprovalRequest
from backend.app.services.rag import ingest_document

logger = logging.getLogger(__name__)

AUDIT_ENTRIES = [
    {"action": "user_login", "actor": "admin@company.com", "detail": "Logged in from 10.0.1.5"},
    {"action": "agent_query", "actor": "analyst_agent", "detail": "Queried revenue data for Q3 2024"},
    {"action": "document_ingest", "actor": "system", "detail": "Ingested quarterly_report_q3.pdf (12 chunks)"},
    {"action": "workflow_run", "actor": "orchestrator", "detail": "Ran risk analysis pipeline — 3 nodes executed"},
    {"action": "approval_resolved", "actor": "admin@company.com", "detail": "Approved bulk data export request"},
    {"action": "cache_clear", "actor": "admin@company.com", "detail": "Flushed agent namespace (42 entries)"},
    {"action": "risk_predict", "actor": "analyst_agent", "detail": "Scored vendor-042 — high risk (0.87)"},
    {"action": "webhook_received", "actor": "n8n", "detail": "Triggered monthly compliance check workflow"},
    {"action": "user_login", "actor": "analyst@company.com", "detail": "Logged in from 10.0.2.8"},
    {"action": "mcp_execute", "actor": "research_agent", "detail": "Executed document_search tool via MCP"},
]

APPROVAL_REQUESTS = [
    {
        "action": "bulk_data_export",
        "description": "Export 10,000 customer records to CSV for quarterly audit",
        "agent_name": "analyst_agent",
        "status": "pending",
    },
    {
        "action": "delete_old_records",
        "description": "Remove 5,200 records older than 3 years per data retention policy",
        "agent_name": "data_cleanup_agent",
        "status": "pending",
    },
    {
        "action": "send_client_report",
        "description": "Email Q3 financial summary to external stakeholders",
        "agent_name": "research_agent",
        "status": "pending",
    },
]

DEMO_DOCUMENTS = [
    {
        "content": (
            "Q3 2024 Financial Summary: Total revenue reached $2.4M, a 15% increase "
            "over Q2. The enterprise segment contributed $1.6M while SMB accounted for "
            "$800K. Operating expenses were $1.8M, yielding an operating margin of 25%. "
            "Key growth drivers included new enterprise contracts and improved retention rates."
        ),
        "source": "quarterly_report_q3_2024.pdf",
    },
    {
        "content": (
            "Employee Onboarding Policy: All new hires must complete security training "
            "within 14 days. Access to production systems requires manager approval and "
            "completion of the SOC 2 compliance module. Remote employees receive hardware "
            "via secure courier with pre-configured VPN credentials."
        ),
        "source": "hr_onboarding_policy.pdf",
    },
    {
        "content": (
            "Vendor Risk Assessment Framework: Vendors are scored on a 0-1 scale across "
            "five dimensions — financial stability, compliance history, data handling practices, "
            "incident response capability, and contractual obligations. Scores above 0.7 "
            "trigger mandatory quarterly reviews. Critical vendors require on-site audits annually."
        ),
        "source": "vendor_risk_framework.pdf",
    },
]


async def seed_database():
    """Create tables and insert demo data."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        existing = (await session.execute(
            AuditLog.__table__.select().limit(1)
        )).first()
        if existing:
            logger.info("Database already seeded — skipping")
            return

        for entry in AUDIT_ENTRIES:
            session.add(AuditLog(**entry))

        for req in APPROVAL_REQUESTS:
            session.add(ApprovalRequest(**req))

        await session.commit()
        logger.info("Inserted %d audit entries", len(AUDIT_ENTRIES))
        logger.info("Inserted %d approval requests", len(APPROVAL_REQUESTS))

    for doc in DEMO_DOCUMENTS:
        ingest_document(doc["content"], doc["source"])
    logger.info("Ingested %d demo documents into RAG", len(DEMO_DOCUMENTS))

    logger.info("Database seeding complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
