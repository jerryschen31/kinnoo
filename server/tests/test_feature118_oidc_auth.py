from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from urllib import parse as urllib_parse

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.auth.oidc import OIDCProviderConfig, KindeOIDCProvider


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _mint_rs256_token(
    *,
    private_key: rsa.RSAPrivateKey,
    kid: str,
    issuer: str,
    audience: str,
    subject: str,
    scope: str = "registry:read",
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
        "tenant_slug": "tenant-alpha",
        "jti": "jti-1",
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


def _configure_oidc_env(monkeypatch: pytest.MonkeyPatch) -> None:
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


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature118_test707_valid_and_invalid_oidc_token_envelopes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_oidc_env(monkeypatch)
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

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "k1"
    provider = app.state.token_service.provider
    provider.fetch_jwks = lambda: {"keys": [_jwk_for_public_key(public_key=private_key.public_key(), kid=kid)]}  # type: ignore[attr-defined]
    provider.build_login_url = lambda state: f"https://issuer.example/oauth2/auth?state={state}"  # type: ignore[method-assign]
    provider.exchange_code_for_tokens = lambda code: {"access_token": "callback-access-token"}  # type: ignore[method-assign]
    provider.fetch_userinfo = lambda access_token: {"email": "dev@example.com", "sub": "oidc-user-1"}  # type: ignore[method-assign]
    provider.build_logout_url = lambda: "https://issuer.example/logout"  # type: ignore[method-assign]

    client = TestClient(app, base_url="https://testserver")
    valid_token = _mint_rs256_token(
        private_key=private_key,
        kid=kid,
        issuer="https://issuer.example",
        audience="https://api.kinnoo.local",
        subject="user-1",
    )
    ok = client.get("/api/agents", headers={"Authorization": f"Bearer {valid_token}"})
    assert ok.status_code == 200

    invalid_issuer_token = _mint_rs256_token(
        private_key=private_key,
        kid=kid,
        issuer="https://wrong-issuer.example",
        audience="https://api.kinnoo.local",
        subject="user-1",
    )
    denied = client.get("/api/agents", headers={"Authorization": f"Bearer {invalid_issuer_token}"})
    assert denied.status_code == 401
    denied_payload = denied.json()
    assert denied_payload["error"]["code"] == "unauthorized"
    assert denied_payload["error"]["message"]
    assert denied_payload["error"]["request_id"]

    login_start = client.get("/login", follow_redirects=False)
    assert login_start.status_code == 307
    assert login_start.headers["location"].startswith("https://issuer.example/oauth2/auth?")

    state_cookie = client.cookies.get("kinnoo_oidc_state")
    assert state_cookie
    callback = client.get(f"/auth/callback?code=code-1&state={state_cookie}", follow_redirects=False)
    assert callback.status_code == 303
    assert callback.headers["location"] == "/registry"
    assert client.cookies.get(app.state.session_service.cookie_name)

    logout = client.post(
        "/logout",
        data={"csrf_token": client.cookies.get("kinnoo_csrf") or ""},
        follow_redirects=False,
    )
    assert logout.status_code == 303
    assert logout.headers["location"] == "https://issuer.example/logout"


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.schema_contract
def test_feature118_test708_provider_selection_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_PROVIDER", "oidc_kinde")
    monkeypatch.delenv("KINDE_ISSUER_URL", raising=False)
    monkeypatch.delenv("JWKS_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("TOKEN_ENDPOINT", raising=False)
    monkeypatch.delenv("AUTHORIZATION_ENDPOINT", raising=False)
    monkeypatch.delenv("LOGOUT_ENDPOINT", raising=False)
    monkeypatch.delenv("USERINFO_ENDPOINT", raising=False)
    monkeypatch.delenv("KINDE_AUDIENCE", raising=False)
    monkeypatch.delenv("KINDE_WEB_CLIENT_ID", raising=False)
    monkeypatch.delenv("KINDE_WEB_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("KINDE_CLI_CLIENT_ID", raising=False)
    monkeypatch.delenv("KINDE_WEB_REDIRECT_URI", raising=False)
    monkeypatch.delenv("KINDE_LOGOUT_REDIRECT_URI", raising=False)

    with pytest.raises(ValueError) as error:
        create_app()
    assert "Missing required OIDC configuration" in str(error.value)


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature118_web_login_scope_excludes_offline_access() -> None:
    provider = KindeOIDCProvider(
        config=OIDCProviderConfig(
            issuer_url="https://issuer.example",
            jwks_endpoint_url="https://issuer.example/.well-known/jwks.json",
            token_endpoint="https://issuer.example/oauth2/token",
            authorization_endpoint="https://issuer.example/oauth2/auth",
            logout_endpoint="https://issuer.example/logout",
            userinfo_endpoint="https://issuer.example/userinfo",
            audience="https://api.kinnoo.local",
            web_client_id="web-client-id",
            web_client_secret="web-client-secret",
            cli_client_id="cli-client-id",
            web_redirect_uri="https://dev.kinnoo.ai/auth/callback",
            logout_redirect_uri="https://dev.kinnoo.ai/login",
        )
    )

    url = provider.build_login_url(state="state-123")
    query = urllib_parse.parse_qs(urllib_parse.urlparse(url).query)
    scope = (query.get("scope") or [""])[0]
    assert "offline_access" not in scope
    assert scope == "openid profile email"
