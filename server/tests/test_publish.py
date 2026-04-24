from __future__ import annotations

import base64
import hashlib
import json
from io import BytesIO
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID
import zipfile

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
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


def _make_archive_bytes_without_visibility(*, name: str, version: str, extra_bytes: bytes = b"") -> bytes:
    payload = BytesIO()
    with zipfile.ZipFile(payload, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "kinnoo.yaml",
            f"name: {name}\nversion: {version}\n",
        )
        archive.writestr("README.md", "test archive")
        if extra_bytes:
            archive.writestr("payload.bin", extra_bytes)
    return payload.getvalue()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _mint_rs256_token(
    *,
    private_key: rsa.RSAPrivateKey,
    kid: str,
    issuer: str,
    audience: str,
    subject: str,
    tenant_slug: str,
    scope: str = "registry:publish registry:read",
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()) - 5,
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "scope": scope,
        "tenant_slug": tenant_slug,
        "jti": f"jti-{subject}",
    }
    header = {"alg": "RS256", "kid": kid, "typ": "JWT"}
    signing_input = f"{_b64url_encode(json.dumps(header).encode('utf-8'))}.{_b64url_encode(json.dumps(payload).encode('utf-8'))}"
    signature = private_key.sign(signing_input.encode("ascii"), padding.PKCS1v15(), hashes.SHA256())
    return f"{signing_input}.{_b64url_encode(signature)}"


def _jwk_for_public_key(*, public_key: rsa.RSAPublicKey, kid: str) -> dict[str, object]:
    numbers = public_key.public_numbers()
    n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    return {"kty": "RSA", "kid": kid, "alg": "RS256", "use": "sig", "n": _b64url_encode(n), "e": _b64url_encode(e)}


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
    assert version_doc.archive_size_bytes == len(archive_bytes)

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


def test_publish_rejects_when_tenant_storage_quota_would_be_exceeded(tmp_path):
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

    archive_bytes = _make_archive_bytes(name="quota-agent", version="1.0.0")
    setattr(
        app.state.metadata_manager,
        "get_tenant_storage_usage",
        lambda *, tenant_slug: (len(archive_bytes) - 1, len(archive_bytes) - 1),
    )

    response = client.post(
        "/api/publish",
        files={"file": ("quota-agent.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )

    assert response.status_code == 413
    payload = response.json()
    assert payload["error"]["code"] == "payload_too_large"
    assert "quota exceeded" in payload["error"]["message"].lower()


def test_publish_defaults_visibility_to_public_when_manifest_omits_visibility(tmp_path):
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

    archive_bytes = _make_archive_bytes_without_visibility(name="agent-default-public", version="1.0.0")
    response = client.post(
        "/api/publish",
        files={"file": ("agent-default-public.kno", archive_bytes, "application/octet-stream")},
        headers={"Authorization": f"Bearer {publish_token}"},
    )
    assert response.status_code == 201

    version_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-alpha",
        agent_slug="agent-default-public",
        version="1.0.0",
    )
    assert version_doc is not None
    assert version_doc.visibility == "public"

    agent_index = app.state.metadata_manager.get_agent_index(
        tenant_slug="tenant-alpha",
        agent_slug="agent-default-public",
    )
    assert agent_index is not None
    assert agent_index.visibility == "public"

    global_index = app.state.metadata_manager.get_global_index()
    assert global_index is not None
    alpha_summaries = global_index.tenants.get("tenant-alpha", ())
    published = [item for item in alpha_summaries if item.agent_slug == "agent-default-public"]
    assert len(published) == 1
    assert published[0].visibility == "public"


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature118_identity_mapping_and_publish_ownership(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "oidc_kinde")
    monkeypatch.setenv("KINDE_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("JWKS_ENDPOINT_URL", "https://issuer.example/.well-known/jwks.json")
    monkeypatch.setenv("TOKEN_ENDPOINT", "https://issuer.example/oauth2/token")
    monkeypatch.setenv("AUTHORIZATION_ENDPOINT", "https://issuer.example/oauth2/auth")
    monkeypatch.setenv("LOGOUT_ENDPOINT", "https://issuer.example/logout")
    monkeypatch.setenv("USERINFO_ENDPOINT", "https://issuer.example/userinfo")
    monkeypatch.setenv("KINDE_AUDIENCE", "https://api.kinnoo.local")
    monkeypatch.setenv("KINDE_WEB_CLIENT_ID", "web-client-id")
    monkeypatch.setenv("KINDE_WEB_CLIENT_SECRET", "web-client-secret")
    monkeypatch.setenv("KINDE_CLI_CLIENT_ID", "cli-client-id")
    monkeypatch.setenv("KINDE_WEB_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")
    monkeypatch.setenv("KINDE_LOGOUT_REDIRECT_URI", "http://localhost:3000/login")

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

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "k-publish"
    provider = app.state.token_service.provider
    provider.fetch_jwks = lambda: {"keys": [_jwk_for_public_key(public_key=private_key.public_key(), kid=kid)]}  # type: ignore[attr-defined]

    archive_one = _make_archive_bytes(name="web-owned-agent", version="1.0.0")
    web_token = _mint_rs256_token(
        private_key=private_key,
        kid=kid,
        issuer="https://issuer.example",
        audience="web-client-id",
        subject="kinde-web-subject-1",
        tenant_slug="tenant-web",
    )
    web_publish = client.post(
        "/api/publish",
        files={"file": ("web-owned-agent.kno", archive_one, "application/octet-stream")},
        headers={"Authorization": f"Bearer {web_token}"},
    )
    assert web_publish.status_code == 201

    archive_two = _make_archive_bytes(name="cli-owned-agent", version="2.0.0")
    cli_token = _mint_rs256_token(
        private_key=private_key,
        kid=kid,
        issuer="https://issuer.example",
        audience="cli-client-id",
        subject="kinde-cli-subject-2",
        tenant_slug="tenant-cli",
    )
    cli_publish = client.post(
        "/api/publish",
        files={"file": ("cli-owned-agent.kno", archive_two, "application/octet-stream")},
        headers={"Authorization": f"Bearer {cli_token}"},
    )
    assert cli_publish.status_code == 201

    web_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-web",
        agent_slug="web-owned-agent",
        version="1.0.0",
    )
    cli_doc = app.state.metadata_manager.get_version_metadata(
        tenant_slug="tenant-cli",
        agent_slug="cli-owned-agent",
        version="2.0.0",
    )
    assert web_doc is not None
    assert cli_doc is not None

    web_internal_user_id = str(web_doc.publisher["user_id"])
    cli_internal_user_id = str(cli_doc.publisher["user_id"])
    assert web_internal_user_id != "kinde-web-subject-1"
    assert cli_internal_user_id != "kinde-cli-subject-2"
    assert web_doc.publisher["external_subject"] == "kinde-web-subject-1"
    assert cli_doc.publisher["external_subject"] == "kinde-cli-subject-2"

    assert UUID(web_internal_user_id)
    assert UUID(cli_internal_user_id)
    assert web_internal_user_id != cli_internal_user_id

    web_mapping = app.state.sqlite_auth_store.get_identity_mapping(
        provider="oidc_kinde",
        provider_user_id="kinde-web-subject-1",
    )
    cli_mapping = app.state.sqlite_auth_store.get_identity_mapping(
        provider="oidc_kinde",
        provider_user_id="kinde-cli-subject-2",
    )
    assert web_mapping is not None
    assert cli_mapping is not None
    assert web_mapping.user_id == web_internal_user_id
    assert cli_mapping.user_id == cli_internal_user_id
