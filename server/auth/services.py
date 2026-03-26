"""Auth service helpers for bootstrap and account lifecycle behavior."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from urllib.parse import urlencode

from server.storage.user_store import UserStore


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_admin_account(*, user_store: UserStore, username: str, plaintext_password: str) -> tuple[bool, str]:
    """Ensure an admin-capable account exists for the provided username.

    Returns a tuple (changed, message) where changed indicates if the store was modified.
    Messages are intentionally secret-safe and never include plaintext password values.
    """
    normalized_username = username.strip()
    if not normalized_username:
        return False, "Admin bootstrap skipped: REGISTRY_ADMIN_EMAIL is empty."
    if not plaintext_password:
        return False, "Admin bootstrap skipped: REGISTRY_ADMIN_PASSWORD is empty."

    existing = user_store.get_by_username(normalized_username)
    if existing is None:
        user_store.create_user(
            username=normalized_username,
            plaintext_password=plaintext_password,
            role="admin",
            force_password_change=False,
        )
        return True, "Admin bootstrap ensured admin account from environment."

    if existing.role == "admin":
        return False, "Admin bootstrap verified existing admin account from environment."

    promoted = replace(
        existing,
        role="admin",
        updated_at=_utc_now_iso(),
    )
    user_store.save(promoted)
    return True, "Admin bootstrap promoted existing account to admin role."


def build_registration_verification_link(*, frontend_url: str, token: str) -> str:
    """Build the frontend verification URL for register-request messages."""
    root = frontend_url.rstrip("/")
    query = urlencode({"token": token})
    return f"{root}/signup/verify?{query}"


def registration_generic_success_message() -> str:
    """Generic, non-enumerating registration response contract."""
    return "If this email is valid, you'll receive a verification link"
