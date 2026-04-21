from __future__ import annotations

import pytest

from server.database.repository import RegistryRepository
from server.database.session import create_database_runtime
from server.metadata.manager import MetadataManager
from server.metadata.models import VersionMetadata, utc_now_iso
from server.metadata.postgres_manager import PostgresMetadataManager
from server.storage.local import LocalStorageBackend


def _sample_metadata() -> VersionMetadata:
    now = utc_now_iso()
    return VersionMetadata(
        tenant_slug="tenant-parity",
        agent_slug="agent-parity",
        version="1.0.0",
        visibility="public",
        manifest={"name": "agent-parity", "version": "1.0.0"},
        storage_keys={"archive": "archives/tenant-parity/agent-parity/1.0.0.kno"},
        integrity={"sha256": "parity"},
        publisher={"user_id": "parity-user"},
        created_at=now,
        updated_at=now,
    )


def test_feature119_test725_backend_parity(tmp_path, migrated_postgres_database: str, postgres_available: bool) -> None:
    if not postgres_available:
        pytest.skip("Postgres is not available")

    json_manager = MetadataManager(storage=LocalStorageBackend(root=tmp_path / "storage"))
    runtime = create_database_runtime(
        database_url=migrated_postgres_database,
        pool_size=5,
        max_overflow=5,
        pool_recycle_seconds=1800,
    )
    postgres_manager = PostgresMetadataManager(repository=RegistryRepository(session_factory=runtime.sync_session_factory))

    metadata = _sample_metadata()
    json_manager.upsert_version_metadata(metadata)
    postgres_manager.upsert_version_metadata(metadata)

    json_loaded = json_manager.get_version_metadata(tenant_slug=metadata.tenant_slug, agent_slug=metadata.agent_slug, version=metadata.version)
    postgres_loaded = postgres_manager.get_version_metadata(
        tenant_slug=metadata.tenant_slug,
        agent_slug=metadata.agent_slug,
        version=metadata.version,
    )
    assert json_loaded is not None
    assert postgres_loaded is not None
    assert json_loaded.to_document() == postgres_loaded.to_document()
