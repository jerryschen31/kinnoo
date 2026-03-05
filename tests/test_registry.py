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


def test_registry_version_resolution_latest_and_exact(tmp_path: Path) -> None:
    backend = LocalFilesystemRegistryBackend(root=tmp_path / "registry")
    service = RegistryService(backend=backend)

    archive_path = tmp_path / "versioned-agent.kno"
    archive_path.write_bytes(b"placeholder")

    service.publish(name="versioned-agent", version="1.0.0", archive_path=archive_path)
    service.publish(name="versioned-agent", version="1.1.0", archive_path=archive_path)
    service.publish(name="versioned-agent", version="2.0.0", archive_path=archive_path)

    latest_record = service.resolve(name="versioned-agent")
    assert latest_record is not None
    assert latest_record.version == "2.0.0"

    exact_record = service.resolve(name="versioned-agent", version="1.1.0")
    assert exact_record is not None
    assert exact_record.version == "1.1.0"

    missing_name_record, missing_name_error = service.resolve_with_error(name="unknown-agent")
    assert missing_name_record is None
    assert missing_name_error is not None
    assert "unknown-agent" in missing_name_error
    assert "not found" in missing_name_error

    missing_version_record, missing_version_error = service.resolve_with_error(
        name="versioned-agent",
        version="9.9.9",
    )
    assert missing_version_record is None
    assert missing_version_error is not None
    assert "versioned-agent==9.9.9" in missing_version_error
    assert "Available versions" in missing_version_error
