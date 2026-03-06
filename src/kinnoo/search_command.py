"""Search command implementation for local registry inventory."""

from __future__ import annotations

import os
from pathlib import Path

from .registry import RegistryService
from .registry_backends import LocalFilesystemRegistryBackend


def search_agents(query: str) -> int:
    query_text = query.strip()
    if not query_text:
        print("Error: Search query cannot be empty.")
        return 1

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None

    backend = LocalFilesystemRegistryBackend(root=backend_root)
    service = RegistryService(backend=backend)
    results = service.search_agents(query=query_text)

    if not results:
        print(f"No local registry matches found for query: {query_text}")
        return 0

    print(f"Local registry search results for: {query_text}")
    for summary in results:
        description = summary.description if summary.description else "(no description)"
        print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

    return 0
