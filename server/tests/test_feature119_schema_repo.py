from __future__ import annotations

from sqlalchemy import create_engine, inspect

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.models import VersionMetadata, utc_now_iso


def test_feature119_test723_schema_and_repository_contract(migrated_postgres_database: str) -> None:
    engine = create_engine(migrated_postgres_database, future=True)
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    expected = {
        "users",
        "tenants",
        "tenant_members",
        "agents",
        "agent_versions",
        "api_keys",
        "audit_log",
        "download_events",
    }
    assert expected.issubset(table_names)

    runtime = create_database_runtime(
        database_url=migrated_postgres_database,
        pool_size=5,
        max_overflow=5,
        pool_recycle_seconds=1800,
    )
    repository = RegistryRepository(session_factory=runtime.sync_session_factory)
    now = utc_now_iso()
    metadata = VersionMetadata(
        tenant_slug="tenant-a",
        agent_slug="agent-a",
        version="1.0.0",
        visibility="private",
        manifest={"name": "agent-a", "version": "1.0.0"},
        storage_keys={"archive": "archives/tenant-a/agent-a/1.0.0.kno"},
        integrity={"sha256": "abc"},
        publisher={"user_id": "tester"},
        created_at=now,
        updated_at=now,
    )
    repository.upsert_version_metadata(metadata)
    loaded = repository.get_version_metadata(tenant_slug="tenant-a", agent_slug="agent-a", version="1.0.0")
    assert loaded is not None
    assert loaded.manifest["name"] == "agent-a"
    index = repository.get_agent_index(tenant_slug="tenant-a", agent_slug="agent-a")
    assert index is not None
    assert tuple(item.version for item in index.versions) == ("1.0.0",)
