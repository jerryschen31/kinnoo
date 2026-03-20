"""Tenant model and slug validation utilities for the remote registry server."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Literal


TENANT_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
Visibility = Literal["public", "private"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Tenant:
    """Immutable tenant metadata persisted in backend JSON documents."""

    tenant_slug: str
    owner_user_id: str
    visibility: Visibility
    created_at: str

    @classmethod
    def create(
        cls,
        *,
        tenant_slug: str,
        owner_user_id: str,
        visibility: Visibility = "private",
    ) -> "Tenant":
        return cls(
            tenant_slug=cls._normalize_tenant_slug(tenant_slug),
            owner_user_id=cls._normalize_owner_user_id(owner_user_id),
            visibility=cls._normalize_visibility(visibility),
            created_at=_utc_now_iso(),
        )

    @classmethod
    def from_document(cls, document: dict[str, str]) -> "Tenant":
        required_fields = ["tenant_slug", "owner_user_id", "visibility", "created_at"]
        missing_fields = [field for field in required_fields if field not in document]
        if missing_fields:
            missing_label = ", ".join(missing_fields)
            raise ValueError(f"Tenant document missing required fields: {missing_label}")

        return cls(
            tenant_slug=cls._normalize_tenant_slug(str(document["tenant_slug"])),
            owner_user_id=cls._normalize_owner_user_id(str(document["owner_user_id"])),
            visibility=cls._normalize_visibility(str(document["visibility"])),
            created_at=str(document["created_at"]),
        )

    def to_document(self) -> dict[str, str]:
        return {
            "tenant_slug": self.tenant_slug,
            "owner_user_id": self.owner_user_id,
            "visibility": self.visibility,
            "created_at": self.created_at,
        }

    @staticmethod
    def _normalize_tenant_slug(tenant_slug: str) -> str:
        if not isinstance(tenant_slug, str) or not tenant_slug.strip():
            raise ValueError("Tenant slug must be a non-empty string.")

        normalized_slug = tenant_slug.strip()
        if not TENANT_SLUG_PATTERN.fullmatch(normalized_slug):
            raise ValueError(
                "Invalid tenant slug. Expected lowercase alphanumeric plus hyphens and starting with a letter."
            )
        return normalized_slug

    @staticmethod
    def _normalize_owner_user_id(owner_user_id: str) -> str:
        if not isinstance(owner_user_id, str) or not owner_user_id.strip():
            raise ValueError("Owner user id must be a non-empty string.")
        return owner_user_id.strip()

    @staticmethod
    def _normalize_visibility(visibility: str) -> Visibility:
        if visibility not in {"public", "private"}:
            raise ValueError("Visibility must be either 'public' or 'private'.")
        return visibility  # type: ignore[return-value]
