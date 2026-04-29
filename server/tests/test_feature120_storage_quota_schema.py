from __future__ import annotations

from pathlib import Path

from server.database.models.agent_version import AgentVersion
from server.database.models.tenant import FREE_TIER_QUOTA_BYTES, Tenant


def test_feature120_test749_storage_quota_schema_fields_exist() -> None:
    agent_columns = AgentVersion.__table__.c
    tenant_columns = Tenant.__table__.c

    assert "archive_size_bytes" in agent_columns
    assert "used_bytes" in tenant_columns
    assert "quota_bytes" in tenant_columns

    quota_default = tenant_columns["quota_bytes"].default
    assert quota_default is not None
    assert quota_default.arg == FREE_TIER_QUOTA_BYTES


def test_feature120_test749_storage_quota_migration_contains_usage_triggers() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "database" / "migrations" / "versions"
    migration_files = sorted(versions_dir.glob("*_storage_quota.py"))

    assert len(migration_files) == 1, (
        "Expected exactly one storage quota migration, found "
        f"{len(migration_files)}: {[path.name for path in migration_files]}"
    )

    migration = migration_files[0].read_text(encoding="utf-8")

    assert "archive_size_bytes" in migration
    assert "used_bytes" in migration
    assert "quota_bytes" in migration
    assert "refresh_tenant_storage_usage" in migration
    assert "trg_refresh_tenant_storage_usage_agent_versions" in migration
