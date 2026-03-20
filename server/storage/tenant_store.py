"""JSON-backed tenant persistence and authorization checks."""

from __future__ import annotations

import json
from pathlib import Path

from server.models.tenant import Tenant, Visibility
from server.models.user import User


class TenantStore:
    """Store tenant records as one-document-per-tenant JSON files."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._tenants_dir = self._root / "tenants"
        self._tenants_dir.mkdir(parents=True, exist_ok=True)

    def create_tenant(
        self,
        *,
        tenant_slug: str,
        owner_user_id: str,
        created_by: User,
        visibility: Visibility = "private",
    ) -> Tenant:
        if created_by.role != "admin":
            raise PermissionError("403 forbidden: only admin users can create tenants.")

        normalized_slug = Tenant._normalize_tenant_slug(tenant_slug)
        if self.get_by_slug(normalized_slug) is not None:
            raise ValueError(f"Tenant slug '{normalized_slug}' already exists.")

        tenant = Tenant.create(
            tenant_slug=normalized_slug,
            owner_user_id=owner_user_id,
            visibility=visibility,
        )
        self.save(tenant)
        return tenant

    def save(self, tenant: Tenant) -> None:
        tenant_path = self._tenants_dir / f"{tenant.tenant_slug}.json"
        tenant_path.write_text(json.dumps(tenant.to_document(), indent=2, sort_keys=True), encoding="utf-8")

    def get_by_slug(self, tenant_slug: str) -> Tenant | None:
        tenant_path = self._tenants_dir / f"{tenant_slug}.json"
        if not tenant_path.exists():
            return None
        return self._read_tenant(tenant_path)

    def list_tenants(self) -> list[Tenant]:
        tenants: list[Tenant] = []
        for path in sorted(self._tenants_dir.glob("*.json")):
            tenants.append(self._read_tenant(path))
        return tenants

    def _read_tenant(self, path: Path) -> Tenant:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Invalid tenant document at {path}: expected JSON object.")
        return Tenant.from_document(raw)
