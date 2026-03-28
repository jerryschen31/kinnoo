from __future__ import annotations

from server.metadata.manager import MetadataManager
from server.metadata.models import VersionMetadata, utc_now_iso
from server.storage.local import LocalStorageBackend


def test_metadata_model(tmp_path):
    storage = LocalStorageBackend(root=tmp_path / "storage")
    manager = MetadataManager(storage=storage)

    created_at = utc_now_iso()
    version_v1 = VersionMetadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
        version="1.0.0",
        visibility="private",
        manifest={"name": "agent-copilot", "version": "1.0.0"},
        storage_keys={"archive": "archives/tenant-alpha/agent-copilot/1.0.0/agent-copilot.kno"},
        integrity={"sha256": "abc123"},
        publisher={"user_id": "admin-1"},
        created_at=created_at,
        updated_at=created_at,
    )

    stored_version_v1, agent_index_v1, global_index_v1 = manager.upsert_version_metadata(version_v1)

    version_key_v1 = manager.version_metadata_key(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
        version="1.0.0",
    )
    assert version_key_v1 in storage.list_objects(prefix="metadata/")

    read_back_v1 = manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
        version="1.0.0",
    )
    assert read_back_v1 is not None
    assert read_back_v1.version == "1.0.0"
    assert stored_version_v1.schema_version == "v1"

    assert agent_index_v1.tenant_slug == "tenant-alpha"
    assert agent_index_v1.agent_slug == "agent-copilot"
    assert tuple(item.version for item in agent_index_v1.versions) == ("1.0.0",)
    assert agent_index_v1.schema_version == "v1"

    tenant_summaries_v1 = global_index_v1.tenants["tenant-alpha"]
    assert len(tenant_summaries_v1) == 1
    assert tenant_summaries_v1[0].latest_version == "1.0.0"
    assert global_index_v1.schema_version == "v1"

    version_v2 = VersionMetadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
        version="1.1.0",
        visibility="private",
        manifest={"name": "agent-copilot", "version": "1.1.0"},
        storage_keys={"archive": "archives/tenant-alpha/agent-copilot/1.1.0/agent-copilot.kno"},
        integrity={"sha256": "def456"},
        publisher={"user_id": "admin-1"},
        created_at=created_at,
        updated_at=utc_now_iso(),
    )

    _, agent_index_v2, global_index_v2 = manager.upsert_version_metadata(version_v2)

    assert tuple(item.version for item in agent_index_v2.versions) == ("1.0.0", "1.1.0")
    tenant_summaries_v2 = global_index_v2.tenants["tenant-alpha"]
    assert len(tenant_summaries_v2) == 1
    assert tenant_summaries_v2[0].latest_version == "1.1.0"
    assert global_index_v2.schema_version == "v1"
