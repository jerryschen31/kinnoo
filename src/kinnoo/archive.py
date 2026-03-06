"""Archive storage abstractions for local package source resolution."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from .schema import SEMVER_PATTERN


DEFAULT_LOCAL_ARCHIVE_ROOT = Path.home() / ".kinnoo" / "archive"


@dataclass(frozen=True)
class ArchiveRecord:
    """Canonical archive source entry for name/version artifacts."""

    name: str
    version: str
    archive_path: Path


@runtime_checkable
class ArchiveBackend(Protocol):
    """Backend contract for archive-source operations."""

    def archive_version_path(self, *, name: str, version: str) -> Path:
        """Return canonical version directory for an archive record."""

    def archive_path_for(self, *, name: str, version: str) -> Path:
        """Return canonical archive path for a name/version pair."""

    def store(
        self,
        *,
        name: str,
        version: str,
        source_archive: Path,
        overwrite: bool = False,
    ) -> ArchiveRecord:
        """Store source archive at canonical location and return record."""

    def resolve_latest(self, *, name: str) -> Optional[ArchiveRecord]:
        """Resolve latest stored version for an agent, if available."""

    def resolve_exact(self, *, name: str, version: str) -> Optional[ArchiveRecord]:
        """Resolve exact stored version for an agent, if available."""


class LocalArchiveBackend:
    """Local archive backend rooted at ~/.kinnoo/archive by default."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or DEFAULT_LOCAL_ARCHIVE_ROOT).expanduser()

    def archive_version_path(self, *, name: str, version: str) -> Path:
        return self.root / name / version

    def archive_path_for(self, *, name: str, version: str) -> Path:
        return self.archive_version_path(name=name, version=version) / f"{name}.kno"

    def store(
        self,
        *,
        name: str,
        version: str,
        source_archive: Path,
        overwrite: bool = False,
    ) -> ArchiveRecord:
        source = Path(source_archive)
        if not source.exists():
            raise FileNotFoundError(f"Archive not found: {source}")

        destination = self.archive_path_for(name=name, version=version)
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.exists() and not overwrite:
            raise FileExistsError(f"Archive already exists: {destination}")

        shutil.copy2(source, destination)
        return ArchiveRecord(name=name, version=version, archive_path=destination)

    def resolve_latest(self, *, name: str) -> Optional[ArchiveRecord]:
        versions = self._discover_versions(name)
        for version in versions:
            resolved = self.resolve_exact(name=name, version=version)
            if resolved is not None:
                return resolved
        return None

    def resolve_exact(self, *, name: str, version: str) -> Optional[ArchiveRecord]:
        archive_path = self.archive_path_for(name=name, version=version)
        if not archive_path.exists() or not archive_path.is_file():
            return None
        return ArchiveRecord(name=name, version=version, archive_path=archive_path)

    def _discover_versions(self, name: str) -> list[str]:
        agent_dir = self.root / name
        if not agent_dir.exists() or not agent_dir.is_dir():
            return []

        versions = [path.name for path in agent_dir.iterdir() if path.is_dir()]
        return sorted(versions, key=_version_sort_key, reverse=True)


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
