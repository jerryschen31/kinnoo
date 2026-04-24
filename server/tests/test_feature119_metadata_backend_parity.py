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


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test725_backend_parity(tmp_path, migrated_postgres_database: str, postgres_available: bool) -> None:
#     ...
