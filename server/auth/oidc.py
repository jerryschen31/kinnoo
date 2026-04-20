"""Provider-portable OIDC adapter + token validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import json
from typing import Any
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from server.auth.token import TokenClaims, TokenValidationError
from server.models.user import username_to_tenant_slug


def _b64url_decode(value: str) -> bytes:
    padding_text = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding_text).encode("ascii"))


def _now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _http_json_request(
    *,
    method: str,
    url: str,
    data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    body: bytes | None = None
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    if data is not None:
        body = urllib_parse.urlencode(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    request = urllib_request.Request(url=url, method=method, headers=request_headers, data=body)
    with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("OIDC endpoint returned non-object JSON payload.")
    return decoded


@dataclass(frozen=True)
class OIDCProviderConfig:
    issuer_url: str
    jwks_endpoint_url: str
    token_endpoint: str
    authorization_endpoint: str
    logout_endpoint: str
    userinfo_endpoint: str
    audience: str
    web_client_id: str
    web_client_secret: str
    cli_client_id: str
    web_redirect_uri: str
    logout_redirect_uri: str

    @classmethod
    def from_env(cls, *, env: dict[str, str], strict: bool = True) -> "OIDCProviderConfig | None":
        required = [
            "KINDE_ISSUER_URL",
            "JWKS_ENDPOINT_URL",
            "TOKEN_ENDPOINT",
            "AUTHORIZATION_ENDPOINT",
            "LOGOUT_ENDPOINT",
            "USERINFO_ENDPOINT",
            "KINDE_AUDIENCE",
            "KINDE_WEB_CLIENT_ID",
            "KINDE_WEB_CLIENT_SECRET",
            "KINDE_CLI_CLIENT_ID",
            "KINDE_WEB_REDIRECT_URI",
            "KINDE_LOGOUT_REDIRECT_URI",
        ]
        missing = [name for name in required if not (env.get(name) or "").strip()]
        if missing:
            if strict:
                raise ValueError(
                    "Missing required OIDC configuration: " + ", ".join(sorted(missing))
                )
            return None

        return cls(
            issuer_url=env["KINDE_ISSUER_URL"].strip(),
            jwks_endpoint_url=env["JWKS_ENDPOINT_URL"].strip(),
            token_endpoint=env["TOKEN_ENDPOINT"].strip(),
            authorization_endpoint=env["AUTHORIZATION_ENDPOINT"].strip(),
            logout_endpoint=env["LOGOUT_ENDPOINT"].strip(),
            userinfo_endpoint=env["USERINFO_ENDPOINT"].strip(),
            audience=env["KINDE_AUDIENCE"].strip(),
            web_client_id=env["KINDE_WEB_CLIENT_ID"].strip(),
            web_client_secret=env["KINDE_WEB_CLIENT_SECRET"].strip(),
            cli_client_id=env["KINDE_CLI_CLIENT_ID"].strip(),
            web_redirect_uri=env["KINDE_WEB_REDIRECT_URI"].strip(),
            logout_redirect_uri=env["KINDE_LOGOUT_REDIRECT_URI"].strip(),
        )


class KindeOIDCProvider:
    """Kinde-backed adapter constrained to provider-portable OIDC interfaces."""

    def __init__(self, *, config: OIDCProviderConfig) -> None:
        self._config = config

    @property
    def config(self) -> OIDCProviderConfig:
        return self._config

    def build_login_url(self, *, state: str) -> str:
        params = {
            "response_type": "code",
            "client_id": self._config.web_client_id,
            "redirect_uri": self._config.web_redirect_uri,
            "scope": "openid profile email offline_access",
            "state": state,
            "audience": self._config.audience,
        }
        return self._config.authorization_endpoint + "?" + urllib_parse.urlencode(params)

    def exchange_code_for_tokens(self, *, code: str) -> dict[str, Any]:
        return _http_json_request(
            method="POST",
            url=self._config.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "client_id": self._config.web_client_id,
                "client_secret": self._config.web_client_secret,
                "code": code,
                "redirect_uri": self._config.web_redirect_uri,
            },
        )

    def build_logout_url(self) -> str:
        params = {
            "post_logout_redirect_uri": self._config.logout_redirect_uri,
        }
        return self._config.logout_endpoint + "?" + urllib_parse.urlencode(params)

    def fetch_userinfo(self, *, access_token: str) -> dict[str, Any]:
        return _http_json_request(
            method="GET",
            url=self._config.userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def fetch_jwks(self) -> dict[str, Any]:
        return _http_json_request(method="GET", url=self._config.jwks_endpoint_url)


class OIDCTokenService:
    """Token validation service compatible with the existing auth middleware contract."""

    def __init__(self, *, provider: KindeOIDCProvider, cache_ttl_seconds: int = 300) -> None:
        self.provider = provider
        self._cache_ttl_seconds = max(60, int(cache_ttl_seconds))
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cached_at_epoch = 0

    @property
    def ttl_minutes(self) -> int:
        # Only used by legacy password token route contract.
        return 60

    def validate_token(self, token: str, *, now_epoch: int | None = None) -> TokenClaims:
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenValidationError("401 unauthorized: token format invalid")

        header_raw, payload_raw, signature_raw = parts
        try:
            header = json.loads(_b64url_decode(header_raw).decode("utf-8"))
            payload = json.loads(_b64url_decode(payload_raw).decode("utf-8"))
        except Exception as error:
            raise TokenValidationError("401 unauthorized: token decode invalid") from error

        if not isinstance(header, dict) or not isinstance(payload, dict):
            raise TokenValidationError("401 unauthorized: token payload invalid")

        if str(header.get("alg", "")).upper() != "RS256":
            raise TokenValidationError("401 unauthorized: token algorithm invalid")
        kid = str(header.get("kid", "")).strip()
        if not kid:
            raise TokenValidationError("401 unauthorized: token kid missing")

        jwk = self._resolve_jwk(kid=kid)
        self._verify_rs256_signature(
            jwk=jwk,
            signing_input=f"{header_raw}.{payload_raw}".encode("ascii"),
            signature=_b64url_decode(signature_raw),
        )

        now = _now_epoch() if now_epoch is None else int(now_epoch)

        iss = str(payload.get("iss", "")).strip()
        if iss != self.provider.config.issuer_url:
            raise TokenValidationError("401 unauthorized: token issuer invalid")

        exp = payload.get("exp")
        if not isinstance(exp, int) or exp <= now:
            raise TokenValidationError("401 unauthorized: token expired")
        nbf = payload.get("nbf")
        if isinstance(nbf, int) and now < nbf:
            raise TokenValidationError("401 unauthorized: token not active")
        iat = payload.get("iat")
        if not isinstance(iat, int):
            raise TokenValidationError("401 unauthorized: token iat invalid")

        if not self._is_valid_audience(payload):
            raise TokenValidationError("401 unauthorized: token audience invalid")

        sub = str(payload.get("sub", "")).strip()
        if not sub:
            raise TokenValidationError("401 unauthorized: token subject invalid")

        scopes = self._extract_scopes(payload)
        if not scopes:
            scopes = ("registry:read",)

        tenant_slug = self._resolve_tenant_slug(payload)

        return TokenClaims(
            iss=iss,
            sub=sub,
            tenant_slug=tenant_slug,
            scopes=scopes,
            token_id=str(payload.get("jti") or f"oidc:{sub}:{iat}"),
            exp=exp,
            iat=iat,
        )

    def _extract_scopes(self, payload: dict[str, Any]) -> tuple[str, ...]:
        scope_raw = payload.get("scope")
        if isinstance(scope_raw, str):
            scopes = tuple(item.strip() for item in scope_raw.split(" ") if item.strip())
            if scopes:
                return scopes

        scp_raw = payload.get("scp")
        if isinstance(scp_raw, list):
            scopes = tuple(str(item).strip() for item in scp_raw if str(item).strip())
            if scopes:
                return scopes

        return ()

    def _resolve_tenant_slug(self, payload: dict[str, Any]) -> str:
        candidate_keys = ("tenant_slug", "org_code", "org", "tenant")
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            return username_to_tenant_slug(email.strip())

        return "global"

    def _is_valid_audience(self, payload: dict[str, Any]) -> bool:
        aud = payload.get("aud")
        expected = {
            self.provider.config.audience,
            self.provider.config.web_client_id,
            self.provider.config.cli_client_id,
        }
        if isinstance(aud, str):
            return aud in expected
        if isinstance(aud, list):
            return any(isinstance(item, str) and item in expected for item in aud)
        return False

    def _resolve_jwk(self, *, kid: str) -> dict[str, Any]:
        now = _now_epoch()
        should_refresh = (
            self._jwks_cache is None
            or (now - self._jwks_cached_at_epoch) >= self._cache_ttl_seconds
        )
        if should_refresh:
            self._jwks_cache = self.provider.fetch_jwks()
            self._jwks_cached_at_epoch = now

        keys = self._jwks_cache.get("keys") if isinstance(self._jwks_cache, dict) else None
        if not isinstance(keys, list):
            raise TokenValidationError("401 unauthorized: jwks response invalid")
        for item in keys:
            if isinstance(item, dict) and str(item.get("kid", "")).strip() == kid:
                return item

        # One forced refresh before failing in case of key rotation.
        self._jwks_cache = self.provider.fetch_jwks()
        self._jwks_cached_at_epoch = now
        keys = self._jwks_cache.get("keys") if isinstance(self._jwks_cache, dict) else None
        if isinstance(keys, list):
            for item in keys:
                if isinstance(item, dict) and str(item.get("kid", "")).strip() == kid:
                    return item

        raise TokenValidationError("401 unauthorized: signing key not found")

    def _verify_rs256_signature(
        self,
        *,
        jwk: dict[str, Any],
        signing_input: bytes,
        signature: bytes,
    ) -> None:
        n_raw = jwk.get("n")
        e_raw = jwk.get("e")
        if not isinstance(n_raw, str) or not isinstance(e_raw, str):
            raise TokenValidationError("401 unauthorized: jwk key invalid")

        try:
            modulus = int.from_bytes(_b64url_decode(n_raw), byteorder="big", signed=False)
            exponent = int.from_bytes(_b64url_decode(e_raw), byteorder="big", signed=False)
            public_key = rsa.RSAPublicNumbers(exponent, modulus).public_key()
            public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
        except Exception as error:
            raise TokenValidationError("401 unauthorized: token signature invalid") from error
