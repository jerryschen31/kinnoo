from __future__ import annotations

from pathlib import Path

from server.database.models.agent_version import AgentVersion
from server.database.models.tenant_member import FREE_TIER_QUOTA_BYTES, TenantMember


def test_feature120_test749_storage_quota_schema_fields_exist() -> None:
    agent_columns = AgentVersion.__table__.c
    member_columns = TenantMember.__table__.c

    assert "archive_size_bytes" in agent_columns
    assert "used_bytes" in member_columns
    assert "quota_bytes" in member_columns

    quota_default = member_columns["quota_bytes"].default
    assert quota_default is not None
    assert quota_default.arg == FREE_TIER_QUOTA_BYTES


def test_feature120_test749_storage_quota_migration_contains_usage_triggers() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "versions"
        / "20260424_0002_storage_quota.py"
    ).read_text(encoding="utf-8")

    assert "archive_size_bytes" in migration
    assert "used_bytes" in migration
    assert "quota_bytes" in migration
    assert "refresh_tenant_storage_usage" in migration
    assert "trg_refresh_tenant_storage_usage_agent_versions" in migration
