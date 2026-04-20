from __future__ import annotations

import io
from urllib.error import HTTPError

import pytest

from server.auth.oidc import (
    KindeOIDCProvider,
    OIDCProviderConfig,
    OIDCRequestError,
    OIDCTokenService,
    _http_json_request,
)
from server.auth.token import TokenValidationError


def _provider_config() -> OIDCProviderConfig:
    return OIDCProviderConfig(
        issuer_url="https://issuer.example.com",
        jwks_endpoint_url="https://issuer.example.com/.well-known/jwks.json",
        token_endpoint="https://issuer.example.com/oauth2/token",
        authorization_endpoint="https://issuer.example.com/oauth2/auth",
        logout_endpoint="https://issuer.example.com/logout",
        userinfo_endpoint="https://issuer.example.com/userinfo",
        audience="kinnoo-api",
        web_client_id="web-client",
        web_client_secret="web-secret",
        cli_client_id="cli-client",
        web_redirect_uri="https://app.example.com/auth/callback",
        logout_redirect_uri="https://app.example.com/",
    )


def test_http_json_request_wraps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_http_error(*args, **kwargs):
        raise HTTPError(
            url="https://issuer.example.com/.well-known/jwks.json",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=io.BytesIO(b"unavailable"),
        )

    monkeypatch.setattr("server.auth.oidc.urllib_request.urlopen", _raise_http_error)

    with pytest.raises(OIDCRequestError, match="failed with HTTP 503"):
        _http_json_request(
            method="GET",
            url="https://issuer.example.com/.well-known/jwks.json",
        )


def test_resolve_jwk_wraps_fetch_errors_as_token_validation_error() -> None:
    provider = KindeOIDCProvider(config=_provider_config())
    service = OIDCTokenService(provider=provider)

    def _raise_oidc_error(*args, **kwargs):
        raise OIDCRequestError("OIDC GET https://issuer.example.com/.well-known/jwks.json failed.")

    provider.fetch_jwks = _raise_oidc_error  # type: ignore[method-assign]

    with pytest.raises(TokenValidationError, match="503 service unavailable: jwks fetch failed") as exc_info:
        service._resolve_jwk(kid="missing-kid")
    assert isinstance(exc_info.value.__cause__, OIDCRequestError)
