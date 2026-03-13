"""Publish command implementation for archive-source registry publish flows."""

from __future__ import annotations

import re
import os
import shutil
from pathlib import Path

from .archive import LocalArchiveBackend
from .checksum import checksum_sidecar_path_for_archive
from .inspect_command import read_manifest_from_kno_archive
from .registry import RegistryService
from .registry_backends import MockFilesystemRegistryBackend
from .schema import NAME_PATTERN
from .validator import validate_manifest_data


def _publish_validated_archive(
    *,
    archive: Path,
    expected_name: str | None,
    expected_version: str | None,
    use_local: bool,
) -> int:
    source_sidecar_path = checksum_sidecar_path_for_archive(archive)
    manifest_data = read_manifest_from_kno_archive(archive)
    if manifest_data is None:
        print("Error: Failed to read manifest metadata from resolved local archive source.")
        return 1

    is_valid, validation_errors = validate_manifest_data(manifest_data)
    if not is_valid:
        print("Error: Manifest validation failed for resolved local archive source.")
        for error in validation_errors:
            print(f"- {error}")
        return 1

    name = str(manifest_data.get("name", "")).strip()
    version = str(manifest_data.get("version", "")).strip()

    if expected_name is not None and name != expected_name:
        print(
            "Error: Archive metadata mismatch for resolved source. "
            f"Requested '{expected_name}' but archive manifest name is '{name}'."
        )
        return 1

    if expected_version is not None and version != expected_version:
        print(
            "Error: Archive metadata mismatch for resolved source. "
            f"Expected {expected_name}=={expected_version} but got {name}=={version}."
        )
        return 1

    registry_root = os.environ.get("KINNOO_REGISTRY_ROOT")
    backend_root = Path(registry_root).expanduser() if registry_root else None

    backend = MockFilesystemRegistryBackend(root=backend_root)
    service = RegistryService(backend=backend)

    target_archive_path = backend.registry_version_path(name=name, version=version) / f"{name}.kno"
    tagged_exists_before_publish = target_archive_path.exists()
    existing_untagged_dirs_before = {
        path.name
        for path in (backend.root / name).iterdir()
        if path.is_dir() and path.name.startswith("untagged-")
    } if (backend.root / name).exists() else set()

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

    backend_label = "local" if use_local else "default-mock"
    print(f"Published {record.name}=={record.version} ({backend_label})")
    print(f"Source archive: {archive}")
    print(f"Target registry path: {record.archive_path}")

    target_sidecar_path = checksum_sidecar_path_for_archive(record.archive_path)
    if source_sidecar_path.exists() and source_sidecar_path.is_file():
        try:
            shutil.copy2(source_sidecar_path, target_sidecar_path)
        except OSError as error:
            print(f"Error: Failed to publish checksum sidecar: {error}")
            return 1
        print(f"Published checksum sidecar: {target_sidecar_path}")
    else:
        print("Published checksum sidecar: (none found at source)")

    if tagged_exists_before_publish:
        untagged_root = backend.root / name
        new_untagged_dirs = []
        if untagged_root.exists():
            new_untagged_dirs = sorted(
                [
                    path
                    for path in untagged_root.iterdir()
                    if path.is_dir()
                    and path.name.startswith("untagged-")
                    and path.name not in existing_untagged_dirs_before
                ],
                key=lambda path: int(path.name.split("untagged-", 1)[1])
                if path.name.split("untagged-", 1)[1].isdigit()
                else 0,
            )

        if new_untagged_dirs:
            rollover_archive = new_untagged_dirs[-1] / f"{name}.kno"
            print(f"Rollover archived previous tagged artifact to: {rollover_archive}")

    return 0


def publish_agent(agent_name: str, use_local: bool = False) -> int:
    """Publish latest archived artifact for agent name to selected registry backend.

    For feature13 task83, publish source resolution is name-based from the local
    archive backend rather than direct archive path input.
    """
    normalized_name = agent_name.strip()

    legacy_archive_candidate = Path(normalized_name).expanduser()
    if (
        legacy_archive_candidate.exists()
        and legacy_archive_candidate.is_file()
        and legacy_archive_candidate.suffix.lower() == ".kno"
    ):
        return _publish_validated_archive(
            archive=legacy_archive_candidate,
            expected_name=None,
            expected_version=None,
            use_local=use_local,
        )

    if not normalized_name:
        print("Error: Agent name cannot be empty.")
        return 1
    if not re.fullmatch(NAME_PATTERN, normalized_name):
        print(f"Error: Invalid agent name '{normalized_name}'.")
        return 1

    archive_root = Path.home() / ".kinnoo" / "archive"
    archive_backend = LocalArchiveBackend(root=Path(os.environ.get("KINNOO_ARCHIVE_ROOT", archive_root)))
    source_record = archive_backend.resolve_latest(name=normalized_name)
    if source_record is None:
        agent_archive_dir = archive_backend.root / normalized_name
        if not agent_archive_dir.exists() or not agent_archive_dir.is_dir():
            print(
                f"Error: Local archive source for agent '{normalized_name}' was not found at {agent_archive_dir}."
            )
            return 1

        available_versions = sorted(path.name for path in agent_archive_dir.iterdir() if path.is_dir())
        if available_versions:
            print(
                f"Error: Local archive source for agent '{normalized_name}' has no publishable .kno artifacts."
            )
        else:
            print(f"Error: Local archive source for agent '{normalized_name}' has no versions.")
        return 1

    archive = source_record.archive_path
    if not archive.exists() or not archive.is_file():
        print(f"Error: Resolved source archive is missing or invalid: {archive}")
        return 1

    return _publish_validated_archive(
        archive=archive,
        expected_name=source_record.name,
        expected_version=source_record.version,
        use_local=use_local,
    )
