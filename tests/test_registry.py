from pathlib import Path

from kinnoo.registry import RegistryBackend, RegistryService
from kinnoo.registry_backends import LocalFilesystemRegistryBackend


def test_registry_backend_contract_and_local_layout(tmp_path: Path) -> None:
    backend = LocalFilesystemRegistryBackend(root=tmp_path / "registry")
    service = RegistryService(backend=backend)

    assert isinstance(backend, RegistryBackend)
    assert backend.registry_version_path(name="demo-agent", version="1.2.3") == (
        tmp_path / "registry" / "demo-agent" / "1.2.3"
    )

    assert service.list_entries() == []
    assert service.search(query="demo") == []
    assert service.resolve(name="demo-agent") is None

    archive_path = tmp_path / "demo-agent.kno"
    archive_path.write_bytes(b"placeholder")

    published = service.publish(
        name="demo-agent",
        version="1.2.3",
        archive_path=archive_path,
    )

    expected_path = tmp_path / "registry" / "demo-agent" / "1.2.3" / "demo-agent.kno"
    assert published.archive_path == expected_path
    assert published.archive_path.exists()

    resolved_latest = service.resolve(name="demo-agent")
    assert resolved_latest is not None
    assert resolved_latest.name == "demo-agent"
    assert resolved_latest.version == "1.2.3"
    assert resolved_latest.archive_path == expected_path
