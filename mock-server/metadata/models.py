"""Schema-versioned metadata models for remote registry indexing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION_V1 = "v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class VersionMetadata:
    """Source-of-truth metadata for one tenant/agent/version tuple."""

    tenant_slug: str
    agent_slug: str
    version: str
    visibility: str
    manifest: dict[str, Any]
    storage_keys: dict[str, str]
    integrity: dict[str, str]
    publisher: dict[str, Any]
    created_at: str
    updated_at: str
    schema_version: str = SCHEMA_VERSION_V1

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tenant_slug": self.tenant_slug,
            "agent_slug": self.agent_slug,
            "version": self.version,
            "visibility": self.visibility,
            "manifest": self.manifest,
            "storage_keys": self.storage_keys,
            "integrity": self.integrity,
            "publisher": self.publisher,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "VersionMetadata":
        return cls(
            schema_version=str(document.get("schema_version", SCHEMA_VERSION_V1)),
            tenant_slug=str(document["tenant_slug"]),
            agent_slug=str(document["agent_slug"]),
            version=str(document["version"]),
            visibility=str(document.get("visibility", "private")),
            manifest=dict(document.get("manifest", {})),
            storage_keys=dict(document.get("storage_keys", {})),
            integrity=dict(document.get("integrity", {})),
            publisher=dict(document.get("publisher", {})),
            created_at=str(document.get("created_at", utc_now_iso())),
            updated_at=str(document.get("updated_at", utc_now_iso())),
        )


@dataclass(frozen=True)
class AgentVersionSummary:
    version: str
    created_at: str
    updated_at: str
    integrity: dict[str, str]

    def to_document(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "integrity": self.integrity,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "AgentVersionSummary":
        return cls(
            version=str(document["version"]),
            created_at=str(document["created_at"]),
            updated_at=str(document["updated_at"]),
            integrity=dict(document.get("integrity", {})),
        )


@dataclass(frozen=True)
class AgentIndex:
    """Per-agent version index derived from VersionMetadata documents."""

    tenant_slug: str
    agent_slug: str
    visibility: str
    versions: tuple[AgentVersionSummary, ...]
    schema_version: str = SCHEMA_VERSION_V1

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tenant_slug": self.tenant_slug,
            "agent_slug": self.agent_slug,
            "visibility": self.visibility,
            "versions": [item.to_document() for item in self.versions],
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "AgentIndex":
        raw_versions = document.get("versions", [])
        return cls(
            schema_version=str(document.get("schema_version", SCHEMA_VERSION_V1)),
            tenant_slug=str(document["tenant_slug"]),
            agent_slug=str(document["agent_slug"]),
            visibility=str(document.get("visibility", "private")),
            versions=tuple(AgentVersionSummary.from_document(item) for item in raw_versions),
        )


@dataclass(frozen=True)
class GlobalAgentSummary:
    agent_slug: str
    visibility: str
    latest_version: str
    latest_updated_at: str

    def to_document(self) -> dict[str, Any]:
        return {
            "agent_slug": self.agent_slug,
            "visibility": self.visibility,
            "latest_version": self.latest_version,
            "latest_updated_at": self.latest_updated_at,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "GlobalAgentSummary":
        return cls(
            agent_slug=str(document["agent_slug"]),
            visibility=str(document.get("visibility", "private")),
            latest_version=str(document.get("latest_version", "")),
            latest_updated_at=str(document.get("latest_updated_at", "")),
        )


@dataclass(frozen=True)
class GlobalIndex:
    """Top-level tenant->agent summary index for search/list operations."""

    generated_at: str
    tenants: dict[str, tuple[GlobalAgentSummary, ...]] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION_V1

    def to_document(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "tenants": {
                tenant: [summary.to_document() for summary in summaries]
                for tenant, summaries in self.tenants.items()
            },
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "GlobalIndex":
        tenants_raw = document.get("tenants", {})
        tenants: dict[str, tuple[GlobalAgentSummary, ...]] = {}
        for tenant_slug, summaries in tenants_raw.items():
            tenants[str(tenant_slug)] = tuple(
                GlobalAgentSummary.from_document(item) for item in summaries
            )

        return cls(
            schema_version=str(document.get("schema_version", SCHEMA_VERSION_V1)),
            generated_at=str(document.get("generated_at", utc_now_iso())),
            tenants=tenants,
        )
