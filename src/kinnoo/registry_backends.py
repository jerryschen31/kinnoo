"""Concrete registry backend implementations."""

from __future__ import annotations

import re
import shutil
import json
from pathlib import Path
from typing import Any, Optional

from .registry import RegistryAgentSummary, RegistryRecord
from .schema import SEMVER_PATTERN


DEFAULT_LOCAL_REGISTRY_ROOT = Path.home() / ".kinnoo" / "registry"
DEFAULT_MOCK_REGISTRY_ROOT = Path.home() / "kinnoo-mock-registry-scratch" / "jerry"


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
        publisher_public_key: str | None = None
        if manifest_metadata is not None:
            metadata_path = target_dir / "manifest-metadata.json"
            with metadata_path.open("w", encoding="utf-8") as metadata_file:
                json.dump(manifest_metadata, metadata_file, sort_keys=True, indent=2)
            key_value = manifest_metadata.get("publisher_public_key")
            if isinstance(key_value, str) and key_value.strip():
                publisher_public_key = key_value.strip()

        return RegistryRecord(
            name=name,
            version=version,
            archive_path=target_archive,
            metadata_path=metadata_path,
            publisher_public_key=publisher_public_key,
        )

    def resolve(self, *, name: str, version: Optional[str] = None) -> Optional[RegistryRecord]:
        record, _ = self.resolve_with_error(name=name, version=version)
        return record

    def resolve_with_error(
        self,
        *,
        name: str,
        version: Optional[str] = None,
    ) -> tuple[Optional[RegistryRecord], Optional[str]]:
        agent_dir = self.root / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return None, f"Registry agent '{name}' was not found."

        if version:
            record = self._resolve_exact(name=name, version=version)
            if record is not None:
                return record, None

            available_versions = self._discover_versions(name)
            if version not in available_versions:
                if available_versions:
                    available = ", ".join(available_versions)
                    return (
                        None,
                        f"Registry version '{name}=={version}' was not found. "
                        f"Available versions: {available}.",
                    )
                return None, f"Registry version '{name}=={version}' was not found."

            return (
                None,
                f"Registry version '{name}=={version}' exists but contains no installable .kno archive.",
            )

        versions = self._discover_versions(name)
        if not versions:
            return None, f"Registry agent '{name}' has no published versions."

        for discovered_version in versions:
            record = self._resolve_exact(name=name, version=discovered_version)
            if record is not None:
                return record, None

        return (
            None,
            f"Registry agent '{name}' has published versions but no installable .kno archives.",
        )

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

    def list_latest_agents(self) -> list[RegistryAgentSummary]:
        summaries: list[RegistryAgentSummary] = []
        if not self.root.exists():
            return summaries

        for agent_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            versions = self._discover_versions(agent_dir.name)
            latest_record: RegistryRecord | None = None
            for version in versions:
                latest_record = self._resolve_exact(name=agent_dir.name, version=version)
                if latest_record is not None:
                    break

            if latest_record is None:
                continue

            description = self._read_description(
                name=latest_record.name,
                version=latest_record.version,
            )
            try:
                archive_size_bytes = latest_record.archive_path.stat().st_size
            except OSError:
                archive_size_bytes = None
            summaries.append(
                RegistryAgentSummary(
                    name=latest_record.name,
                    latest_version=latest_record.version,
                    description=description,
                    archive_size_bytes=archive_size_bytes,
                )
            )

        return summaries

    def search_agents(self, *, query: str) -> list[RegistryAgentSummary]:
        query_normalized = query.strip().lower()
        summaries = self.list_latest_agents()
        if not query_normalized:
            return summaries

        return [
            summary
            for summary in summaries
            if query_normalized in summary.name.lower()
            or query_normalized in summary.description.lower()
        ]

    def _resolve_exact(self, *, name: str, version: str) -> Optional[RegistryRecord]:
        version_path = self.registry_version_path(name=name, version=version)
        if not version_path.exists() or not version_path.is_dir():
            return None

        archive_candidates = sorted(version_path.glob("*.kno"))
        if not archive_candidates:
            return None

        metadata_path = version_path / "manifest-metadata.json"
        publisher_public_key: str | None = None
        if metadata_path.exists() and metadata_path.is_file():
            try:
                metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata_payload = None
            if isinstance(metadata_payload, dict):
                raw_key = metadata_payload.get("publisher_public_key")
                if isinstance(raw_key, str) and raw_key.strip():
                    publisher_public_key = raw_key.strip()

        return RegistryRecord(
            name=name,
            version=version,
            archive_path=archive_candidates[0],
            metadata_path=metadata_path if metadata_path.exists() else None,
            publisher_public_key=publisher_public_key,
        )

    def _discover_versions(self, name: str) -> list[str]:
        agent_dir = self.root / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return []

        versions = [path.name for path in agent_dir.iterdir() if path.is_dir()]
        return sorted(versions, key=_version_sort_key, reverse=True)

    def _read_description(self, *, name: str, version: str) -> str:
        metadata_path = self.registry_version_path(name=name, version=version) / "manifest-metadata.json"
        if not metadata_path.exists() or not metadata_path.is_file():
            return ""

        try:
            raw = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""

        value = raw.get("description") if isinstance(raw, dict) else None
        if isinstance(value, str):
            return value.strip()
        return ""


