"""Concrete registry backend implementations."""

from __future__ import annotations

import shutil
import json
from pathlib import Path
from typing import Any, Optional

from .registry import RegistryRecord


DEFAULT_LOCAL_REGISTRY_ROOT = Path.home() / ".kinnoo" / "registry"


class LocalFilesystemRegistryBackend:
    """Local filesystem backend rooted at ~/.kinnoo/registry by default."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or DEFAULT_LOCAL_REGISTRY_ROOT).expanduser()

    def registry_version_path(self, *, name: str, version: str) -> Path:
        return self.root / name / version

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
    ) -> RegistryRecord:
        source_archive = Path(archive_path)
        if not source_archive.exists():
            raise FileNotFoundError(f"Archive not found: {source_archive}")

        target_dir = self.registry_version_path(name=name, version=version)
        if target_dir.exists():
            raise FileExistsError(
                f"Registry already contains published version '{name}=={version}'. "
                "Refusing to overwrite existing entry."
            )

        target_dir.mkdir(parents=True, exist_ok=True)
        target_archive = target_dir / source_archive.name

        shutil.copy2(source_archive, target_archive)

        metadata_path: Path | None = None
        if manifest_metadata is not None:
            metadata_path = target_dir / "manifest-metadata.json"
            with metadata_path.open("w", encoding="utf-8") as metadata_file:
                json.dump(manifest_metadata, metadata_file, sort_keys=True, indent=2)

        return RegistryRecord(
            name=name,
            version=version,
            archive_path=target_archive,
            metadata_path=metadata_path,
        )

    def resolve(self, *, name: str, version: Optional[str] = None) -> Optional[RegistryRecord]:
        if version:
            return self._resolve_exact(name=name, version=version)

        versions = self._discover_versions(name)
        if not versions:
            return None
        return self._resolve_exact(name=name, version=versions[0])

    def list_entries(self) -> list[RegistryRecord]:
        records: list[RegistryRecord] = []
        if not self.root.exists():
            return records

        for agent_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            versions = self._discover_versions(agent_dir.name)
            for version in versions:
                record = self._resolve_exact(name=agent_dir.name, version=version)
                if record is not None:
                    records.append(record)
        return records

    def search(self, *, query: str) -> list[RegistryRecord]:
        query_normalized = query.strip().lower()
        if not query_normalized:
            return self.list_entries()

        return [
            record
            for record in self.list_entries()
            if query_normalized in record.name.lower()
        ]

    def _resolve_exact(self, *, name: str, version: str) -> Optional[RegistryRecord]:
        version_path = self.registry_version_path(name=name, version=version)
        if not version_path.exists() or not version_path.is_dir():
            return None

        archive_candidates = sorted(version_path.glob("*.kno"))
        if not archive_candidates:
            return None

        return RegistryRecord(name=name, version=version, archive_path=archive_candidates[0])

    def _discover_versions(self, name: str) -> list[str]:
        agent_dir = self.root / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return []

        versions = [path.name for path in agent_dir.iterdir() if path.is_dir()]
        return sorted(versions, key=_version_sort_key, reverse=True)


def _version_sort_key(value: str) -> tuple[int, ...] | tuple[int, str]:
    parts = value.split(".")
    if all(part.isdigit() for part in parts):
        return tuple(int(part) for part in parts)
    return (0, value)
