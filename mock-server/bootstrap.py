"""One-time bootstrap flow for creating the first admin user."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import secrets

from server.storage.user_store import UserStore


@dataclass(frozen=True)
class BootstrapResult:
    created: bool
    message: str
    username: str | None = None
    temporary_password: str | None = None


def _generate_temporary_password(length: int = 24) -> str:
    # token_urlsafe returns URL-safe random bytes and can include punctuation.
    return secrets.token_urlsafe(length)


def bootstrap_admin(*, store_root: Path, username: str = "admin") -> BootstrapResult:
    store = UserStore(store_root)
    if store.any_admin_exists():
        return BootstrapResult(
            created=False,
            message="Bootstrap refused: admin already exists.",
        )

    temporary_password = _generate_temporary_password()
    created_user = store.create_user(
        username=username,
        plaintext_password=temporary_password,
        role="admin",
        force_password_change=True,
    )
    return BootstrapResult(
        created=True,
        message="Bootstrap complete: admin account created.",
        username=created_user.username,
        temporary_password=temporary_password,
    )
