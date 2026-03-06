from pathlib import Path

from kinnoo.archive import ArchiveBackend, LocalArchiveBackend
from kinnoo.registry import RegistryBackend
from kinnoo.registry_backends import MockFilesystemRegistryBackend


def test_pack_uses_canonical_archive_path_and_storage_abstraction(tmp_path: Path) -> None:
    archive_backend = LocalArchiveBackend(root=tmp_path / "archive")
    mock_registry_backend = MockFilesystemRegistryBackend(root=tmp_path / "registry-scratch" / "jerry")

    assert isinstance(archive_backend, ArchiveBackend)
    assert isinstance(mock_registry_backend, RegistryBackend)

    canonical_archive_path = archive_backend.archive_path_for(name="demo-agent", version="1.2.3")
    assert canonical_archive_path == (
        tmp_path / "archive" / "demo-agent" / "1.2.3" / "demo-agent.kno"
    )

    source_archive = tmp_path / "source.kno"
    source_archive.write_bytes(b"archive-payload")
    stored_archive = archive_backend.store(
        name="demo-agent",
        version="1.2.3",
        source_archive=source_archive,
    )
    assert stored_archive.archive_path == canonical_archive_path
    assert stored_archive.archive_path.exists()

    latest = archive_backend.resolve_latest(name="demo-agent")
    assert latest is not None
    assert latest.version == "1.2.3"
    assert latest.archive_path == canonical_archive_path

    published = mock_registry_backend.publish(
        name="demo-agent",
        version="1.2.3",
        archive_path=canonical_archive_path,
    )
    assert published.archive_path == (
        tmp_path / "registry-scratch" / "jerry" / "demo-agent" / "1.2.3" / "demo-agent.kno"
    )
