"""List command implementation for local registry inventory."""

from __future__ import annotations

import os
from pathlib import Path

from .registry import RegistryService
from .registry_backends import LocalFilesystemRegistryBackend


def list_agents() -> int:
    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None

    backend = LocalFilesystemRegistryBackend(root=backend_root)
    service = RegistryService(backend=backend)
    summaries = service.list_latest_agents()

    if not summaries:
        print("No agents found in local registry.")
        return 0

    print("Local registry agents:")
    for summary in summaries:
        description = summary.description if summary.description else "(no description)"
        print(f"- {summary.name} | latest: {summary.latest_version} | description: {description}")

    return 0
