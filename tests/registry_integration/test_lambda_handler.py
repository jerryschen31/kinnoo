import hashlib
from io import BytesIO
import json
import types
import zipfile

import lambda_handler


def _make_archive_bytes(*, name: str, version: str, include_signature: bool = True) -> bytes:
    payload = BytesIO()
    readme_bytes = b"hello from lambda"
    with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            f"name: {name}\nversion: {version}\nentrypoint: run.py\n",
        )
        archive.writestr("run.py", "print('ok')\n")
        archive.writestr("README.md", readme_bytes)
        if include_signature:
            archive.writestr(
                "META-INF/signature.json",
                json.dumps({"signature": "dummy-signature"}),
            )
        archive.writestr(
            "META-INF/integrity.json",
            json.dumps(
                {
                    "files": {
                        "README.md": {
                            "sha256": hashlib.sha256(readme_bytes).hexdigest(),
                            "size": len(readme_bytes),
                        },
                        "kinnoo.yaml": {
                            "sha256": hashlib.sha256(
                                f"name: {name}\nversion: {version}\nentrypoint: run.py\n".encode("utf-8")
                            ).hexdigest(),
                            "size": len(f"name: {name}\nversion: {version}\nentrypoint: run.py\n".encode("utf-8")),
                        },
                        "run.py": {
                            "sha256": hashlib.sha256(b"print('ok')\n").hexdigest(),
                            "size": len(b"print('ok')\n"),
                        },
                    }
                }
            ),
        )
    return payload.getvalue()


class _FakeS3Client:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self._objects = objects

    def get_object(self, *, Bucket: str, Key: str):
        del Bucket
        if Key not in self._objects:
            raise RuntimeError(f"missing key: {Key}")
        return {"Body": BytesIO(self._objects[Key])}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str):
        del Bucket, ContentType
        self._objects[Key] = Body

    def list_objects_v2(self, *, Bucket: str, Prefix: str):
        del Bucket
        keys = [{"Key": key} for key in self._objects if key.startswith(Prefix)]
        return {"Contents": keys}


def test_lambda_handler_processes_kno_and_updates_metadata(monkeypatch) -> None:
    tenant = "tenant-a"
    agent = "agent-a"
    version = "1.2.3"
    archive_key = f"archives/tenants/{tenant}/agents/{agent}/versions/{version}/{agent}.kno"
    metadata_key = f"metadata/tenants/{tenant}/agents/{agent}/versions/{version}.v1.json"
    archive_bytes = _make_archive_bytes(name=agent, version=version)
    checksum_bytes = f"{hashlib.sha256(archive_bytes).hexdigest()}\n".encode("utf-8")

    store: dict[str, bytes] = {
        archive_key: archive_bytes,
        f"{archive_key}.sha256": checksum_bytes,
        metadata_key: json.dumps(
            {
                "schema_version": "v1",
                "tenant_slug": tenant,
                "agent_slug": agent,
                "version": version,
                "security_status": "",
                "security_report": None,
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ).encode("utf-8"),
    }

    fake_boto3 = types.SimpleNamespace(client=lambda service: _FakeS3Client(store))
    assert fake_boto3.client("s3")
    monkeypatch.setitem(__import__("sys").modules, "boto3", fake_boto3)

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "kinnoo-registry-dev-386775099533"},
                    "object": {"key": archive_key},
                }
            }
        ]
    }

    result = lambda_handler.handler(event, context=None)

    assert result["processed_count"] == 1
    assert result["processed"][0]["overall_status"] == "pass"

    updated_doc = json.loads(store[metadata_key].decode("utf-8"))
    assert updated_doc["security_status"] == {
        "signature": "pass",
        "archive": "pass",
        "per_file": "pass",
    }
    assert isinstance(updated_doc["security_report"], list)
    assert len(updated_doc["security_report"]) == 4

    result_key = result["processed"][0]["result_key"]
    report_doc = json.loads(store[result_key].decode("utf-8"))
    assert report_doc["tenant_slug"] == tenant
    assert report_doc["agent_slug"] == agent
    assert report_doc["version"] == version


def test_lambda_handler_skips_non_kno_objects(monkeypatch) -> None:
    fake_boto3 = types.SimpleNamespace(client=lambda service: _FakeS3Client({}))
    assert fake_boto3.client("s3")
    monkeypatch.setitem(__import__("sys").modules, "boto3", fake_boto3)

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "kinnoo-registry-dev-386775099533"},
                    "object": {"key": "archives/tenants/t1/agents/a1/versions/1.0.0/a1.kno.sha256"},
                }
            }
        ]
    }

    result = lambda_handler.handler(event, context=None)

    assert result["processed_count"] == 0
    assert result["skipped"]
    assert result["skipped"][0]["reason"] == "not_archive"


def test_lambda_handler_reports_unsigned_when_signature_missing(monkeypatch) -> None:
    tenant = "tenant-a"
    agent = "agent-unsigned"
    version = "1.2.3"
    archive_key = f"archives/tenants/{tenant}/agents/{agent}/versions/{version}/{agent}.kno"
    metadata_key = f"metadata/tenants/{tenant}/agents/{agent}/versions/{version}.v1.json"
    archive_bytes = _make_archive_bytes(name=agent, version=version, include_signature=False)
    checksum_bytes = f"{hashlib.sha256(archive_bytes).hexdigest()}\n".encode("utf-8")

    store: dict[str, bytes] = {
        archive_key: archive_bytes,
        f"{archive_key}.sha256": checksum_bytes,
        metadata_key: json.dumps(
            {
                "schema_version": "v1",
                "tenant_slug": tenant,
                "agent_slug": agent,
                "version": version,
                "security_status": "",
                "security_report": None,
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ).encode("utf-8"),
    }

    fake_boto3 = types.SimpleNamespace(client=lambda service: _FakeS3Client(store))
    assert fake_boto3.client("s3")
    monkeypatch.setitem(__import__("sys").modules, "boto3", fake_boto3)

    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "kinnoo-registry-dev-386775099533"},
                    "object": {"key": archive_key},
                }
            }
        ]
    }

    result = lambda_handler.handler(event, context=None)
    assert result["processed_count"] == 1
    assert result["processed"][0]["overall_status"] == "pass"

    updated_doc = json.loads(store[metadata_key].decode("utf-8"))
    assert updated_doc["security_status"]["signature"] == "unsigned"
