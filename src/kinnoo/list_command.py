"""List command implementation for local-archive and remote-registry inventory."""

from __future__ import annotations

import os
from pathlib import Path

from .config import load_registry_config
from .archive import LocalArchiveBackend
from .registry import RegistryService
from .registry_backends import MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient
from .size_format import format_size_human_readable


def list_agents(source: str = "local") -> int:
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
            # Preserve existing remote-mode behavior for local mock workflows.
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
            archive_size = _format_archive_size(summary.archive_size_bytes)
            print(
                f"- {summary.name} | latest: {summary.latest_version} | "
                f"description: {description} | size: {archive_size}"
            )

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
        archive_size = _format_archive_size(summary.archive_size_bytes)
        print(
            f"- {summary.name} | latest: {summary.latest_version} | "
            f"description: {description} | size: {archive_size}"
        )

    return 0


def _format_archive_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "unknown"
    return format_size_human_readable(size_bytes)
