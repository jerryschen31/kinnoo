"""Session-cookie authentication helpers for web UI routes."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import time
from typing import Any
from uuid import uuid4


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


@dataclass(frozen=True)
class SessionCookie:
    """Cookie contract expected by the web UI layer."""

    name: str
    value: str
    http_only: bool
    secure: bool
    same_site: str
    path: str
    max_age_seconds: int


@dataclass(frozen=True)
class SessionRecord:
    """Session state persisted server-side as JSON."""

    session_id: str
    user_id: str
    csrf_token: str
    created_at_epoch: int
    expires_at_epoch: int
    invalidated_at_epoch: int | None

    def to_document(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "csrf_token": self.csrf_token,
            "created_at_epoch": self.created_at_epoch,
            "expires_at_epoch": self.expires_at_epoch,
            "invalidated_at_epoch": self.invalidated_at_epoch,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "SessionRecord":
        required = [
            "session_id",
            "user_id",
            "csrf_token",
            "created_at_epoch",
            "expires_at_epoch",
            "invalidated_at_epoch",
        ]
        missing = [field for field in required if field not in document]
        if missing:
            raise ValueError(f"Session document missing required fields: {', '.join(missing)}")

        return cls(
            session_id=str(document["session_id"]),
            user_id=str(document["user_id"]),
            csrf_token=str(document["csrf_token"]),
            created_at_epoch=int(document["created_at_epoch"]),
            expires_at_epoch=int(document["expires_at_epoch"]),
            invalidated_at_epoch=(
                None if document["invalidated_at_epoch"] is None else int(document["invalidated_at_epoch"])
            ),
        )


class SessionService:
    """Create, validate, and invalidate signed cookie sessions."""

    def __init__(
        self,
        *,
        root: Path,
        signing_secret: str,
        cookie_name: str = "kinnoo_session",
        ttl_hours: int = 10,
    ) -> None:
        if not isinstance(signing_secret, str) or not signing_secret:
            raise ValueError("signing_secret must be a non-empty string")
        if ttl_hours < 8 or ttl_hours > 12:
            raise ValueError("ttl_hours must be within [8, 12]")

        self._root = Path(root)
        self._sessions_dir = self._root / "sessions"
        self._sessions_dir.mkdir(parents=True, exist_ok=True)

        self._signing_secret = signing_secret
        self.cookie_name = cookie_name
        self.ttl_seconds = ttl_hours * 60 * 60

    def create_session(self, *, user_id: str, now_epoch: int | None = None) -> tuple[SessionRecord, SessionCookie]:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")

        now = int(time.time()) if now_epoch is None else now_epoch
        session_id = uuid4().hex
        record = SessionRecord(
            session_id=session_id,
            user_id=user_id.strip(),
            csrf_token=secrets.token_urlsafe(32),
            created_at_epoch=now,
            expires_at_epoch=now + self.ttl_seconds,
            invalidated_at_epoch=None,
        )
        self._write_session(record)

        cookie = SessionCookie(
            name=self.cookie_name,
            value=self._sign_cookie_value(session_id),
            http_only=True,
            secure=True,
            same_site="Lax",
            path="/",
            max_age_seconds=self.ttl_seconds,
        )
        return record, cookie

    def validate_session_cookie(
        self,
        *,
        cookie_value: str | None,
        now_epoch: int | None = None,
    ) -> SessionRecord:
        if not cookie_value:
            raise PermissionError("401 unauthorized: missing session cookie")

        session_id = self._verify_cookie_value(cookie_value)
        record = self._read_session(session_id)
        if record is None:
            raise PermissionError("401 unauthorized: session not found")
        if record.invalidated_at_epoch is not None:
            raise PermissionError("401 unauthorized: session invalidated")

        now = int(time.time()) if now_epoch is None else now_epoch
        if record.expires_at_epoch <= now:
            raise PermissionError("401 unauthorized: session expired")

        return record

    def validate_post_request(
        self,
        *,
        cookie_value: str | None,
        csrf_token: str | None,
        now_epoch: int | None = None,
    ) -> SessionRecord:
        record = self.validate_session_cookie(cookie_value=cookie_value, now_epoch=now_epoch)
        self._validate_csrf(record=record, csrf_token=csrf_token)
        return record

    def logout(self, *, cookie_value: str | None, now_epoch: int | None = None) -> bool:
        if not cookie_value:
            return False
        try:
            session_id = self._verify_cookie_value(cookie_value)
        except PermissionError:
            return False

        record = self._read_session(session_id)
        if record is None or record.invalidated_at_epoch is not None:
            return False

        now = int(time.time()) if now_epoch is None else now_epoch
        updated = SessionRecord(
            session_id=record.session_id,
            user_id=record.user_id,
            csrf_token=record.csrf_token,
            created_at_epoch=record.created_at_epoch,
            expires_at_epoch=record.expires_at_epoch,
            invalidated_at_epoch=now,
        )
        self._write_session(updated)
        return True

    def invalidate_user_sessions(self, *, user_id: str, now_epoch: int | None = None) -> int:
        now = int(time.time()) if now_epoch is None else now_epoch
        invalidated_count = 0
        for path in sorted(self._sessions_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            record = SessionRecord.from_document(raw)
            if record.user_id != user_id or record.invalidated_at_epoch is not None:
                continue
            updated = SessionRecord(
                session_id=record.session_id,
                user_id=record.user_id,
                csrf_token=record.csrf_token,
                created_at_epoch=record.created_at_epoch,
                expires_at_epoch=record.expires_at_epoch,
                invalidated_at_epoch=now,
            )
            self._write_session(updated)
            invalidated_count += 1
        return invalidated_count

    def _validate_csrf(self, *, record: SessionRecord, csrf_token: str | None) -> None:
        if not csrf_token:
            raise PermissionError("403 forbidden: missing csrf token")
        if not hmac.compare_digest(record.csrf_token, csrf_token):
            raise PermissionError("403 forbidden: csrf token invalid")

    def _session_path(self, session_id: str) -> Path:
        return self._sessions_dir / f"{session_id}.json"

    def _read_session(self, session_id: str) -> SessionRecord | None:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid session document at {path}: expected JSON object")
        return SessionRecord.from_document(raw)

    def _write_session(self, record: SessionRecord) -> None:
        path = self._session_path(record.session_id)
        path.write_text(
            json.dumps(record.to_document(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _sign_cookie_value(self, session_id: str) -> str:
        signature = hmac.new(
            self._signing_secret.encode("utf-8"),
            session_id.encode("ascii"),
            hashlib.sha256,
        ).digest()
        return f"{session_id}.{_b64url_encode(signature)}"

    def _verify_cookie_value(self, cookie_value: str) -> str:
        parts = cookie_value.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise PermissionError("401 unauthorized: malformed session cookie")

        session_id, provided_signature = parts
        expected_cookie_value = self._sign_cookie_value(session_id)
        expected_signature = expected_cookie_value.split(".", 1)[1]
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise PermissionError("401 unauthorized: session signature invalid")
        return session_id
