"""JSON-backed user persistence for the remote registry server."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Iterable

from server.models.user import Role, User


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


def usernames(users: Iterable[User]) -> list[str]:
    return [user.username for user in users]
