"""List command implementation for local-archive and remote-registry inventory."""

from __future__ import annotations

import os
from pathlib import Path

from .archive import LocalArchiveBackend
from .registry import RegistryService
from .registry_backends import MockFilesystemRegistryBackend


def list_agents(source: str = "local") -> int:
    if source == "remote":
        registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
        backend_root = Path(registry_root).expanduser() if registry_root else None

        backend = MockFilesystemRegistryBackend(root=backend_root)
        service = RegistryService(backend=backend)
        summaries = service.list_latest_agents()

        if not summaries:
            print("No agents found in remote registry.")
            return 0

        print("Remote registry agents:")
        for summary in summaries:
            description = summary.description if summary.description else "(no description)"
            print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

        return 0

    archive_root = os.environ.get("KINNOO_ARCHIVE_ROOT")
    backend_root = Path(archive_root).expanduser() if archive_root else None

    backend = LocalArchiveBackend(root=backend_root)
    summaries = backend.list_latest_agents()

    if not summaries:
        print("No agents found in local archive.")
        return 0

    print("Local archive agents:")
    for summary in summaries:
        description = summary.description if summary.description else "(no description)"
        print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

    return 0
