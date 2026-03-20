from __future__ import annotations

from io import BytesIO
from urllib.parse import urlparse

from server.config import ServerConfig
from server.storage import build_storage_backend_from_config
from server.storage.local import LocalStorageBackend
from server.storage.mock_s3 import MockS3Backend
from server.storage.s3 import S3StorageBackend


class _FakeS3Client:
    """In-memory S3 client double to keep protocol tests deterministic in CI."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], bytes] = {}

    def create_bucket(self, Bucket: str) -> None:
        _ = Bucket

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        _ = ContentType
        self._store[(Bucket, Key)] = bytes(Body)

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, BytesIO]:
        return {"Body": BytesIO(self._store[(Bucket, Key)])}

    def list_objects_v2(self, *, Bucket: str, Prefix: str = "") -> dict[str, list[dict[str, str]]]:
        keys = [key for (bucket, key), _ in self._store.items() if bucket == Bucket and key.startswith(Prefix)]
        return {"Contents": [{"Key": key} for key in sorted(keys)]}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        self._store.pop((Bucket, Key), None)

    def generate_presigned_url(self, _method: str, *, Params: dict[str, str], ExpiresIn: int) -> str:
        return (
            "https://mock-s3.local/"
            f"{Params['Bucket']}/{Params['Key']}"
            f"?expires_in={ExpiresIn}"
        )


def _exercise_protocol(backend, key_prefix: str) -> None:
    key = f"{key_prefix}/object.txt"
    payload = b"storage-protocol-check"

    backend.put_object(key=key, data=payload, content_type="text/plain")
    assert backend.get_object(key=key) == payload

    listed = backend.list_objects(prefix=key_prefix)
    assert key in listed

    presigned_url = backend.generate_presigned_url(key=key, expires_in_seconds=120)
    parsed = urlparse(presigned_url)
    assert parsed.scheme in {"file", "http", "https"}

    backend.delete_object(key=key)
    assert key not in backend.list_objects(prefix=key_prefix)


def test_storage_protocol(tmp_path, monkeypatch):
    fake_client = _FakeS3Client()
    fake_client.create_bucket(Bucket="kinnoo-registry-dev")

    local_config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "local-storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=50,
    )
    local_backend = build_storage_backend_from_config(local_config)
    assert isinstance(local_backend, LocalStorageBackend)
    _exercise_protocol(local_backend, "tenant/local")

    mock_config = ServerConfig(
        storage_backend="mock",
        local_storage_root=tmp_path / "unused",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=50,
    )
    mock_backend = build_storage_backend_from_config(mock_config, s3_client=fake_client)
    assert isinstance(mock_backend, MockS3Backend)
    _exercise_protocol(mock_backend, "tenant/mock")

    s3_config = ServerConfig(
        storage_backend="s3",
        local_storage_root=tmp_path / "unused",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url="http://localhost:9000",
        s3_access_key_id="dev",
        s3_secret_access_key="dev",
        presign_ttl_seconds=120,
        max_upload_mb=50,
    )
    s3_backend = build_storage_backend_from_config(s3_config, s3_client=fake_client)
    assert isinstance(s3_backend, S3StorageBackend)
    _exercise_protocol(s3_backend, "tenant/s3")

    monkeypatch.setenv("REGISTRY_STORAGE_BACKEND", "local")
    selected_local = ServerConfig.from_env()
    assert selected_local.storage_backend == "local"

    monkeypatch.setenv("REGISTRY_STORAGE_BACKEND", "mock")
    selected_mock = ServerConfig.from_env()
    assert selected_mock.storage_backend == "mock"

    monkeypatch.setenv("REGISTRY_STORAGE_BACKEND", "s3")
    selected_s3 = ServerConfig.from_env()
    assert selected_s3.storage_backend == "s3"
