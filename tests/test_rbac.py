"""Tests for Role-Based Access Control (RBAC).

Covers role hierarchy enforcement, dev-mode bypass, protected
endpoints, and error cases (missing role, insufficient role).
"""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.api.rbac import Role, ROLE_MAP, require_role, _get_role_level
from backend.app.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.exceptions import AuthorizationError
from backend.app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Unit tests — role definitions and hierarchy
# ---------------------------------------------------------------------------

def test_role_hierarchy_values():
    assert Role.VIEWER < Role.ANALYST < Role.ADMIN


def test_role_map_completeness():
    assert "viewer" in ROLE_MAP
    assert "analyst" in ROLE_MAP
    assert "admin" in ROLE_MAP


def test_get_role_level_valid():
    assert _get_role_level("admin") == Role.ADMIN
    assert _get_role_level("ANALYST") == Role.ANALYST
    assert _get_role_level("Viewer") == Role.VIEWER


def test_get_role_level_invalid():
    with pytest.raises(AuthorizationError, match="Unknown role"):
        _get_role_level("superuser")


def test_require_role_returns_callable():
    dep = require_role("admin")
    assert callable(dep)


# ---------------------------------------------------------------------------
# Integration tests — dev-mode bypass (JWT_SECRET_KEY is unset)
#
# Dev mode returns {"sub": "dev-user", "role": "admin"} so all
# role checks pass automatically.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dev_mode_admin_access_cache_clear():
    """Cache clear (admin-only) works in dev mode."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/cache/clear", json={})
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dev_mode_admin_access_audit_logs():
    """Audit log listing (admin-only) works in dev mode."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/audit/logs")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dev_mode_analyst_access_risk():
    """Risk predict (analyst+) works in dev mode (admin > analyst)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/risk/predict", json={
            "entity_id": "vendor-42",
            "features": {
                "days_since_last_audit": 200,
                "compliance_score": 55,
                "open_incidents": 3,
            },
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Integration tests — JWT-based role enforcement
#
# When JWT_SECRET_KEY is set, tokens must carry a valid role claim.
# ---------------------------------------------------------------------------

@pytest.fixture
def jwt_mode(monkeypatch):
    """Temporarily enable JWT authentication."""
    monkeypatch.setattr(settings, "jwt_secret_key", "test-secret-key-rbac")
    yield
    monkeypatch.setattr(settings, "jwt_secret_key", "")


def _make_token(role: str, secret: str = "test-secret-key-rbac") -> str:
    from backend.app.api.auth import create_access_token
    from unittest.mock import patch
    with patch.object(settings, "jwt_secret_key", secret):
        return create_access_token({"sub": "test-user", "role": role})


@pytest.mark.asyncio
async def test_admin_can_clear_cache(jwt_mode):
    token = _make_token("admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/cache/clear",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_clear_cache(jwt_mode):
    token = _make_token("viewer")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/cache/clear",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyst_cannot_clear_cache(jwt_mode):
    token = _make_token("analyst")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/cache/clear",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_predict_risk(jwt_mode):
    token = _make_token("analyst")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/risk/predict",
            json={
                "entity_id": "vendor-1",
                "features": {"days_since_last_audit": 100, "compliance_score": 80, "open_incidents": 1},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_predict_risk(jwt_mode):
    """Admin has higher level than analyst — should pass."""
    token = _make_token("admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/risk/predict",
            json={
                "entity_id": "vendor-2",
                "features": {"days_since_last_audit": 50, "compliance_score": 90, "open_incidents": 0},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_predict_risk(jwt_mode):
    token = _make_token("viewer")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/risk/predict",
            json={
                "entity_id": "vendor-3",
                "features": {"days_since_last_audit": 300, "compliance_score": 40, "open_incidents": 5},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_missing_auth_header(jwt_mode):
    """No Bearer token → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/cache/clear", json={})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_structured_error_on_forbidden(jwt_mode):
    """RBAC denials return structured JSON error."""
    token = _make_token("viewer")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/cache/clear",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "FORBIDDEN"
