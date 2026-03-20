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

        if not results:
            print(f"No remote registry matches found for query: {query_text}")
            return 0

        print(f"Remote registry search results for: {query_text}")
        for summary in results:
            description = summary.description if summary.description else "(no description)"
            print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

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
        description = summary.description if summary.description else "(no description)"
        print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

    return 0
