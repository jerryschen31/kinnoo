"""SQLite-backed auth helpers used by registration and reset workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time


@dataclass(frozen=True)
class ReservedTenant:
    tenant_slug: str
    owner_user_id: str


class SQLiteAuthStore:
    """Persist token consumption, tenant slugs, and identity mappings."""

    def __init__(self, *, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS consumed_registration_tokens (
                    token_hash TEXT PRIMARY KEY,
                    consumed_at_epoch INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_slug TEXT PRIMARY KEY,
                    owner_user_id TEXT NOT NULL,
                    created_at_epoch INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS identities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    provider_user_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    provider_email TEXT,
                    created_at_epoch INTEGER NOT NULL,
                    UNIQUE(provider, provider_user_id)
                );
                """
            )

    def mark_registration_token_consumed(self, *, token_hash: str, now_epoch: int | None = None) -> bool:
        timestamp = int(time.time()) if now_epoch is None else int(now_epoch)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT OR IGNORE INTO consumed_registration_tokens (token_hash, consumed_at_epoch) VALUES (?, ?)",
                (token_hash, timestamp),
            )
            return cursor.rowcount == 1

    def reserve_tenant_slug(self, *, base_slug: str, owner_user_id: str, now_epoch: int | None = None) -> ReservedTenant:
        timestamp = int(time.time()) if now_epoch is None else int(now_epoch)
        suffix = 0

        while True:
            candidate = base_slug if suffix == 0 else f"{base_slug}-{suffix}"
            with self._connect() as connection:
                cursor = connection.execute(
                    "INSERT OR IGNORE INTO tenants (tenant_slug, owner_user_id, created_at_epoch) VALUES (?, ?, ?)",
                    (candidate, owner_user_id, timestamp),
                )
                if cursor.rowcount == 1:
                    return ReservedTenant(tenant_slug=candidate, owner_user_id=owner_user_id)
            suffix += 1

    def upsert_local_identity(self, *, user_id: str, provider_user_id: str, provider_email: str) -> None:
        now_epoch = int(time.time())
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO identities (provider, provider_user_id, user_id, provider_email, created_at_epoch)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider, provider_user_id)
                DO UPDATE SET user_id = excluded.user_id, provider_email = excluded.provider_email
                """,
                ("local", provider_user_id, user_id, provider_email, now_epoch),
            )