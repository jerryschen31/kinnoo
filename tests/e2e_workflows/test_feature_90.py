from __future__ import annotations

import hashlib
import json
from io import BytesIO
import zipfile

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def _build_app(tmp_path):
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
    token = app.state.token_service.issue_token(
        subject="publisher-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:publish", "registry:read"],
    )
    return app, token


def _archive_bytes(*, manifest: str | None = None, extras: dict[str, str] | None = None) -> bytes:
    payload = BytesIO()
    with zipfile.ZipFile(payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        if manifest is not None:
            archive.writestr("kinnoo.yaml", manifest)
        archive.writestr("README.md", "test archive")
        if extras:
            for key, value in extras.items():
                archive.writestr(key, value)
    return payload.getvalue()


def test_feature90_group1(tmp_path) -> None:
    app, token = _build_app(tmp_path)
    client = TestClient(app)

    oversized = b"x" * (2 * 1024 * 1024)
    too_large = client.post(
        "/api/publish",
        files={"file": ("too-large.kno", oversized, "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert too_large.status_code == 413

    not_zip = client.post(
        "/api/publish",
        files={"file": ("not-zip.kno", b"plain text", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert not_zip.status_code == 400
    assert "zip" in json.dumps(not_zip.json()).lower()

    missing_manifest = client.post(
        "/api/publish",
        files={"file": ("missing-manifest.kno", _archive_bytes(manifest=None), "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert missing_manifest.status_code == 400
    assert "kinnoo.yaml" in json.dumps(missing_manifest.json()).lower()

    invalid_manifest = client.post(
        "/api/publish",
        files={
            "file": (
                "invalid-manifest.kno",
                _archive_bytes(manifest="name: agent\nversion: 1.0.0\n"),
                "application/octet-stream",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid_manifest.status_code == 400
    assert "framework" in json.dumps(invalid_manifest.json()).lower()


def test_feature90_group2(tmp_path) -> None:
    app, token = _build_app(tmp_path)
    client = TestClient(app)

    valid_manifest = "name: agent-copilot\nversion: 1.0.0\nframework: chatgpt\nvisibility: private\n"
    ok = client.post(
        "/api/publish",
        files={"file": ("valid.kno", _archive_bytes(manifest=valid_manifest), "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 201

    files = {
        "kinnoo.yaml": valid_manifest.encode("utf-8"),
        "README.md": b"test archive",
    }
    integrity_manifest = {
        "version": 1,
        "files": {
            path: {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            for path, data in files.items()
        },
    }
    integrity_manifest["files"]["README.md"]["sha256"] = "0" * 64

    tampered_payload = BytesIO()
    with zipfile.ZipFile(tampered_payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in files.items():
            archive.writestr(path, data)
        archive.writestr("META-INF/integrity.json", json.dumps(integrity_manifest))

    tampered = client.post(
        "/api/publish",
        files={"file": ("tampered.kno", tampered_payload.getvalue(), "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert tampered.status_code == 400
    error_payload = tampered.json()
    assert "error" in error_payload
    assert "hash mismatch" in json.dumps(error_payload).lower()
