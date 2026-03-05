"""Publish command implementation for local registry flows."""

from __future__ import annotations

import os
from pathlib import Path
import zipfile

import yaml

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

    manifest_data = _read_manifest_from_archive(archive)
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

    try:
        record = service.publish(name=name, version=version, archive_path=archive)
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


def _read_manifest_from_archive(archive_path: Path) -> dict | None:
    try:
        with zipfile.ZipFile(archive_path, "r") as archive_zip:
            try:
                manifest_bytes = archive_zip.read("kinnoo.yaml")
            except KeyError:
                print("Error: Archive is missing required file: kinnoo.yaml")
                return None
    except zipfile.BadZipFile:
        print(f"Error: Invalid archive format: {archive_path}")
        return None
    except OSError as error:
        print(f"Error: Unable to read archive: {error}")
        return None

    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError:
        print("Error: Unable to decode kinnoo.yaml from archive as UTF-8")
        return None

    try:
        parsed = yaml.safe_load(manifest_text)
    except yaml.YAMLError as error:
        print(f"Error: Failed to parse kinnoo.yaml in archive: {error}")
        return None

    if not isinstance(parsed, dict):
        print("Error: Manifest must be a YAML mapping (dict) at the top level.")
        return None
    return parsed
