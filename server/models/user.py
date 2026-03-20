"""User model and password hashing primitives for the remote registry server."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import importlib
import secrets
from typing import Literal
from uuid import uuid4


Role = Literal["admin", "user"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PasswordManager:
    """Hash and verify passwords using a strong algorithm with safe fallbacks."""

    def __init__(self) -> None:
        self._argon2_module = None
        self._argon2_hasher = None
        try:
            self._argon2_module = importlib.import_module("argon2")
            hasher_class = getattr(self._argon2_module, "PasswordHasher", None)
            if hasher_class is not None:
                self._argon2_hasher = hasher_class()
        except Exception:  # pragma: no cover - exercised only when argon2 is unavailable
            self._argon2_module = None
            self._argon2_hasher = None

    def hash_password(self, plaintext_password: str) -> str:
        password = self._validate_password(plaintext_password)
        if self._argon2_hasher is not None:
            return self._argon2_hasher.hash(password)

        # Fall back to scrypt when argon2 is unavailable to keep security strong.
        salt = secrets.token_bytes(16)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return f"scrypt${salt.hex()}${digest.hex()}"

    def verify_password(self, plaintext_password: str, password_hash: str) -> bool:
        password = self._validate_password(plaintext_password)
        if not isinstance(password_hash, str) or not password_hash.strip():
            return False

        if password_hash.startswith("$argon2"):
            if self._argon2_hasher is None:
                return False
            verify_mismatch_error = Exception
            invalid_hash_error = Exception
            if self._argon2_module is not None:
                exceptions_module = getattr(self._argon2_module, "exceptions", None)
                if exceptions_module is not None:
                    verify_mismatch_error = getattr(
                        exceptions_module,
                        "VerifyMismatchError",
                        Exception,
                    )
                    invalid_hash_error = getattr(
                        exceptions_module,
                        "InvalidHashError",
                        Exception,
                    )
            try:
                return bool(self._argon2_hasher.verify(password_hash, password))
            except (verify_mismatch_error, invalid_hash_error):
                return False

        if password_hash.startswith("scrypt$"):
            try:
                _prefix, salt_hex, expected_hex = password_hash.split("$", 2)
                salt = bytes.fromhex(salt_hex)
                expected = bytes.fromhex(expected_hex)
            except ValueError:
                return False
            derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
            return hmac.compare_digest(derived, expected)

        return False

    @staticmethod
    def _validate_password(plaintext_password: str) -> str:
        if not isinstance(plaintext_password, str) or not plaintext_password:
            raise ValueError("Password must be a non-empty string.")
        return plaintext_password


PASSWORD_MANAGER = PasswordManager()


@dataclass(frozen=True)
class User:
    """Immutable user record persisted as JSON in the registry server backend."""

    id: str
    username: str
    password_hash: str
    role: Role
    force_password_change: bool
    created_at: str
    updated_at: str

    @classmethod
    def create(
        cls,
        *,
        username: str,
        plaintext_password: str,
        role: Role = "user",
        force_password_change: bool = False,
    ) -> "User":
        normalized_username = cls._normalize_username(username)
        normalized_role = cls._normalize_role(role)
        password_hash = PASSWORD_MANAGER.hash_password(plaintext_password)
        timestamp = _utc_now_iso()
        return cls(
            id=str(uuid4()),
            username=normalized_username,
            password_hash=password_hash,
            role=normalized_role,
            force_password_change=bool(force_password_change),
            created_at=timestamp,
            updated_at=timestamp,
        )

    @classmethod
    def from_document(cls, document: dict[str, str]) -> "User":
        required_fields = ["id", "username", "password_hash", "role", "created_at", "updated_at"]
        missing_fields = [field for field in required_fields if field not in document]
        if missing_fields:
            missing_label = ", ".join(missing_fields)
            raise ValueError(f"User document missing required fields: {missing_label}")

        return cls(
            id=str(document["id"]),
            username=cls._normalize_username(str(document["username"])),
            password_hash=str(document["password_hash"]),
            role=cls._normalize_role(str(document["role"])),
            # Older documents may not have this key; default to False.
            force_password_change=bool(document.get("force_password_change", False)),
            created_at=str(document["created_at"]),
            updated_at=str(document["updated_at"]),
        )

    def to_document(self) -> dict[str, str | bool]:
        return {
            "id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "force_password_change": self.force_password_change,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def verify_password(self, plaintext_password: str) -> bool:
        return PASSWORD_MANAGER.verify_password(plaintext_password, self.password_hash)

    @staticmethod
    def _normalize_username(username: str) -> str:
        if not isinstance(username, str) or not username.strip():
            raise ValueError("Username must be a non-empty string.")
        return username.strip()

    @staticmethod
    def _normalize_role(role: str) -> Role:
        if role not in {"admin", "user"}:
            raise ValueError("Role must be either 'admin' or 'user'.")
        return role  # type: ignore[return-value]
