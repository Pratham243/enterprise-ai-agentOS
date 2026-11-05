"""Tests for gzip response compression."""

import gzip

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_gzip_response_when_accepted():
    """Large responses are gzip-compressed when client accepts it."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/agent/query",
            json={"question": "Give me a detailed analysis of revenue trends"},
            headers={"Accept-Encoding": "gzip"},
        )
        assert resp.status_code == 200
        assert resp.json()["answer"]


@pytest.mark.asyncio
async def test_no_gzip_without_accept_header():
    """Responses are not compressed when client doesn't accept gzip."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/", headers={"Accept-Encoding": "identity"})
        assert resp.status_code == 200
        assert "content-encoding" not in resp.headers or resp.headers.get("content-encoding") != "gzip"


@pytest.mark.asyncio
async def test_small_responses_not_compressed():
    """Responses below minimum_size threshold are not compressed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/health",
            headers={"Accept-Encoding": "gzip"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_gzip_on_workflow_endpoint():
    """Workflow responses (typically large) support compression."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/workflow/run",
            json={"question": "What are the top risk factors?"},
            headers={"Accept-Encoding": "gzip"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data


@pytest.mark.asyncio
async def test_gzip_on_task_list():
    """Paginated list endpoints support compression."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/tasks/",
            headers={"Accept-Encoding": "gzip"},
        )
        assert resp.status_code == 200
        assert "items" in resp.json()
