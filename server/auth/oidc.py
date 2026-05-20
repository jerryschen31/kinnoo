"""Provider-portable OIDC adapter + token validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import json
import os
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from server.auth.token import TokenClaims, TokenValidationError
from server.config import REQUIRED_AUTH_ENV_KEYS, resolve_auth_env_contract
from server.models.user import username_to_tenant_slug


def _b64url_decode(value: str) -> bytes:
    padding_text = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding_text).encode("ascii"))


def _now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


class OIDCRequestError(Exception):
    """Raised when provider HTTP/JSON responses cannot be safely consumed."""


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
    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read().decode("utf-8")
    except urllib_error.HTTPError as error:
        detail = ""
        try:
            raw_error_payload = error.read().decode("utf-8")
            parsed_error = json.loads(raw_error_payload)
            if isinstance(parsed_error, dict):
                code = str(parsed_error.get("error", "")).strip()
                desc = str(parsed_error.get("error_description", "")).strip()
                if code or desc:
                    detail = f" provider_error={code or 'unknown'}"
                    if desc:
                        detail += f" provider_error_description={desc}"
        except Exception:
            detail = ""
        raise OIDCRequestError(
            f"OIDC {method.upper()} {url} failed with HTTP {error.code}.{detail}"
        ) from error
    except urllib_error.URLError as error:
        raise OIDCRequestError(
            f"OIDC {method.upper()} {url} failed due to network error: {error.reason!s}."
        ) from error
    except (TimeoutError, UnicodeDecodeError) as error:
        raise OIDCRequestError(
            f"OIDC {method.upper()} {url} returned an unreadable response payload."
        ) from error

    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OIDCRequestError(
            f"OIDC {method.upper()} {url} returned invalid JSON."
        ) from error
    if not isinstance(decoded, dict):
        raise OIDCRequestError(
            f"OIDC {method.upper()} {url} returned non-object JSON payload (got {type(decoded).__name__})."
        )
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
        resolved = resolve_auth_env_contract(env=env)
        missing = [name for name in REQUIRED_AUTH_ENV_KEYS if not resolved.get(name)]
        if missing:
            if strict:
                raise ValueError(
                    "Missing required OIDC configuration: " + ", ".join(sorted(missing))
                )
            return None

        return cls(
            issuer_url=resolved["AUTH_ISSUER_URL"].strip(),
            jwks_endpoint_url=resolved["AUTH_JWKS_ENDPOINT_URL"].strip(),
            token_endpoint=resolved["AUTH_TOKEN_ENDPOINT"].strip(),
            authorization_endpoint=resolved["AUTH_AUTHORIZATION_ENDPOINT"].strip(),
            logout_endpoint=resolved["AUTH_LOGOUT_ENDPOINT"].strip(),
            userinfo_endpoint=resolved["AUTH_USERINFO_ENDPOINT"].strip(),
            audience=resolved["AUTH_AUDIENCE"].strip(),
            web_client_id=resolved["AUTH_WEB_CLIENT_ID"].strip(),
            web_client_secret=resolved["AUTH_WEB_CLIENT_SECRET"].strip(),
            cli_client_id=resolved["AUTH_CLI_CLIENT_ID"].strip(),
            web_redirect_uri=resolved["AUTH_WEB_REDIRECT_URI"].strip(),
            logout_redirect_uri=resolved["AUTH_LOGOUT_REDIRECT_URI"].strip(),
        )


class KindeOIDCProvider:
    """Kinde-backed adapter constrained to provider-portable OIDC interfaces."""

    def __init__(self, *, config: OIDCProviderConfig) -> None:
        self._config = config

    @property
    def config(self) -> OIDCProviderConfig:
        return self._config

    def _build_authorization_url(self, *, state: str, extra_params: dict[str, str] | None = None) -> str:
        params = {
            "response_type": "code",
            "client_id": self._config.web_client_id,
            "redirect_uri": self._config.web_redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "audience": self._config.audience,
        }
        if extra_params:
            params.update(extra_params)
        return self._config.authorization_endpoint + "?" + urllib_parse.urlencode(params)

    def build_login_url(self, *, state: str) -> str:
        # Web login does not require refresh-token scope; some Kinde web clients
        # reject offline_access by default and fail auth initiation.
        return self._build_authorization_url(state=state)

    def build_signup_url(self, *, state: str) -> str:
        # Hint hosted auth to open registration first when provider supports it.
        return self._build_authorization_url(
            state=state,
            extra_params={
                "start_page": "sign_up",
                "prompt": "create",
            },
        )

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

        payload = self._augment_payload_with_userinfo_email(payload=payload, access_token=token)
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
        scopes: tuple[str, ...] = ()
        if isinstance(scope_raw, str):
            scopes = tuple(item.strip() for item in scope_raw.split(" ") if item.strip())
            if scopes:
                return self._normalize_registry_scopes(scopes)

        scp_raw = payload.get("scp")
        if isinstance(scp_raw, list):
            scopes = tuple(str(item).strip() for item in scp_raw if str(item).strip())
            if scopes:
                return self._normalize_registry_scopes(scopes)

        return ()

    def _normalize_registry_scopes(self, scopes: tuple[str, ...]) -> tuple[str, ...]:
        if any(scope.startswith("registry:") for scope in scopes):
            return scopes

        compatibility_enabled = self._is_scope_compatibility_enabled()
        if compatibility_enabled and any(scope in {"openid", "profile", "email"} for scope in scopes):
            ordered = dict.fromkeys((*scopes, "registry:read", "registry:publish"))
            return tuple(ordered.keys())
        return scopes

    def _is_scope_compatibility_enabled(self) -> bool:
        raw = (os.getenv("AUTH_ENABLE_OIDC_SCOPE_COMPAT") or "true").strip().lower()
        return raw not in {"0", "false", "no", "off"}

    def _augment_payload_with_userinfo_email(
        self,
        *,
        payload: dict[str, Any],
        access_token: str,
    ) -> dict[str, Any]:
        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            return payload

        try:
            userinfo = self.provider.fetch_userinfo(access_token=access_token.strip())
        except OIDCRequestError:
            return payload

        if not isinstance(userinfo, dict):
            return payload

        resolved_email = userinfo.get("email")
        if not isinstance(resolved_email, str) or not resolved_email.strip():
            return payload

        merged_payload = dict(payload)
        merged_payload["email"] = resolved_email.strip()
        return merged_payload

    def _resolve_tenant_slug(self, payload: dict[str, Any]) -> str:
        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            return username_to_tenant_slug(email.strip())

        candidate_keys = ("tenant_slug", "org_code", "org", "tenant")
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        subject = payload.get("sub")
        if isinstance(subject, str) and subject.strip():
            return username_to_tenant_slug(f"{subject.strip()}@kinde.local")

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
            try:
                self._jwks_cache = self.provider.fetch_jwks()
            except OIDCRequestError as error:
                raise TokenValidationError("503 service unavailable: jwks fetch failed") from error
            self._jwks_cached_at_epoch = now

        keys = self._jwks_cache.get("keys") if isinstance(self._jwks_cache, dict) else None
        if not isinstance(keys, list):
            raise TokenValidationError("401 unauthorized: jwks response invalid")
        for item in keys:
            if isinstance(item, dict) and str(item.get("kid", "")).strip() == kid:
                return item

        # One forced refresh before failing in case of key rotation.
        try:
            self._jwks_cache = self.provider.fetch_jwks()
        except OIDCRequestError as error:
            raise TokenValidationError("503 service unavailable: jwks fetch failed") from error
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
