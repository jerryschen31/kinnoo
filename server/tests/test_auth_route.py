from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def test_auth_token_route_and_rate_limit(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=5,
    )

    app = create_app(config=config)
    client = TestClient(app)

    app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )

    auth_ok = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "admin-secret",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert auth_ok.status_code == 200
    ok_body = auth_ok.json()
    assert ok_body["token_type"] == "Bearer"
    assert isinstance(ok_body["access_token"], str)
    assert ok_body["expires_in"] > 0

    invalid = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert invalid.status_code == 401
    invalid_body = invalid.json()
    assert invalid_body["error"]["code"] == "unauthorized"
    assert invalid_body["error"]["message"]
    assert invalid_body["error"]["request_id"]

    # 20 requests/minute are allowed; the 21st request should be throttled.
    for _ in range(20):
        response = client.post(
            "/api/auth/token",
            json={
                "username": "admin",
                "password": "wrong-password",
                "tenant_slug": "tenant-alpha",
            },
        )
        assert response.status_code in {401, 429}

    final = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert final.status_code == 429
    throttled_body = final.json()
    assert throttled_body["error"]["code"] == "too_many_requests"
    assert throttled_body["error"]["message"] == "429 too many requests"
    assert throttled_body["error"]["request_id"]


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_auth_config_discovery_endpoint_returns_non_secret_oidc_fields(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "oidc_kinde")
    monkeypatch.setenv("AUTH_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("AUTH_JWKS_ENDPOINT_URL", "https://issuer.example/.well-known/jwks.json")
    monkeypatch.setenv("AUTH_TOKEN_ENDPOINT", "https://issuer.example/oauth2/token")
    monkeypatch.setenv("AUTH_AUTHORIZATION_ENDPOINT", "https://issuer.example/oauth2/auth")
    monkeypatch.setenv("AUTH_LOGOUT_ENDPOINT", "https://issuer.example/logout")
    monkeypatch.setenv("AUTH_USERINFO_ENDPOINT", "https://issuer.example/userinfo")
    monkeypatch.setenv("AUTH_AUDIENCE", "https://api.kinnoo.local")
    monkeypatch.setenv("AUTH_WEB_CLIENT_ID", "web-client-id")
    monkeypatch.setenv("AUTH_WEB_CLIENT_SECRET", "web-client-secret")
    monkeypatch.setenv("AUTH_CLI_CLIENT_ID", "cli-client-id")
    monkeypatch.setenv("AUTH_WEB_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")
    monkeypatch.setenv("AUTH_LOGOUT_REDIRECT_URI", "http://localhost:3000/login")

    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    response = client.get("/api/auth/config")
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert payload["auth_mode"] == "oidc"
    assert payload["issuer_url"] == "https://issuer.example"
    assert payload["authorization_endpoint"] == "https://issuer.example/oauth2/auth"
    assert payload["token_endpoint"] == "https://issuer.example/oauth2/token"
    assert payload["logout_endpoint"] == "https://issuer.example/logout"
    assert payload["userinfo_endpoint"] == "https://issuer.example/userinfo"
    assert payload["audience"] == "https://api.kinnoo.local"
    assert payload["cli_client_id"] == "cli-client-id"
    assert "web_client_secret" not in payload


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature118_legacy_auth_paths_disabled(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "oidc_kinde")
    monkeypatch.setenv("AUTH_ISSUER_URL", "https://issuer.example")
    monkeypatch.setenv("AUTH_JWKS_ENDPOINT_URL", "https://issuer.example/.well-known/jwks.json")
    monkeypatch.setenv("AUTH_TOKEN_ENDPOINT", "https://issuer.example/oauth2/token")
    monkeypatch.setenv("AUTH_AUTHORIZATION_ENDPOINT", "https://issuer.example/oauth2/auth")
    monkeypatch.setenv("AUTH_LOGOUT_ENDPOINT", "https://issuer.example/logout")
    monkeypatch.setenv("AUTH_USERINFO_ENDPOINT", "https://issuer.example/userinfo")
    monkeypatch.setenv("AUTH_AUDIENCE", "https://api.kinnoo.local")
    monkeypatch.setenv("AUTH_WEB_CLIENT_ID", "web-client-id")
    monkeypatch.setenv("AUTH_WEB_CLIENT_SECRET", "web-client-secret")
    monkeypatch.setenv("AUTH_CLI_CLIENT_ID", "cli-client-id")
    monkeypatch.setenv("AUTH_WEB_REDIRECT_URI", "http://127.0.0.1:8000/auth/callback")
    monkeypatch.setenv("AUTH_LOGOUT_REDIRECT_URI", "http://localhost:3000/login")
    monkeypatch.delenv("AUTH_ENABLE_LEGACY_PATHS", raising=False)

    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=5,
    )
    app = create_app(config=config)
    client = TestClient(app)

    token_response = client.post(
        "/api/auth/token",
        json={"username": "admin", "password": "admin-secret"},
    )
    assert token_response.status_code == 403
    assert "legacy auth path disabled" in token_response.json()["error"]["message"]

    register_response = client.post("/api/auth/register-request", json={"email": "dev@example.com"})
    assert register_response.status_code == 403

    reset_response = client.post("/api/auth/password-reset-request", json={"email": "dev@example.com"})
    assert reset_response.status_code == 403

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 401

    monkeypatch.setenv("AUTH_ENABLE_LEGACY_PATHS", "true")
    compat_app = create_app(config=config)
    compat_client = TestClient(compat_app)
    compat_app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )
    compat_token = compat_client.post(
        "/api/auth/token",
        json={"username": "admin", "password": "admin-secret"},
    )
    assert compat_token.status_code == 200
