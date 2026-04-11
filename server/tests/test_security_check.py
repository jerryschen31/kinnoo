from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import types
import zipfile

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.services.security_check import invoke_security_check_lambda_async, run_post_publish_checks


def _build_archive(
    archive_path: Path,
    *,
    include_signature: bool,
    include_integrity: bool,
    tamper_integrity: bool,
) -> None:
    readme_payload = b"security check sample"
    integrity_hash = hashlib.sha256(readme_payload).hexdigest()
    if tamper_integrity:
        integrity_hash = "0" * 64

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("kinnoo.yaml", "name: task480-agent\nversion: 1.0.0\n")
        archive.writestr("README.md", readme_payload)

        if include_integrity:
            archive.writestr(
                "META-INF/integrity.json",
                json.dumps(
                    {
                        "files": {
                            "README.md": {
                                "sha256": integrity_hash,
                                "size": len(readme_payload),
                            }
                        }
                    }
                ),
            )

        if include_signature:
            archive.writestr(
                "META-INF/signature.json",
                json.dumps({"signature": "dummy-signature"}),
            )


def test_post_publish_security_checks(tmp_path: Path) -> None:
    passing_archive = tmp_path / "passing.kno"
    _build_archive(
        passing_archive,
        include_signature=True,
        include_integrity=True,
        tamper_integrity=False,
    )

    passing_report = run_post_publish_checks(passing_archive)
    assert passing_report["overall_status"] == "pass"
    assert passing_report["security_status"] == {
        "signature": "pass",
        "archive": "pass",
        "per_file": "pass",
    }

    failing_archive = tmp_path / "failing.kno"
    _build_archive(
        failing_archive,
        include_signature=False,
        include_integrity=True,
        tamper_integrity=True,
    )

    failing_report = run_post_publish_checks(failing_archive)
    assert failing_report["overall_status"] == "fail"
    checks = {item["check_name"]: item for item in failing_report["checks"]}
    assert checks["signature"]["status"] == "fail"
    assert checks["archive_integrity"]["status"] == "pass"
    assert checks["per_file_integrity"]["status"] == "fail"


def _make_publishable_archive_bytes(*, name: str, version: str) -> bytes:
    manifest_payload = f"name: {name}\nversion: {version}\nvisibility: private\n".encode("utf-8")
    readme_payload = b"publish-integrity"
    integrity_doc = {
        "files": {
            "kinnoo.yaml": {
                "sha256": hashlib.sha256(manifest_payload).hexdigest(),
                "size": len(manifest_payload),
            },
            "README.md": {
                "sha256": hashlib.sha256(readme_payload).hexdigest(),
                "size": len(readme_payload),
            }
        }
    }

    payload = BytesIO()
    with zipfile.ZipFile(payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("kinnoo.yaml", manifest_payload)
        archive.writestr("README.md", readme_payload)
        archive.writestr("META-INF/integrity.json", json.dumps(integrity_doc))
        archive.writestr("META-INF/signature.json", json.dumps({"signature": "dummy-signature"}))
    return payload.getvalue()


def test_publish_triggers_security_update(tmp_path: Path) -> None:
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=2,
    )
    app = create_app(config=config)
    client = TestClient(app)

    publish_token = app.state.token_service.issue_token(
        subject="publisher-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:publish", "registry:read"],
    )

    archive_bytes = _make_publishable_archive_bytes(name="agent-secure", version="1.0.0")
    publish_response = client.post(
        "/api/publish",
        files={"file": ("agent-secure.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert publish_response.status_code == 201

    version_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-secure",
        version="1.0.0",
    )
    assert version_doc is not None
    assert version_doc.security_status == {
        "signature": "pass",
        "archive": "pass",
        "per_file": "pass",
    }
    assert isinstance(version_doc.security_report, list)
    assert len(version_doc.security_report) == 3

    report_response = client.get(
        "/api/agents/tenant-alpha/agent-secure/1.0.0/security-report",
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert report_response.status_code == 200
    body = report_response.json()
    assert body["security_status"]["signature"] == "pass"
    assert {item["check_name"] for item in body["checks"]} == {
        "signature",
        "archive_integrity",
        "per_file_integrity",
    }


def test_containerized_security_check(monkeypatch, tmp_path: Path) -> None:
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=2,
    )
    app = create_app(config=config)
    client = TestClient(app)

    invoked: list[dict[str, object]] = []

    class _FakeLambdaClient:
        def invoke(self, **kwargs):
            invoked.append(kwargs)
            return {"StatusCode": 202}

    fake_boto3 = types.SimpleNamespace(client=lambda service_name: _FakeLambdaClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("KINNOO_SECURITY_CHECK_EXECUTION_MODE", "lambda")
    monkeypatch.setenv("KINNOO_SECURITY_CHECK_LAMBDA_NAME", "kinnoo-dev-security-check")

    publish_token = app.state.token_service.issue_token(
        subject="publisher-user",
        tenant_slug="tenant-alpha",
        scopes=["registry:publish", "registry:read"],
    )

    archive_bytes = _make_publishable_archive_bytes(name="agent-lambda", version="1.0.0")
    publish_response = client.post(
        "/api/publish",
        files={"file": ("agent-lambda.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert publish_response.status_code == 201

    assert len(invoked) == 1
    assert invoked[0]["InvocationType"] == "Event"
    assert invoked[0]["FunctionName"] == "kinnoo-dev-security-check"

    version_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-lambda",
        version="1.0.0",
    )
    assert version_doc is not None
    assert isinstance(version_doc.security_report, list)
    assert len(version_doc.security_report) == 3


def test_containerized_security_check_lambda_retry_fallback(monkeypatch) -> None:
    attempts = {"count": 0}

    class _FailingLambdaClient:
        def invoke(self, **_kwargs):
            attempts["count"] += 1
            raise RuntimeError("simulated lambda invoke failure")

    fake_boto3 = types.SimpleNamespace(client=lambda _service_name: _FailingLambdaClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("KINNOO_SECURITY_CHECK_EXECUTION_MODE", "lambda")
    monkeypatch.setenv("KINNOO_SECURITY_CHECK_LAMBDA_NAME", "kinnoo-dev-security-check")
    monkeypatch.setenv("KINNOO_SECURITY_CHECK_LAMBDA_RETRIES", "2")

    result = invoke_security_check_lambda_async(
        tenant_slug="tenant-alpha",
        agent_slug="agent-retry",
        version="1.0.0",
    )

    assert attempts["count"] == 3
    assert result["mode"] == "lambda"
    assert result["invoked"] is False
    assert result["attempts"] == 3
    assert result["fallback"] == "inline_publish_checks_preserved"
