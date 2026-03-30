"""Search command implementation for local-archive and remote-registry inventory."""

from __future__ import annotations

import os
from pathlib import Path

from .config import load_registry_config
from .archive import LocalArchiveBackend
from .registry import RegistryService
from .registry_backends import MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient


def search_agents(query: str, source: str = "local") -> int:
    query_text = query.strip()
    if not query_text:
        print("Error: Search query cannot be empty.")
        return 1

    query_normalized = query_text.lower()

    config = load_registry_config()
    effective_source = source
    if source == "auto":
        effective_source = "remote" if config.registry_url else "local"

    if effective_source == "remote":
        if config.registry_url and config.registry_token and config.tenant_slug:
            service = RegistryService(
                backend=RemoteRegistryClient(
                    base_url=config.registry_url,
                    token=config.registry_token,
                    tenant_slug=config.tenant_slug,
                )
            )
        elif config.registry_url:
            print(
                "Error: Remote registry URL is configured but token/tenant settings are missing.",
            )
            return 1
        else:
            registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
            backend_root = Path(registry_root).expanduser() if registry_root else None
            backend = MockFilesystemRegistryBackend(root=backend_root)
            service = RegistryService(backend=backend)

        results = service.search_agents(query=query_text)
        mirror_results = [
            record
            for record in service.list_clawhub_mirror_records()
            if _mirror_record_matches_query(record, query_normalized)
        ]

        if not results and not mirror_results:
            print(f"No remote registry matches found for query: {query_text}")
            return 0

        print(f"Remote registry search results for: {query_text}")
        for summary in results:
            description = _summary_text(summary=summary, field="description", default="(no description)")
            name = _summary_text(summary=summary, field="name", default="(unknown)")
            latest_version = _summary_text(summary=summary, field="latest_version", default="(unknown)")
            print(f"- {name} | latest: {latest_version} | description: {description}")

        for record in mirror_results:
            metadata_value = _mirror_value(record=record, field="metadata")
            description = "(no description)"
            if isinstance(metadata_value, dict):
                description = str(metadata_value.get("description") or "(no description)")

            source_slug = str(
                _mirror_value(record=record, field="source_slug")
                or _mirror_value(record=record, field="agent_slug")
                or "(unknown)"
            )
            source_version = str(
                _mirror_value(record=record, field="source_version")
                or _mirror_value(record=record, field="version")
                or "(unknown)"
            )
            synced_at = str(_mirror_value(record=record, field="synced_at") or "(unknown)")
            mirror_name = str(_mirror_value(record=record, field="name") or "(unknown)")
            print(
                "- "
                f"{mirror_name} | latest: {source_version} | "
                f"description: {description} | source: clawhub (mirrored) | "
                f"slug: {source_slug} | synced_at: {synced_at}"
            )

        return 0

    archive_root = os.environ.get("KINNOO_ARCHIVE_ROOT")
    backend_root = Path(archive_root).expanduser() if archive_root else None

    backend = LocalArchiveBackend(root=backend_root)
    summaries = backend.list_latest_agents()
    results = [
        summary
        for summary in summaries
        if query_normalized in summary.name.lower()
        or query_normalized in summary.description.lower()
    ]

    if not results:
        print(f"No local archive matches found for query: {query_text}")
        return 0

    print(f"Local archive search results for: {query_text}")
    for summary in results:
        description = _summary_text(summary=summary, field="description", default="(no description)")
        name = _summary_text(summary=summary, field="name", default="(unknown)")
        latest_version = _summary_text(summary=summary, field="latest_version", default="(unknown)")
        print(f"- {name} | latest: {latest_version} | description: {description}")

    return 0


def _summary_text(*, summary: object, field: str, default: str) -> str:
    value = _summary_value(summary=summary, field=field)
    if value in (None, ""):
        return default
    return str(value)


def _summary_value(*, summary: object, field: str) -> object | None:
    if isinstance(summary, dict):
        return summary.get(field)
    return getattr(summary, field, None)


def _mirror_record_matches_query(record: object, query_normalized: str) -> bool:
    haystack = [
        str(_mirror_value(record=record, field="name") or "").lower(),
        str(_mirror_value(record=record, field="agent_slug") or "").lower(),
        str(_mirror_value(record=record, field="source_slug") or "").lower(),
        str(_mirror_value(record=record, field="source_version") or "").lower(),
        str(_mirror_value(record=record, field="source_url") or "").lower(),
        "clawhub",
    ]
    return any(query_normalized in value for value in haystack)


def _mirror_value(*, record: object, field: str) -> object | None:
    if isinstance(record, dict):
        return record.get(field)
    return getattr(record, field, None)
