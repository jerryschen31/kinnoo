from __future__ import annotations

from typing import Protocol

from server.metadata.models import AgentIndex, GlobalIndex, VersionMetadata


class MetadataManagerProtocol(Protocol):
    def upsert_version_metadata(self, metadata: VersionMetadata) -> tuple[VersionMetadata, AgentIndex, GlobalIndex]: ...

    def get_version_metadata(self, *, tenant_slug: str, agent_slug: str, version: str) -> VersionMetadata | None: ...

    def get_agent_index(self, *, tenant_slug: str, agent_slug: str) -> AgentIndex | None: ...

    def get_global_index(self) -> GlobalIndex | None: ...

    def get_tenant_storage_usage(self, *, tenant_slug: str) -> tuple[int, int] | None: ...
