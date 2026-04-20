from __future__ import annotations

from pathlib import Path

import pytest

from server.auth.oidc import OIDCProviderConfig
from server.config import resolve_auth_env_contract


@pytest.mark.regression_integration
@pytest.mark.server_api
@pytest.mark.security_checks
def test_feature118_provider_neutral_env_alignment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_ISSUER_URL", "https://canonical-issuer.example")
    monkeypatch.setenv("AUTH_JWKS_ENDPOINT_URL", "https://canonical-issuer.example/.well-known/jwks.json")
    monkeypatch.setenv("AUTH_TOKEN_ENDPOINT", "https://canonical-issuer.example/oauth2/token")
    monkeypatch.setenv("AUTH_AUTHORIZATION_ENDPOINT", "https://canonical-issuer.example/oauth2/auth")
    monkeypatch.setenv("AUTH_LOGOUT_ENDPOINT", "https://canonical-issuer.example/logout")
    monkeypatch.setenv("AUTH_USERINFO_ENDPOINT", "https://canonical-issuer.example/userinfo")
    monkeypatch.setenv("AUTH_AUDIENCE", "https://api.kinnoo.local")
    monkeypatch.setenv("AUTH_WEB_CLIENT_ID", "canonical-web-client")
    monkeypatch.setenv("AUTH_WEB_CLIENT_SECRET", "canonical-web-secret")
    monkeypatch.setenv("AUTH_CLI_CLIENT_ID", "canonical-cli-client")
    monkeypatch.setenv("AUTH_WEB_REDIRECT_URI", "https://dev-api.kinnoo.ai/auth/callback")
    monkeypatch.setenv("AUTH_LOGOUT_REDIRECT_URI", "https://dev.kinnoo.ai/login")

    # Alias values exist but canonical keys must win.
    monkeypatch.setenv("KINDE_ISSUER_URL", "https://alias-issuer.example")
    monkeypatch.setenv("KINDE_WEB_CLIENT_ID", "alias-web-client")
    monkeypatch.setenv("KINDE_WEB_CLIENT_SECRET", "alias-web-secret")
    monkeypatch.setenv("KINDE_CLI_CLIENT_ID", "alias-cli-client")
    monkeypatch.setenv("TOKEN_ENDPOINT", "https://alias-issuer.example/oauth2/token")
    monkeypatch.setenv("AUTHORIZATION_ENDPOINT", "https://alias-issuer.example/oauth2/auth")

    resolved = resolve_auth_env_contract()
    assert resolved["AUTH_ISSUER_URL"] == "https://canonical-issuer.example"
    assert resolved["AUTH_WEB_CLIENT_ID"] == "canonical-web-client"
    assert resolved["AUTH_CLI_CLIENT_ID"] == "canonical-cli-client"
    assert resolved["AUTH_TOKEN_ENDPOINT"] == "https://canonical-issuer.example/oauth2/token"

    config = OIDCProviderConfig.from_env(env=dict(resolved), strict=True)
    assert config is not None
    assert config.issuer_url == "https://canonical-issuer.example"
    assert config.web_client_id == "canonical-web-client"
    assert config.cli_client_id == "canonical-cli-client"

    ecs_main = Path("iac/modules/ecs-fargate/main.tf").read_text(encoding="utf-8")
    secrets_main = Path("iac/modules/secrets/main.tf").read_text(encoding="utf-8")
    assert "AUTH_WEB_CLIENT_ID" in ecs_main
    assert "AUTH_CLI_CLIENT_ID" in ecs_main
    assert "AUTH_ISSUER_URL" in ecs_main
    assert "AUTH_TOKEN_ENDPOINT" in ecs_main
    assert "AUTH_WEB_CLIENT_ID" in secrets_main
    assert "AUTH_CLI_CLIENT_ID" in secrets_main
    assert "AUTH_ISSUER_URL" in secrets_main
    assert "AUTH_TOKEN_ENDPOINT" in secrets_main
    assert "Filter out AUTH_PROVIDER env var when matching secret exists" in ecs_main


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
