"""Enterprise AI AgentOS — FastAPI application entry point.

Run with:
    uvicorn backend.app.main:app --reload

Interactive docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.app.api.routes import (
    agent,
    approvals,
    audit,
    cache_admin,
    evaluation,
    health,
    mcp,
    multi_agent,
    rag,
    risk,
    tasks,
    webhooks,
    workflow,
    ws,
)
from backend.app.api.v1_router import v1_router
from backend.app.config import settings
from backend.app.error_handlers import register_error_handlers
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.logging_config import setup_logging
from backend.app.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


setup_logging()


logger = logging.getLogger("agentos.lifecycle")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the application.

    On startup: create database tables if they don't exist.
    On shutdown: flush cache, close DB connections, log cleanly.
    """
    logger.info("Starting up — creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Startup complete — ready to serve requests")

    yield

    logger.info("Shutting down — draining connections")
    from backend.app.services.cache import app_cache
    cache_size = app_cache.stats()["size"]
    app_cache.clear()
    logger.info("Cache flushed (%d entries cleared)", cache_size)

    await engine.dispose()
    logger.info("Database connections closed — shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Multi-Agent Business Intelligence & Workflow Platform.\n\n"
        "Specialized AI agents answer business questions, analyze data and documents, "
        "run analytics workflows, and automate business processes — with humans kept "
        "in the loop for critical decisions.\n\n"
        "**Key capabilities:**\n"
        "- RAG-powered document intelligence\n"
        "- Multi-agent orchestration with conditional routing\n"
        "- Human-in-the-loop approval workflows\n"
        "- Risk scoring with feature-level explanations\n"
        "- Background async job processing\n"
        "- Role-based access control (admin / analyst / viewer)\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Service health, liveness, and readiness probes"},
        {"name": "RAG", "description": "Document ingestion and semantic search"},
        {"name": "Agent", "description": "AI agent query routing (research, analyst, SQL)"},
        {"name": "Workflow", "description": "LangGraph-style multi-step orchestration pipeline"},
        {"name": "Multi-Agent", "description": "Multi-agent orchestrator with specialized agents"},
        {"name": "MCP", "description": "Model Context Protocol tool discovery and execution"},
        {"name": "Approvals", "description": "Human-in-the-loop approval requests and resolution"},
        {"name": "Webhooks", "description": "External automation triggers (n8n, Zapier)"},
        {"name": "Risk Model", "description": "ML risk scoring with SHAP-style explanations"},
        {"name": "Evaluation", "description": "AI response quality scoring"},
        {"name": "Cache", "description": "Cache statistics and administration"},
        {"name": "Audit", "description": "Compliance audit trail (log and query)"},
        {"name": "Background Tasks", "description": "Async job submission, polling, and stats"},
        {"name": "WebSocket", "description": "Real-time streaming agent workflow"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# --- Global error handlers ----------------------------------------------------
register_error_handlers(app)

# --- Register route modules ---------------------------------------------------
# Health endpoints stay at root level for Kubernetes / Docker / load balancers.
app.include_router(health.router)

# Versioned API — all business-logic endpoints live under /api/v1.
app.include_router(v1_router)

# Backward-compatible root-level mounts (kept so existing clients don't break).
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(workflow.router)
app.include_router(multi_agent.router)
app.include_router(mcp.router)
app.include_router(approvals.router)
app.include_router(webhooks.router)
app.include_router(risk.router)
app.include_router(evaluation.router)
app.include_router(cache_admin.router)
app.include_router(audit.router)
app.include_router(tasks.router)
app.include_router(ws.router)

# Ensure all models are imported so Base.metadata knows about them.
import backend.app.models  # noqa: E402, F401


@app.get("/")
async def root() -> dict:
    """Root endpoint — confirms the API is reachable."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
    }
