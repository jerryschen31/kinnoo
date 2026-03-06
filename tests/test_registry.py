from pathlib import Path

from kinnoo.registry import RegistryBackend, RegistryService
from kinnoo.registry_backends import LocalFilesystemRegistryBackend


# [agent] test deprecated: Feature12 registry tests are superseded by feature13 tests.
# def test_registry_backend_contract_and_local_layout(tmp_path: Path) -> None:
#     ...
#
# def test_registry_version_resolution_latest_and_exact(tmp_path: Path) -> None:
#     ...
