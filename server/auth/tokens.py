"""Signed token helpers for registration and password-reset flows."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import time


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@dataclass(frozen=True)
class RegistrationTokenService:
    """Issue signed, expiring registration tokens."""

    signing_secret: str
    ttl_seconds: int = 24 * 60 * 60

    def issue_token(self, *, email: str, now_epoch: int | None = None) -> str:
        now = int(time.time()) if now_epoch is None else int(now_epoch)
        payload = {
            "token_type": "register",
            "email": email.strip().lower(),
            "iat": now,
            "exp": now + self.ttl_seconds,
            "nonce": secrets.token_urlsafe(16),
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_segment = _b64url_encode(payload_json)
        signature = hmac.new(
            self.signing_secret.encode("utf-8"),
            payload_segment.encode("ascii"),
            hashlib.sha256,
        ).digest()
        signature_segment = _b64url_encode(signature)
        return f"{payload_segment}.{signature_segment}"

    def verify_token(self, *, token: str, now_epoch: int | None = None) -> dict[str, object] | None:
        try:
            payload_segment, signature_segment = token.split(".", 1)
        except ValueError:
            return None

        expected_signature = hmac.new(
            self.signing_secret.encode("utf-8"),
            payload_segment.encode("ascii"),
            hashlib.sha256,
        ).digest()
        expected_signature_segment = _b64url_encode(expected_signature)
        if not hmac.compare_digest(signature_segment, expected_signature_segment):
            return None

        try:
            payload_bytes = base64.urlsafe_b64decode(payload_segment + "===")
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return None

        if not isinstance(payload, dict):
            return None
        if payload.get("token_type") != "register":
            return None

        now = int(time.time()) if now_epoch is None else int(now_epoch)
        try:
            exp = int(payload.get("exp", 0))
        except (TypeError, ValueError):
            return None
        if exp <= now:
            return None

        return payload

    def hash_token(self, *, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()