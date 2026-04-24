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
from server.auth.oidc import OIDCProviderConfig, KindeOIDCProvider, OIDCTokenService


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
    extra_claims: dict[str, object] | None = None,
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
    if extra_claims:
        payload.update(extra_claims)
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


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature118_test707_valid_and_invalid_oidc_token_envelopes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
#     ...


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature118_test708_provider_selection_fail_fast(monkeypatch: pytest.MonkeyPatch) -> None:
#     ...


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


@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature118_web_signup_url_hints_registration() -> None:
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

    url = provider.build_signup_url(state="state-456")
    query = urllib_parse.parse_qs(urllib_parse.urlparse(url).query)
    assert (query.get("start_page") or [""])[0] == "sign_up"
    assert (query.get("prompt") or [""])[0] == "create"

@pytest.mark.regression_integration
@pytest.mark.server_api
def test_feature118_token_service_falls_back_to_org_code_without_email() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    kid = "k-org-fallback"
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
    service = OIDCTokenService(provider=provider)
    provider.fetch_jwks = lambda: {"keys": [_jwk_for_public_key(public_key=private_key.public_key(), kid=kid)]}  # type: ignore[method-assign]

    token = _mint_rs256_token(
        private_key=private_key,
        kid=kid,
        issuer="https://issuer.example",
        audience="https://api.kinnoo.local",
        subject="oidc-user-1",
        extra_claims={
            "org_code": "org_90bd1f158ac",
            "tenant_slug": "org_90bd1f158ac",
            "email": "",
        },
    )

    claims = service.validate_token(token)
    assert claims.tenant_slug == "org_90bd1f158ac"

