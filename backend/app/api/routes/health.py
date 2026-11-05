"""Health-check endpoints for production orchestration.

GET /health       — simple alive check (backward-compatible)
GET /health/live  — liveness probe (is the process running?)
GET /health/ready — readiness probe (are all dependencies healthy?)

Kubernetes / Docker / load balancers use these to decide whether to
route traffic to this instance. The readiness probe checks each
dependency individually so operators can see exactly what's degraded.
"""

import logging
import time

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.db.session import async_session
from backend.app.services.cache import app_cache

logger = logging.getLogger("agentos.health")

router = APIRouter()

_start_time = time.monotonic()


def _uptime_seconds() -> float:
    return round(time.monotonic() - _start_time, 1)


@router.get("/health")
async def health_check() -> dict:
    """Simple health check — confirms the API is running."""
    return {
        "status": "healthy",
        "service": "Enterprise AI AgentOS",
        "uptime_seconds": _uptime_seconds(),
    }


@router.get("/health/live")
async def liveness() -> dict:
    """Liveness probe — if this responds, the process is alive."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> dict:
    """Readiness probe — checks every dependency and reports status.

    Returns 200 when all dependencies are healthy, 503 when any
    dependency is degraded (the response body still includes details
    so operators can see exactly what's wrong).
    """
    checks: dict[str, dict] = {}

    checks["database"] = await _check_database()
    checks["cache"] = _check_cache()
    checks["vector_store"] = _check_vector_store()

    all_healthy = all(c["status"] == "healthy" for c in checks.values())

    from fastapi.responses import JSONResponse

    body = {
        "status": "ready" if all_healthy else "degraded",
        "uptime_seconds": _uptime_seconds(),
        "checks": checks,
    }

    return JSONResponse(
        content=body,
        status_code=200 if all_healthy else 503,
    )


async def _check_database() -> dict:
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}


def _check_cache() -> dict:
    try:
        stats = app_cache.stats()
        return {"status": "healthy", "size": stats["size"], "hit_rate": stats["hit_rate"]}
    except Exception as exc:
        logger.warning("Cache health check failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}


def _check_vector_store() -> dict:
    try:
        from backend.app.services.pinecone_store import vector_store
        store_type = type(vector_store).__name__
        return {"status": "healthy", "backend": store_type}
    except Exception as exc:
        logger.warning("Vector store health check failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}
