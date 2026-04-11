from __future__ import annotations

import hashlib
from io import BytesIO
import os
import zipfile

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def _make_archive_bytes(*, name: str, version: str, extra_bytes: bytes = b"") -> bytes:
    payload = BytesIO()
    with zipfile.ZipFile(payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            f"name: {name}\nversion: {version}\nvisibility: private\n",
        )
        archive.writestr("README.md", "test archive")
        if extra_bytes:
            archive.writestr("payload.bin", extra_bytes)
    return payload.getvalue()


def test_publish_endpoint(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=1,
    )

    app = create_app(config=config)
    client = TestClient(app)

    publish_token = app.state.token_service.issue_token(
        subject="publisher-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:publish", "registry:read"],
    )
    read_only_token = app.state.token_service.issue_token(
        subject="reader-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    archive_bytes = _make_archive_bytes(name="agent-copilot", version="1.0.0")
    response = client.post(
        "/api/publish",
        files={"file": ("agent-copilot.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_slug"] == "tenant-alpha"
    assert body["agent_slug"] == "agent-copilot"
    assert body["version"] == "1.0.0"

    expected_checksum = hashlib.sha256(archive_bytes).hexdigest()
    assert body["checksum"] == expected_checksum

    archive_key = (
        "archives/tenants/tenant-alpha/agents/agent-copilot/versions/1.0.0/agent-copilot.kno"
    )
    checksum_key = archive_key + ".sha256"

    stored_archive = app.state.storage_backend.get_object(key=archive_key)
    stored_checksum = app.state.storage_backend.get_object(key=checksum_key).decode("utf-8")
    assert stored_archive == archive_bytes
    assert stored_checksum == expected_checksum

    version_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
        version="1.0.0",
    )
    assert version_doc is not None
    assert version_doc.integrity["sha256"] == expected_checksum

    agent_index = app.state.metadata_manager.get_agent_index(
        tenant_slug="tenant-alpha",
        agent_slug="agent-copilot",
    )
    assert agent_index is not None
    assert tuple(item.version for item in agent_index.versions) == ("1.0.0",)

    global_index = app.state.metadata_manager.get_global_index()
    assert global_index is not None
    assert global_index.tenants["tenant-alpha"][0].latest_version == "1.0.0"

    duplicate = client.post(
        "/api/publish",
        files={"file": ("agent-copilot.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert duplicate.status_code == 409
    duplicate_body = duplicate.json()
    assert duplicate_body["error"]["code"] == "conflict"
    assert duplicate_body["error"]["message"]
    assert duplicate_body["error"]["request_id"]

    missing_auth = client.post(
        "/api/publish",
        files={"file": ("agent-copilot.kno", archive_bytes, "application/octet-stream")},
    )
    assert missing_auth.status_code == 401
    missing_auth_body = missing_auth.json()
    assert missing_auth_body["error"]["code"] == "unauthorized"
    assert missing_auth_body["error"]["message"]
    assert missing_auth_body["error"]["request_id"]

    wrong_scope = client.post(
        "/api/publish",
        files={"file": ("agent-copilot.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {read_only_token}"},
    )
    assert wrong_scope.status_code == 403
    wrong_scope_body = wrong_scope.json()
    assert wrong_scope_body["error"]["code"] == "forbidden"
    assert wrong_scope_body["error"]["message"]
    assert wrong_scope_body["error"]["request_id"]

    large_archive = _make_archive_bytes(
        name="agent-copilot",
        version="1.0.1",
        extra_bytes=os.urandom(2 * 1024 * 1024),
    )
    too_large = client.post(
        "/api/publish",
        files={"file": ("agent-copilot.kno", large_archive, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert too_large.status_code == 400
    too_large_body = too_large.json()
    assert too_large_body["error"]["code"] == "bad_request"
    assert too_large_body["error"]["message"]
    assert too_large_body["error"]["request_id"]


def test_publish_accepts_manifest_without_framework_field(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=1,
    )

    app = create_app(config=config)
    client = TestClient(app)

    publish_token = app.state.token_service.issue_token(
        subject="publisher-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:publish", "registry:read"],
    )

    archive_bytes = _make_archive_bytes(name="agent-no-framework", version="1.0.0")
    response = client.post(
        "/api/publish",
        files={"file": ("agent-no-framework.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["agent_slug"] == "agent-no-framework"
    assert body["version"] == "1.0.0"
