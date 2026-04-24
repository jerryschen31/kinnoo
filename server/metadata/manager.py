"""Metadata manager for three-tier JSON index documents."""

from __future__ import annotations

import hashlib
import json
from typing import Callable

from server.metadata.models import (
    AgentIndex,
    AgentVersionSummary,
    GlobalAgentSummary,
    GlobalIndex,
    VersionMetadata,
    utc_now_iso,
)
from server.storage.base import StorageBackend


class MetadataManager:
    """Read/write metadata documents via configured storage backend."""

    def __init__(self, *, storage: StorageBackend, max_global_index_retries: int = 3) -> None:
        self._storage = storage
        self._max_global_index_retries = max_global_index_retries

    @staticmethod
    def version_metadata_key(*, tenant_slug: str, agent_slug: str, version: str) -> str:
        return f"metadata/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}.v1.json"

    @staticmethod
    def agent_index_key(*, tenant_slug: str, agent_slug: str) -> str:
        return f"metadata/tenants/{tenant_slug}/agents/{agent_slug}/index.v1.json"

    @staticmethod
    def global_index_key() -> str:
        return "metadata/global/index.v1.json"

    def put_version_metadata(self, metadata: VersionMetadata) -> None:
        key = self.version_metadata_key(
            tenant_slug=metadata.tenant_slug,
            agent_slug=metadata.agent_slug,
            version=metadata.version,
        )
        self._put_json(key=key, payload=metadata.to_document())

    def get_version_metadata(self, *, tenant_slug: str, agent_slug: str, version: str) -> VersionMetadata | None:
        key = self.version_metadata_key(tenant_slug=tenant_slug, agent_slug=agent_slug, version=version)
        payload = self._get_json_optional(key)
        if payload is None:
            return None
        return VersionMetadata.from_document(payload)

    def put_agent_index(self, index: AgentIndex) -> None:
        key = self.agent_index_key(tenant_slug=index.tenant_slug, agent_slug=index.agent_slug)
        self._put_json(key=key, payload=index.to_document())

    def get_agent_index(self, *, tenant_slug: str, agent_slug: str) -> AgentIndex | None:
        key = self.agent_index_key(tenant_slug=tenant_slug, agent_slug=agent_slug)
        payload = self._get_json_optional(key)
        if payload is None:
            return None
        return AgentIndex.from_document(payload)

    def put_global_index(self, index: GlobalIndex) -> None:
        self._put_json(key=self.global_index_key(), payload=index.to_document())

    def get_global_index(self) -> GlobalIndex | None:
        payload = self._get_json_optional(self.global_index_key())
        if payload is None:
            return None
        return GlobalIndex.from_document(payload)

    def get_tenant_storage_usage(self, *, tenant_slug: str) -> tuple[int, int] | None:
        _ = tenant_slug
        return None

    def upsert_version_metadata(self, metadata: VersionMetadata) -> tuple[VersionMetadata, AgentIndex, GlobalIndex]:
        self.put_version_metadata(metadata)
        updated_agent_index = self._upsert_agent_index_from_version(metadata)
        updated_global_index = self._upsert_global_index_from_agent(updated_agent_index)
        return metadata, updated_agent_index, updated_global_index

    def _upsert_agent_index_from_version(self, metadata: VersionMetadata) -> AgentIndex:
        current = self.get_agent_index(tenant_slug=metadata.tenant_slug, agent_slug=metadata.agent_slug)
        by_version: dict[str, AgentVersionSummary] = {}
        if current is not None:
            by_version.update({item.version: item for item in current.versions})

        by_version[metadata.version] = AgentVersionSummary(
            version=metadata.version,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            integrity=metadata.integrity,
        )
        sorted_versions = tuple(sorted(by_version.values(), key=lambda item: item.version))

        index = AgentIndex(
            tenant_slug=metadata.tenant_slug,
            agent_slug=metadata.agent_slug,
            visibility=metadata.visibility,
            versions=sorted_versions,
        )
        self.put_agent_index(index)
        return index

    def _upsert_global_index_from_agent(self, index: AgentIndex) -> GlobalIndex:
        def mutator(current: GlobalIndex) -> GlobalIndex:
            tenants = {tenant: list(summaries) for tenant, summaries in current.tenants.items()}
            tenant_summaries = tenants.setdefault(index.tenant_slug, [])

            latest = max(index.versions, key=lambda item: item.updated_at)
            new_summary = GlobalAgentSummary(
                agent_slug=index.agent_slug,
                visibility=index.visibility,
                latest_version=latest.version,
                latest_updated_at=latest.updated_at,
            )

            replaced = False
            for idx, existing in enumerate(tenant_summaries):
                if existing.agent_slug == index.agent_slug:
                    tenant_summaries[idx] = new_summary
                    replaced = True
                    break
            if not replaced:
                tenant_summaries.append(new_summary)

            normalized = {
                tenant: tuple(sorted(summaries, key=lambda item: item.agent_slug))
                for tenant, summaries in tenants.items()
            }
            return GlobalIndex(generated_at=utc_now_iso(), tenants=normalized)

        return self._update_global_index_atomic(mutator)

    def _update_global_index_atomic(self, mutator: Callable[[GlobalIndex], GlobalIndex]) -> GlobalIndex:
        for _attempt in range(self._max_global_index_retries):
            baseline_bytes = self._get_raw_optional(self.global_index_key())
            baseline_hash = _sha256_hex(baseline_bytes) if baseline_bytes is not None else None

            if baseline_bytes is None:
                current = GlobalIndex(generated_at=utc_now_iso(), tenants={})
            else:
                current = GlobalIndex.from_document(json.loads(baseline_bytes.decode("utf-8")))

            updated = mutator(current)

            latest_bytes = self._get_raw_optional(self.global_index_key())
            latest_hash = _sha256_hex(latest_bytes) if latest_bytes is not None else None
            # Best-effort optimistic retry if a concurrent writer changed global index.
            if latest_hash != baseline_hash:
                continue

            self._put_json(key=self.global_index_key(), payload=updated.to_document())
            return updated

        raise RuntimeError("Unable to update global metadata index after retries.")

    def _put_json(self, *, key: str, payload: dict) -> None:
        self._storage.put_object(
            key=key,
            data=json.dumps(payload, sort_keys=True, indent=2).encode("utf-8"),
            content_type="application/json",
        )

    def _get_json_optional(self, key: str) -> dict | None:
        raw = self._get_raw_optional(key)
        if raw is None:
            return None
        return json.loads(raw.decode("utf-8"))

    def _get_raw_optional(self, key: str) -> bytes | None:
        try:
            return self._storage.get_object(key=key)
        except FileNotFoundError:
            return None


def _sha256_hex(payload: bytes | None) -> str | None:
    if payload is None:
        return None
    return hashlib.sha256(payload).hexdigest()
