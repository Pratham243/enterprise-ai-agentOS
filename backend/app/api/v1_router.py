"""API v1 router — aggregates all versioned route modules under /api/v1.

Health and liveness endpoints stay at root level for orchestrators
(Kubernetes, Docker, load balancers). All business-logic endpoints
live here so future versions can coexist without breaking clients.
"""

from fastapi import APIRouter

from backend.app.api.routes import (
    agent,
    approvals,
    audit,
    cache_admin,
    evaluation,
    mcp,
    multi_agent,
    rag,
    risk,
    tasks,
    webhooks,
    workflow,
    ws,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(rag.router)
v1_router.include_router(agent.router)
v1_router.include_router(audit.router)
v1_router.include_router(workflow.router)
v1_router.include_router(multi_agent.router)
v1_router.include_router(mcp.router)
v1_router.include_router(approvals.router)
v1_router.include_router(webhooks.router)
v1_router.include_router(risk.router)
v1_router.include_router(evaluation.router)
v1_router.include_router(cache_admin.router)
v1_router.include_router(tasks.router)
v1_router.include_router(ws.router)
