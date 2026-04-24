"""Postgres-backed metadata manager."""

from __future__ import annotations

from server.database.repository import RegistryRepository
from server.metadata.models import AgentIndex, GlobalIndex, VersionMetadata


class PostgresMetadataManager:
    """Metadata manager implementation backed by registry Postgres repository."""

    def __init__(self, *, repository: RegistryRepository) -> None:
        self._repository = repository

    def upsert_version_metadata(self, metadata: VersionMetadata) -> tuple[VersionMetadata, AgentIndex, GlobalIndex]:
        self._repository.upsert_version_metadata(metadata)
        agent_index = self._repository.get_agent_index(tenant_slug=metadata.tenant_slug, agent_slug=metadata.agent_slug)
        assert agent_index is not None
        return metadata, agent_index, self._repository.get_global_index()

    def get_version_metadata(self, *, tenant_slug: str, agent_slug: str, version: str) -> VersionMetadata | None:
        return self._repository.get_version_metadata(tenant_slug=tenant_slug, agent_slug=agent_slug, version=version)

    def get_agent_index(self, *, tenant_slug: str, agent_slug: str) -> AgentIndex | None:
        return self._repository.get_agent_index(tenant_slug=tenant_slug, agent_slug=agent_slug)

    def get_global_index(self) -> GlobalIndex | None:
        return self._repository.get_global_index()

    def get_tenant_storage_usage(self, *, tenant_slug: str) -> tuple[int, int]:
        return self._repository.get_tenant_storage_usage(tenant_slug=tenant_slug)
