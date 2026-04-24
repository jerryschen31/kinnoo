from __future__ import annotations

from pathlib import Path

import pytest

from server.auth.oidc import OIDCProviderConfig
from server.config import resolve_auth_env_contract, resolve_auth_provider


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature118_provider_neutral_env_alignment(monkeypatch: pytest.MonkeyPatch) -> None:
#     ...


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature118_provider_neutral_env_missing_required_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_ISSUER_URL", raising=False)
    monkeypatch.delenv("KINDE_ISSUER_URL", raising=False)
    monkeypatch.setenv("AUTH_JWKS_ENDPOINT_URL", "https://issuer.example/.well-known/jwks.json")
    monkeypatch.setenv("AUTH_TOKEN_ENDPOINT", "https://issuer.example/oauth2/token")
    monkeypatch.setenv("AUTH_AUTHORIZATION_ENDPOINT", "https://issuer.example/oauth2/auth")
    monkeypatch.setenv("AUTH_LOGOUT_ENDPOINT", "https://issuer.example/logout")
    monkeypatch.setenv("AUTH_USERINFO_ENDPOINT", "https://issuer.example/userinfo")
    monkeypatch.setenv("AUTH_AUDIENCE", "https://api.kinnoo.local")
    monkeypatch.setenv("AUTH_WEB_CLIENT_ID", "web-client")
    monkeypatch.setenv("AUTH_WEB_CLIENT_SECRET", "web-secret")
    monkeypatch.setenv("AUTH_CLI_CLIENT_ID", "cli-client")
    monkeypatch.setenv("AUTH_WEB_REDIRECT_URI", "https://dev-api.kinnoo.ai/auth/callback")
    monkeypatch.setenv("AUTH_LOGOUT_REDIRECT_URI", "https://dev.kinnoo.ai/login")

    with pytest.raises(ValueError) as error:
        _ = OIDCProviderConfig.from_env(env=dict(resolve_auth_env_contract()), strict=True)
    assert "AUTH_ISSUER_URL" in str(error.value)


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature118_provider_selection_infers_oidc_from_env_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTH_PROVIDER", raising=False)
    monkeypatch.setenv("KINNOO_ENV", "production")
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

    assert resolve_auth_provider() == "oidc_kinde"
