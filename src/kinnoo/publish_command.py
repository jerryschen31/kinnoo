"""Publish command implementation for local registry flows."""

from __future__ import annotations

import os
from pathlib import Path

from .inspect_command import read_manifest_from_kno_archive
from .registry import RegistryService
from .registry_backends import LocalFilesystemRegistryBackend
from .validator import validate_manifest_data


def publish_archive(archive_path: str, use_local: bool = False) -> int:
    """Publish a `.kno` archive into the selected registry backend.

    For feature12 task70, `--local` is accepted as an explicit forward-compatible
    backend selection flag while local backend remains the default behavior.
    """
    archive = Path(archive_path)

    if not archive.exists():
        print(f"Error: Archive not found: {archive}")
        return 1
    if not archive.is_file():
        print(f"Error: Archive path is not a file: {archive}")
        return 1

    manifest_data = read_manifest_from_kno_archive(archive)
    if manifest_data is None:
        return 1

    is_valid, validation_errors = validate_manifest_data(manifest_data)
    if not is_valid:
        print("Error: Manifest validation failed for publish.")
        for error in validation_errors:
            print(f"- {error}")
        return 1

    name = str(manifest_data.get("name", "")).strip()
    version = str(manifest_data.get("version", "")).strip()

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None

    backend = LocalFilesystemRegistryBackend(root=backend_root)
    service = RegistryService(backend=backend)

    metadata_payload = {
        "name": name,
        "version": version,
        "description": manifest_data.get("description"),
        "author": manifest_data.get("author"),
        "license": manifest_data.get("license"),
    }

    try:
        record = service.publish(
            name=name,
            version=version,
            archive_path=archive,
            manifest_metadata=metadata_payload,
        )
    except FileExistsError as error:
        print(f"Error: {error}")
        return 1
    except OSError as error:
        print(f"Error: Failed to publish archive: {error}")
        return 1

    backend_label = "local" if use_local else "default-local"
    print(f"Published {record.name}=={record.version} ({backend_label})")
    print(f"Stored at: {record.archive_path}")
    return 0
