"""Registry abstraction layer for publish/resolve/list/search flows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass(frozen=True)
class RegistryRecord:
    """Canonical registry entry representation used across backends."""

    name: str
    version: str
    archive_path: Path
    metadata_path: Path | None = None


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
