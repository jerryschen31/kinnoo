from __future__ import annotations

from server.storage.tenant_store import TenantStore
from server.storage.user_store import UserStore


def test_tenant_slug_management(tmp_path):
    store_root = tmp_path / "registry-store"
    user_store = UserStore(store_root)
    tenant_store = TenantStore(store_root)

    admin_user = user_store.create_user(
        username="admin-user",
        plaintext_password="admin-pass",
        role="admin",
    )
    non_admin_user = user_store.create_user(
        username="regular-user",
        plaintext_password="user-pass",
        role="user",
    )

    created = tenant_store.create_tenant(
        tenant_slug="tenant-alpha-1",
        owner_user_id=admin_user.id,
        created_by=admin_user,
        visibility="private",
    )
    assert created.tenant_slug == "tenant-alpha-1"

    try:
        tenant_store.create_tenant(
            tenant_slug="tenant-alpha-1",
            owner_user_id=admin_user.id,
            created_by=admin_user,
            visibility="public",
        )
        raise AssertionError("Expected duplicate tenant slug rejection.")
    except ValueError as error:
        assert "already exists" in str(error)

    try:
        tenant_store.create_tenant(
            tenant_slug="Tenant!Invalid",
            owner_user_id=admin_user.id,
            created_by=admin_user,
            visibility="public",
        )
        raise AssertionError("Expected invalid tenant slug rejection.")
    except ValueError as error:
        assert "Invalid tenant slug" in str(error)

    try:
        tenant_store.create_tenant(
            tenant_slug="tenant-non-admin",
            owner_user_id=non_admin_user.id,
            created_by=non_admin_user,
            visibility="private",
        )
        raise AssertionError("Expected non-admin tenant creation rejection.")
    except PermissionError as error:
        assert "403" in str(error)
