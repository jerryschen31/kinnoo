"""JSON-backed user persistence for the remote registry server."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import secrets
from typing import Iterable

from server.models.user import PASSWORD_MANAGER, Role, User, username_to_tenant_slug


class UserStore:
    """Store user records as one-document-per-user JSON files."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._users_dir = self._root / "users"
        self._users_dir.mkdir(parents=True, exist_ok=True)

    def create_user(
        self,
        *,
        username: str,
        plaintext_password: str,
        role: Role = "user",
        force_password_change: bool = False,
    ) -> User:
        if self.get_by_username(username) is not None:
            raise ValueError(f"User already exists for username '{username}'.")

        user = User.create(
            username=username,
            plaintext_password=plaintext_password,
            role=role,
            force_password_change=force_password_change,
        )
        self.save(user)
        return user

    def save(self, user: User) -> None:
        user_path = self._users_dir / f"{user.id}.json"
        user_path.write_text(json.dumps(user.to_document(), indent=2, sort_keys=True), encoding="utf-8")

    def list_users(self) -> list[User]:
        users: list[User] = []
        for path in sorted(self._users_dir.glob("*.json")):
            users.append(self._read_user(path))
        return users

    def get_by_id(self, user_id: str) -> User | None:
        user_path = self._users_dir / f"{user_id}.json"
        if not user_path.exists():
            return None
        return self._read_user(user_path)

    def get_by_username(self, username: str) -> User | None:
        normalized = username.strip().lower()
        for user in self.list_users():
            if user.username.lower() == normalized:
                return user
        return None

    def any_admin_exists(self) -> bool:
        return any(user.role == "admin" for user in self.list_users())

    def reset_password(self, *, email: str, new_password: str) -> User:
        user = self.get_by_username(email)
        if user is None:
            raise ValueError(f"User not found for email '{email}'.")

        updated = replace(
            user,
            password_hash=PASSWORD_MANAGER.hash_password(new_password),
            password_changed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            force_password_change=True,
            updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.save(updated)
        return updated

    def unlock_user(self, *, email: str) -> User:
        user = self.get_by_username(email)
        if user is None:
            raise ValueError(f"User not found for email '{email}'.")
        return self.reset_login_failures(user=user)

    def delete_user(self, *, email: str) -> bool:
        user = self.get_by_username(email)
        if user is None:
            return False
        user_path = self._users_dir / f"{user.id}.json"
        user_path.unlink(missing_ok=True)
        return True

    def create_invite(self, *, email: str, days_valid: int) -> dict[str, object]:
        normalized_email = email.strip().lower()
        if days_valid <= 0:
            raise ValueError("days_valid must be positive")

        invites = self._load_invites()
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=days_valid)

        invite = {
            "email": normalized_email,
            "tenant_slug": username_to_tenant_slug(normalized_email),
            "token": token,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "consumed": False,
        }
        invites.append(invite)
        self._save_invites(invites)
        return invite

    def list_invites(self) -> list[dict[str, object]]:
        invites = self._load_invites()
        return sorted(invites, key=lambda item: str(item.get("created_at", "")), reverse=True)

    def validate_invite(self, *, token: str) -> dict[str, object] | None:
        now = datetime.now(timezone.utc)
        for invite in self._load_invites():
            if str(invite.get("token", "")) != token:
                continue
            if bool(invite.get("consumed", False)):
                return None
            expires_at_raw = str(invite.get("expires_at", ""))
            try:
                expires_at = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            except ValueError:
                return None
            if expires_at <= now:
                return None
            return invite
        return None

    def consume_invite(self, *, token: str) -> bool:
        invites = self._load_invites()
        changed = False
        for index, invite in enumerate(invites):
            if str(invite.get("token", "")) == token and not bool(invite.get("consumed", False)):
                invite_copy = dict(invite)
                invite_copy["consumed"] = True
                invites[index] = invite_copy
                changed = True
                break
        if changed:
            self._save_invites(invites)
        return changed

    def increment_failed_login(self, *, user: User, lockout_after: int = 5, lockout_minutes: int = 15) -> User:
        attempts = int(user.failed_login_attempts) + 1
        lock_until: str | None = None
        if attempts >= lockout_after:
            attempts = lockout_after
            lock_until = (
                datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
            ).isoformat().replace("+00:00", "Z")

        updated = replace(
            user,
            failed_login_attempts=attempts,
            locked_until=lock_until,
            updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.save(updated)
        return updated

    def reset_login_failures(self, *, user: User) -> User:
        updated = replace(
            user,
            failed_login_attempts=0,
            locked_until=None,
            updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        self.save(updated)
        return updated

    def _read_user(self, path: Path) -> User:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid user document at {path}: expected JSON object.")
        return User.from_document(raw)

    def _invites_path(self) -> Path:
        return self._root / "invites.json"

    def _load_invites(self) -> list[dict[str, object]]:
        path = self._invites_path()
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        return []

    def _save_invites(self, invites: list[dict[str, object]]) -> None:
        path = self._invites_path()
        path.write_text(json.dumps(invites, indent=2, sort_keys=True), encoding="utf-8")


def usernames(users: Iterable[User]) -> list[str]:
    return [user.username for user in users]
