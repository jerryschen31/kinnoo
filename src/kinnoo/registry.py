"""Registry abstraction layer for publish/resolve/list/search flows."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Any, Literal, Optional, Protocol, runtime_checkable

from .schema import NAME_PATTERN, SEMVER_PATTERN


@dataclass(frozen=True)
class RegistryRecord:
    """Canonical registry entry representation used across backends."""

    name: str
    version: str
    archive_path: Path
    metadata_path: Path | None = None


@dataclass(frozen=True)
class RegistryAgentSummary:
    """Latest-version summary used by `kinnoo list` output."""

    name: str
    latest_version: str
    description: str
    archive_size_bytes: int | None = None


@dataclass(frozen=True)
class InstallTargetSpec:
    """Parsed install target classification for install command routing."""

    kind: Literal["archive-path", "registry-latest", "registry-exact", "invalid"]
    raw_target: str
    archive_path: Path | None = None
    name: str | None = None
    version: str | None = None
    error: str | None = None


@runtime_checkable
class RegistryBackend(Protocol):
    """Backend contract for registry operations.

    Backends can be local filesystem or remote in future versions.
    """

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
    ) -> RegistryRecord:
        """Publish an archive under a name/version and return stored record."""

    def resolve(self, *, name: str, version: Optional[str] = None) -> Optional[RegistryRecord]:
        """Resolve a specific version or latest available version for a name."""

    def list_entries(self) -> list[RegistryRecord]:
        """List all published records in deterministic order."""

    def search(self, *, query: str) -> list[RegistryRecord]:
        """Search for records matching a query in deterministic order."""

    def list_latest_agents(self) -> list[RegistryAgentSummary]:
        """List latest-version summary rows per agent in deterministic order."""

    def search_agents(self, *, query: str) -> list[RegistryAgentSummary]:
        """Search latest-version agent summaries by query in deterministic order."""


class RegistryService:
    """Backend-agnostic service boundary used by command handlers."""

    def __init__(self, backend: RegistryBackend) -> None:
        self._backend = backend

    def publish(
        self,
        *,
        name: str,
        version: str,
        archive_path: Path,
        manifest_metadata: Optional[dict[str, Any]] = None,
    ) -> RegistryRecord:
        return self._backend.publish(
            name=name,
            version=version,
            archive_path=archive_path,
            manifest_metadata=manifest_metadata,
        )

    def resolve(self, *, name: str, version: Optional[str] = None) -> Optional[RegistryRecord]:
        return self._backend.resolve(name=name, version=version)

    def list_entries(self) -> list[RegistryRecord]:
        return self._backend.list_entries()

    def search(self, *, query: str) -> list[RegistryRecord]:
        return self._backend.search(query=query)

    def list_latest_agents(self) -> list[RegistryAgentSummary]:
        backend_lister = getattr(self._backend, "list_latest_agents", None)
        if callable(backend_lister):
            return backend_lister()

        summaries: dict[str, RegistryAgentSummary] = {}
        for record in self.list_entries():
            existing = summaries.get(record.name)
            if existing is None:
                summaries[record.name] = RegistryAgentSummary(
                    name=record.name,
                    latest_version=record.version,
                    description="",
                    archive_size_bytes=None,
                )
        return [summaries[name] for name in sorted(summaries)]

    def search_agents(self, *, query: str) -> list[RegistryAgentSummary]:
        backend_searcher = getattr(self._backend, "search_agents", None)
        if callable(backend_searcher):
            return backend_searcher(query=query)

        query_normalized = query.strip().lower()
        if not query_normalized:
            return self.list_latest_agents()

        return [
            summary
            for summary in self.list_latest_agents()
            if query_normalized in summary.name.lower()
            or query_normalized in summary.description.lower()
        ]

    def resolve_with_error(
        self,
        *,
        name: str,
        version: Optional[str] = None,
    ) -> tuple[Optional[RegistryRecord], Optional[str]]:
        backend_resolver = getattr(self._backend, "resolve_with_error", None)
        if callable(backend_resolver):
            return backend_resolver(name=name, version=version)

        record = self.resolve(name=name, version=version)
        if record is not None:
            return record, None

        if version:
            return None, f"Registry version '{name}=={version}' was not found."
        return None, f"Registry agent '{name}' was not found."


def parse_install_target_spec(target: str) -> InstallTargetSpec:
    """Parse install target into file-path or registry selector forms.

    Supported selector forms:
    - ``<name>`` (latest)
    - ``<name>==<version>`` (exact)
    """

    candidate = target.strip()
    if not candidate:
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error="Install target cannot be empty.",
        )

    looks_like_path = (
        "/" in candidate
        or candidate.startswith(".")
        or candidate.startswith("~")
        or candidate.endswith(".kno")
        or Path(candidate).exists()
    )

    if looks_like_path:
        return InstallTargetSpec(
            kind="archive-path",
            raw_target=target,
            archive_path=Path(candidate).expanduser(),
        )

    separator_count = candidate.count("==")
    if separator_count > 1:
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error=(
                "Invalid registry selector format. Use '<name>' or "
                "'<name>==<version>'."
            ),
        )

    if separator_count == 1:
        name_part, version_part = candidate.split("==", 1)
        name = name_part.strip()
        version = version_part.strip()

        if not name or not version:
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=(
                    "Invalid registry selector format. Use '<name>==<version>' "
                    "with both name and version present."
                ),
            )

        if not re.fullmatch(NAME_PATTERN, name):
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=f"Invalid registry agent name '{name}'.",
            )

        if not re.fullmatch(SEMVER_PATTERN, version):
            return InstallTargetSpec(
                kind="invalid",
                raw_target=target,
                error=f"Invalid registry version '{version}'. Expected semver.",
            )

        return InstallTargetSpec(
            kind="registry-exact",
            raw_target=target,
            name=name,
            version=version,
        )

    if not re.fullmatch(NAME_PATTERN, candidate):
        return InstallTargetSpec(
            kind="invalid",
            raw_target=target,
            error=(
                f"Invalid install target '{candidate}'. Use a .kno file path, "
                "'<name>', or '<name>==<version>'."
            ),
        )

    return InstallTargetSpec(
        kind="registry-latest",
        raw_target=target,
        name=candidate,
    )
