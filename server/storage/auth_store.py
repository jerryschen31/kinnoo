"""Protocol definitions for relational auth persistence backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ReservedTenant:
    tenant_slug: str
    owner_user_id: str


@dataclass(frozen=True)
class IdentityMapping:
    user_id: str
    provider: str
    provider_user_id: str
    provider_email: str | None


class AuthStore(Protocol):
    """Common contract for auth-store implementations (SQLite now, PostgreSQL later)."""

    def mark_registration_token_consumed(self, *, token_hash: str, now_epoch: int | None = None) -> bool:
        ...

    def mark_password_reset_token_consumed(self, *, token_hash: str, now_epoch: int | None = None) -> bool:
        ...

    def reserve_tenant_slug(self, *, base_slug: str, owner_user_id: str, now_epoch: int | None = None) -> ReservedTenant:
        ...

    def upsert_local_identity(self, *, user_id: str, provider_user_id: str, provider_email: str) -> None:
        ...

    def upsert_external_identity(
        self,
        *,
        provider: str,
        provider_user_id: str,
        user_id: str,
        provider_email: str | None = None,
    ) -> None:
        ...

    def get_identity_mapping(self, *, provider: str, provider_user_id: str) -> IdentityMapping | None:
        ...

    def upsert_tenant_owner(self, *, tenant_slug: str, owner_user_id: str, now_epoch: int | None = None) -> ReservedTenant:
        ...
