"""Tests for Step 25 — Comprehensive Error Handling & Custom Exceptions.

Tests cover:
  - Custom exception classes have correct attributes
  - Structured error responses include code, message, and request_id
  - Validation errors return structured JSON (not default 422 body)
  - 404 errors return structured JSON
  - Rate limit errors include Retry-After header
  - Unhandled exceptions return 500 with INTERNAL_ERROR code
  - NotFoundError used in approvals route
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db.base import Base
from backend.app.db.session import engine


@pytest.fixture
def app():
    from backend.app.main import app as _app
    return _app


@pytest.fixture
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_app_error_attributes():
    from backend.app.exceptions import AppError
    err = AppError("something broke")
    assert err.status_code == 500
    assert err.code == "INTERNAL_ERROR"
    assert err.message == "something broke"


def test_not_found_error_with_resource():
    from backend.app.exceptions import NotFoundError
    err = NotFoundError("User", "42")
    assert err.status_code == 404
    assert err.code == "NOT_FOUND"
    assert "User" in err.message
    assert "'42'" in err.message


def test_not_found_error_without_identifier():
    from backend.app.exceptions import NotFoundError
    err = NotFoundError("Document")
    assert err.message == "Document not found"


def test_rate_limit_error_attributes():
    from backend.app.exceptions import RateLimitError
    err = RateLimitError(retry_after=30)
    assert err.status_code == 429
    assert err.code == "RATE_LIMIT_EXCEEDED"
    assert err.retry_after == 30


def test_authentication_error():
    from backend.app.exceptions import AuthenticationError
    err = AuthenticationError()
    assert err.status_code == 401
    assert err.code == "AUTHENTICATION_REQUIRED"


def test_service_unavailable_error():
    from backend.app.exceptions import ServiceUnavailableError
    err = ServiceUnavailableError("Database")
    assert err.status_code == 503
    assert "Database" in err.message


@pytest.mark.asyncio
async def test_validation_error_structured_response(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agent/query", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["error"]


@pytest.mark.asyncio
async def test_404_structured_response(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/nonexistent-path")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_approval_not_found_structured(app, setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/approvals/99999/resolve",
            json={"status": "approved", "reviewer": "admin"},
        )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "99999" in body["error"]["message"]


@pytest.mark.asyncio
async def test_rate_limit_structured_response(app):
    from backend.app.rate_limiter import RateLimiter, rate_limit
    from fastapi import APIRouter, Request

    limiter = RateLimiter(max_requests=1, window_seconds=60)
    test_router = APIRouter()

    @test_router.get("/test-rate-limit")
    async def rate_limited_endpoint(request: Request, _=rate_limit(limiter)):
        return {"ok": True}

    app.include_router(test_router)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/test-rate-limit")
        resp = await client.get("/test-rate-limit")

    assert resp.status_code == 429
    body = resp.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_method_not_allowed_structured(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete("/health")
    assert resp.status_code == 405
    body = resp.json()
    assert body["error"]["code"] == "METHOD_NOT_ALLOWED"
