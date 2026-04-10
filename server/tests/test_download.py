from __future__ import annotations

from io import BytesIO
from urllib.parse import parse_qs, urlparse
import zipfile

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.publish import publish_archive


def _archive_bytes(*, name: str, version: str, visibility: str = "private") -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            (
                f"name: {name}\n"
                f"version: {version}\n"
                "framework: none\n"
                f"visibility: {visibility}\n"
            ),
        )
        archive.writestr("README.md", "download test")
    return buffer.getvalue()


def test_download_presigned(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=321,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    reader_token = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    publish_result = publish_archive(
        authorization_header=f"Bearer {publisher_token}",
        filename="agent-downloader.kno",
        archive_bytes=_archive_bytes(name="agent-downloader", version="1.2.3"),
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert publish_result.status_code == 201

    # Mock presign generation to keep URL contract deterministic in tests.
    def _mock_presign(*, key: str, expires_in_seconds: int) -> str:
        return f"https://mock-storage.local/{key}?expires_in={expires_in_seconds}"

    app.state.storage_backend.generate_presigned_url = _mock_presign

    response = client.get(
        "/api/agents/tenant-alpha/agent-downloader/1.2.3/download",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "download_url" in body
    assert body["expires_in"] == 321

    parsed_url = urlparse(body["download_url"])
    assert parsed_url.scheme in {"http", "https"}
    assert parse_qs(parsed_url.query)["expires_in"] == ["321"]

    missing = client.get(
        "/api/agents/tenant-alpha/agent-downloader/9.9.9/download",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert missing.status_code == 404
    missing_body = missing.json()
    assert missing_body["error"]["code"] == "not_found"
    assert missing_body["error"]["message"]
    assert missing_body["error"]["request_id"]

    missing_auth = client.get("/api/agents/tenant-alpha/agent-downloader/1.2.3/download")
    assert missing_auth.status_code == 401
    missing_auth_body = missing_auth.json()
    assert missing_auth_body["error"]["code"] == "unauthorized"
    assert missing_auth_body["error"]["message"]
    assert missing_auth_body["error"]["request_id"]


def test_download_local_backend_returns_http_archive_endpoint(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=321,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    publisher_token = app.state.token_service.issue_token(
        subject="publisher-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read", "registry:publish"],
    )
    reader_token = app.state.token_service.issue_token(
        subject="reader-alpha",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    publish_result = publish_archive(
        authorization_header=f"Bearer {publisher_token}",
        filename="agent-downloader.kno",
        archive_bytes=_archive_bytes(name="agent-downloader", version="1.2.3"),
        token_service=app.state.token_service,
        storage_backend=app.state.storage_backend,
        metadata_manager=app.state.metadata_manager,
        max_upload_mb=app.state.config.max_upload_mb,
    )
    assert publish_result.status_code == 201

    response = client.get(
        "/api/agents/tenant-alpha/agent-downloader/1.2.3/download",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    download_url = body["download_url"]
    parsed_url = urlparse(download_url)
    assert parsed_url.scheme in {"http", "https"}
    assert parsed_url.path.endswith("/api/agents/tenant-alpha/agent-downloader/1.2.3/archive")

    archive_response = client.get(
        "/api/agents/tenant-alpha/agent-downloader/1.2.3/archive",
        headers={"Authorization": f"Bearer {reader_token}"},
    )
    assert archive_response.status_code == 200
    assert archive_response.content[:2] == b"PK"