class MockFilesystemRegistryBackend(LocalFilesystemRegistryBackend):
    """Mock registry backend rooted at ~/kinnoo-mock-registry-scratch/jerry by default."""

    def __init__(self, root: Optional[Path] = None) -> None:
        super().__init__(root=(root or DEFAULT_MOCK_REGISTRY_ROOT))

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
        target_dir.mkdir(parents=True, exist_ok=True)
        target_archive = target_dir / f"{name}.kno"
        metadata_path = target_dir / "manifest-metadata.json"

        if target_archive.exists():
            rollover_dir = self._next_untagged_dir(name=name)
            rollover_dir.mkdir(parents=True, exist_ok=True)

            rollover_archive = rollover_dir / f"{name}.kno"
            shutil.copy2(target_archive, rollover_archive)

            if metadata_path.exists() and metadata_path.is_file():
                rollover_metadata = rollover_dir / "manifest-metadata.json"
                shutil.copy2(metadata_path, rollover_metadata)

        shutil.copy2(source_archive, target_archive)

        resolved_metadata_path: Path | None = None
        publisher_public_key: str | None = None
        if manifest_metadata is not None:
            with metadata_path.open("w", encoding="utf-8") as metadata_file:
                json.dump(manifest_metadata, metadata_file, sort_keys=True, indent=2)
            resolved_metadata_path = metadata_path
            key_value = manifest_metadata.get("publisher_public_key")
            if isinstance(key_value, str) and key_value.strip():
                publisher_public_key = key_value.strip()

        return RegistryRecord(
            name=name,
            version=version,
            archive_path=target_archive,
            metadata_path=resolved_metadata_path,
            publisher_public_key=publisher_public_key,
        )

    def _next_untagged_dir(self, *, name: str) -> Path:
        agent_root = self.root / name
        next_slot = 1

        for child in agent_root.iterdir() if agent_root.exists() else []:
            if not child.is_dir() or not child.name.startswith("untagged-"):
                continue
            suffix = child.name.split("untagged-", 1)[1]
            if suffix.isdigit():
                next_slot = max(next_slot, int(suffix) + 1)

        return agent_root / f"untagged-{next_slot}"


def _version_sort_key(value: str) -> tuple[int, ...] | tuple[int, str]:
    parsed = _parse_semver(value)
    if parsed is not None:
        major, minor, patch, prerelease_tokens = parsed
        is_release = 1 if not prerelease_tokens else 0
        return (2, major, minor, patch, is_release, prerelease_tokens)

    return (1, value)


def _parse_semver(value: str) -> tuple[int, int, int, tuple[tuple[int, int | str], ...]] | None:
    if not re.fullmatch(SEMVER_PATTERN, value):
        return None

    without_build = value.split("+", 1)[0]
    if "-" in without_build:
        core, prerelease = without_build.split("-", 1)
    else:
        core, prerelease = without_build, ""

    major_str, minor_str, patch_str = core.split(".")
    major, minor, patch = int(major_str), int(minor_str), int(patch_str)

    prerelease_tokens: tuple[tuple[int, int | str], ...]
    if not prerelease:
        prerelease_tokens = ()
    else:
        normalized_tokens: list[tuple[int, int | str]] = []
        for token in prerelease.split("."):
            if token.isdigit():
                normalized_tokens.append((0, int(token)))
            else:
                normalized_tokens.append((1, token))
        prerelease_tokens = tuple(normalized_tokens)

    return major, minor, patch, prerelease_tokens
