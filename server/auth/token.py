"""JWT-style token issuance and validation for registry auth flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
from typing import Any

from server.storage.user_store import UserStore


class TokenValidationError(Exception):
    """Raised when a token cannot be validated."""


@dataclass(frozen=True)
class TokenClaims:
    iss: str
    sub: str
    tenant_slug: str
    scopes: tuple[str, ...]
    token_id: str
    exp: int
    iat: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "iss": self.iss,
            "sub": self.sub,
            "tenant_slug": self.tenant_slug,
            "scopes": list(self.scopes),
            "token_id": self.token_id,
            "exp": self.exp,
            "iat": self.iat,
        }


@dataclass(frozen=True)
class SigningKey:
    kid: str
    secret: str


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _json_dumps(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(digest)


class TokenService:
    """Issue and verify HMAC-signed JWT-compatible tokens."""

    def __init__(
        self,
        *,
        issuer: str,
        current_signing_key: SigningKey,
        previous_signing_key: SigningKey | None = None,
        ttl_minutes: int = 60,
    ) -> None:
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes must be positive")
        self.issuer = issuer
        self.current_signing_key = current_signing_key
        self.previous_signing_key = previous_signing_key
        self.ttl_minutes = ttl_minutes
        self._denylist: set[str] = set()

    def issue_token(
        self,
        *,
        subject: str,
        tenant_slug: str,
        scopes: list[str],
    ) -> str:
        now = datetime.now(timezone.utc)
        iat = int(now.timestamp())
        exp = int((now + timedelta(minutes=self.ttl_minutes)).timestamp())
        claims = TokenClaims(
            iss=self.issuer,
            sub=subject,
            tenant_slug=tenant_slug,
            scopes=tuple(scopes),
            token_id=secrets.token_hex(16),
            exp=exp,
            iat=iat,
        )
        header = {"alg": "HS256", "typ": "JWT", "kid": self.current_signing_key.kid}
        header_segment = _b64url_encode(_json_dumps(header))
        payload_segment = _b64url_encode(_json_dumps(claims.to_dict()))
        signing_input = f"{header_segment}.{payload_segment}"
        signature = _sign(signing_input, self.current_signing_key.secret)
        return f"{signing_input}.{signature}"

    def validate_token(self, token: str, *, now_epoch: int | None = None) -> TokenClaims:
        header_raw, payload_raw, signature = self._split_token(token)
        header = self._decode_header(header_raw)
        payload = self._decode_payload(payload_raw)

        signing_input = f"{header_raw}.{payload_raw}"
        self._validate_signature(signing_input=signing_input, signature=signature, header=header)

        token_id = payload.get("token_id")
        if not isinstance(token_id, str) or not token_id:
            raise TokenValidationError("401 unauthorized: token_id missing")
        if token_id in self._denylist:
            raise TokenValidationError("401 unauthorized: token revoked")

        now = now_epoch if now_epoch is not None else int(datetime.now(timezone.utc).timestamp())
        exp = payload.get("exp")
        if not isinstance(exp, int) or exp <= now:
            raise TokenValidationError("401 unauthorized: token expired")

        iat = payload.get("iat")
        if not isinstance(iat, int):
            raise TokenValidationError("401 unauthorized: token iat invalid")

        iss = payload.get("iss")
        if not isinstance(iss, str) or iss != self.issuer:
            raise TokenValidationError("401 unauthorized: token issuer invalid")

        sub = payload.get("sub")
        tenant_slug = payload.get("tenant_slug")
        scopes = payload.get("scopes")
        if not isinstance(sub, str) or not sub:
            raise TokenValidationError("401 unauthorized: token subject invalid")
        if not isinstance(tenant_slug, str) or not tenant_slug:
            raise TokenValidationError("401 unauthorized: token tenant invalid")
        if not isinstance(scopes, list) or not all(isinstance(scope, str) for scope in scopes):
            raise TokenValidationError("401 unauthorized: token scopes invalid")

        return TokenClaims(
            iss=iss,
            sub=sub,
            tenant_slug=tenant_slug,
            scopes=tuple(scopes),
            token_id=token_id,
            exp=exp,
            iat=iat,
        )

    def revoke_token_id(self, token_id: str) -> None:
        if token_id:
            self._denylist.add(token_id)

    def issue_token_for_credentials(
        self,
        *,
        username: str,
        plaintext_password: str,
        user_store: UserStore,
        tenant_slug: str = "global",
    ) -> str:
        user = user_store.get_by_username(username)
        if user is None or not user.verify_password(plaintext_password):
            raise PermissionError("401 unauthorized: invalid username or password")

        if user.role == "admin":
            scopes = ["registry:read", "registry:publish", "registry:admin"]
        else:
            scopes = ["registry:read"]

        return self.issue_token(subject=user.id, tenant_slug=tenant_slug, scopes=scopes)

    def _validate_signature(self, *, signing_input: str, signature: str, header: dict[str, Any]) -> None:
        kid = header.get("kid")
        keys_to_try: list[SigningKey] = []
        if isinstance(kid, str):
            if kid == self.current_signing_key.kid:
                keys_to_try.append(self.current_signing_key)
            elif self.previous_signing_key is not None and kid == self.previous_signing_key.kid:
                keys_to_try.append(self.previous_signing_key)

        if not keys_to_try:
            # Fallback path to support key rotation overlap and tokens with stale/unknown kid.
            keys_to_try = [self.current_signing_key]
            if self.previous_signing_key is not None:
                keys_to_try.append(self.previous_signing_key)

        for key in keys_to_try:
            expected_signature = _sign(signing_input, key.secret)
            if hmac.compare_digest(signature, expected_signature):
                return

        raise TokenValidationError("401 unauthorized: token signature invalid")

    @staticmethod
    def _split_token(token: str) -> tuple[str, str, str]:
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenValidationError("401 unauthorized: token format invalid")
        return parts[0], parts[1], parts[2]

    @staticmethod
    def _decode_header(encoded_header: str) -> dict[str, Any]:
        try:
            header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
        except Exception as error:
            raise TokenValidationError("401 unauthorized: token header invalid") from error
        if not isinstance(header, dict):
            raise TokenValidationError("401 unauthorized: token header invalid")
        return header

    @staticmethod
    def _decode_payload(encoded_payload: str) -> dict[str, Any]:
        try:
            payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        except Exception as error:
            raise TokenValidationError("401 unauthorized: token payload invalid") from error
        if not isinstance(payload, dict):
            raise TokenValidationError("401 unauthorized: token payload invalid")
        return payload
