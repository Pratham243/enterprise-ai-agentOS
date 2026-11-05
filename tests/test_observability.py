"""Tests for Step 18: Structured logging and request observability."""

import json
import logging

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.logging_config import JSONFormatter, request_id_var, setup_logging
from backend.app.main import app


def test_json_formatter_basic():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="hello world", args=(), exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "hello world"
    assert "timestamp" in parsed


def test_json_formatter_includes_request_id():
    formatter = JSONFormatter()
    token = request_id_var.set("abc123")
    try:
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="with request", args=(), exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["request_id"] == "abc123"
    finally:
        request_id_var.reset(token)


def test_json_formatter_extra_fields():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="request", args=(), exc_info=None,
    )
    record.duration_ms = 42.5
    record.status_code = 200
    record.method = "GET"
    record.path = "/health"
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["duration_ms"] == 42.5
    assert parsed["status_code"] == 200
    assert parsed["method"] == "GET"


def test_setup_logging_configures_handler():
    setup_logging("WARNING")
    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert any(isinstance(h.formatter, JSONFormatter) for h in root.handlers)
    setup_logging("INFO")


async def test_request_id_in_response_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


async def test_custom_request_id_passthrough():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"X-Request-ID": "my-custom-id-123"},
        )
    assert response.headers["x-request-id"] == "my-custom-id-123"


async def test_request_logging_does_not_break_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/")
        r2 = await client.get("/health")
        r3 = await client.post("/agent/query", json={"question": "test"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200
