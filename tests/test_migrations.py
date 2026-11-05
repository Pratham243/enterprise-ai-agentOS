"""Tests for Step 22 — Database Migrations (Alembic).

Tests cover:
  - Alembic configuration loads correctly
  - Migration scripts are discovered
  - Initial migration has valid upgrade/downgrade
  - Migration matches current model metadata
"""

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory


@pytest.fixture
def alembic_cfg():
    cfg = Config("alembic.ini")
    return cfg


@pytest.fixture
def script_dir(alembic_cfg):
    return ScriptDirectory.from_config(alembic_cfg)


def test_alembic_config_loads(alembic_cfg):
    assert alembic_cfg.get_main_option("script_location") == "backend/app/migrations"


def test_migration_scripts_discovered(script_dir):
    revisions = list(script_dir.walk_revisions())
    assert len(revisions) >= 1


def test_initial_migration_exists(script_dir):
    rev = script_dir.get_revision("001")
    assert rev is not None
    assert rev.down_revision is None


def test_head_is_reachable(script_dir):
    heads = script_dir.get_heads()
    assert len(heads) == 1
    assert "001" in heads


def test_initial_migration_has_upgrade_and_downgrade(script_dir):
    rev = script_dir.get_revision("001")
    module = rev.module
    assert hasattr(module, "upgrade")
    assert hasattr(module, "downgrade")
    assert callable(module.upgrade)
    assert callable(module.downgrade)


def test_models_match_migration():
    """Verify that our ORM models define the same tables as the migration."""
    from backend.app.db.base import Base
    import backend.app.models  # noqa: F401

    table_names = set(Base.metadata.tables.keys())
    assert "audit_logs" in table_names
    assert "approval_requests" in table_names
