from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.models import VersionMetadata, utc_now_iso
from server.metadata.postgres_manager import PostgresMetadataManager


def test_feature119_test730_publish_search_concurrency(migrated_postgres_database: str, postgres_available: bool) -> None:
    if not postgres_available:
        pytest.skip("Postgres is not available")
    runtime = create_database_runtime(
        database_url=migrated_postgres_database,
        pool_size=5,
        max_overflow=5,
        pool_recycle_seconds=1800,
    )
    manager = PostgresMetadataManager(repository=RegistryRepository(session_factory=runtime.sync_session_factory))

    def _write(version: str) -> None:
        now = utc_now_iso()
        metadata = VersionMetadata(
            tenant_slug="tenant-concurrency",
            agent_slug="agent-concurrency",
            version=version,
            visibility="public",
            manifest={"name": "agent-concurrency", "version": version},
            storage_keys={"archive": f"archives/tenant-concurrency/agent-concurrency/{version}.kno"},
            integrity={"sha256": version},
            publisher={"user_id": "concurrent"},
            created_at=now,
            updated_at=now,
        )
        manager.upsert_version_metadata(metadata)

    versions = [f"1.0.{idx}" for idx in range(10)]
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(_write, versions))

    index = manager.get_agent_index(tenant_slug="tenant-concurrency", agent_slug="agent-concurrency")
    assert index is not None
    assert len(index.versions) == len(versions)
