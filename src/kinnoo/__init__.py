"""kinnoo — agent packaging toolkit."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .archive import ArchiveBackend, ArchiveRecord, LocalArchiveBackend
from .registry import RegistryBackend, RegistryRecord, RegistryService
from .registry_backends import LocalFilesystemRegistryBackend, LocalRegistryBackend, MockFilesystemRegistryBackend
from .remote_client import RemoteRegistryClient
from .validator import validate


def _resolve_version() -> str:
	try:
		return version("kinnoo")
	except PackageNotFoundError:
		pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
		if pyproject_path.exists():
			import tomllib

			with pyproject_path.open("rb") as file_handle:
				project_data = tomllib.load(file_handle)
			return project_data.get("project", {}).get("version", "0.0.0")
		return "0.0.0"


__version__ = _resolve_version()

__all__ = [
	"validate",
	"__version__",
	"RegistryBackend",
	"RegistryRecord",
	"RegistryService",
	"ArchiveBackend",
	"ArchiveRecord",
	"LocalArchiveBackend",
	"LocalRegistryBackend",
	"LocalFilesystemRegistryBackend",
	"MockFilesystemRegistryBackend",
	"RemoteRegistryClient",
]
