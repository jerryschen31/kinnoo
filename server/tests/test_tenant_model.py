from __future__ import annotations

from server.api.endpoints import post_admin_create_tenant, post_admin_create_user
from server.auth.token import SigningKey, TokenService
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

    token_service = TokenService(
        issuer="kinnoo-registry",
        current_signing_key=SigningKey(kid="k1", secret="current-secret"),
        ttl_minutes=60,
    )
    admin_token = token_service.issue_token_for_credentials(
        username="admin-user",
        plaintext_password="admin-pass",
        user_store=user_store,
        tenant_slug="tenant-alpha-1",
    )
    user_token = token_service.issue_token_for_credentials(
        username="regular-user",
        plaintext_password="user-pass",
        user_store=user_store,
        tenant_slug="tenant-alpha-1",
    )

    user_status, user_response = post_admin_create_user(
        authorization_header=f"Bearer {admin_token}",
        payload={
            "username": "created-by-admin",
            "password": "created-pass",
            "role": "user",
        },
        token_service=token_service,
        user_store=user_store,
    )
    assert user_status == 201
    assert user_response["username"] == "created-by-admin"
    assert user_response["role"] == "user"

    non_admin_user_status, non_admin_user_response = post_admin_create_user(
        authorization_header=f"Bearer {user_token}",
        payload={
            "username": "should-not-create",
            "password": "created-pass",
            "role": "user",
        },
        token_service=token_service,
        user_store=user_store,
    )
    assert non_admin_user_status == 403
    assert "missing required scope" in non_admin_user_response["error"]

    tenant_status, tenant_response = post_admin_create_tenant(
        authorization_header=f"Bearer {admin_token}",
        payload={
            "tenant_slug": "tenant-admin-created",
            "owner_user_id": admin_user.id,
            "visibility": "public",
        },
        token_service=token_service,
        user_store=user_store,
        tenant_store=tenant_store,
    )
    assert tenant_status == 201
    assert tenant_response["tenant_slug"] == "tenant-admin-created"

    non_admin_tenant_status, non_admin_tenant_response = post_admin_create_tenant(
        authorization_header=f"Bearer {user_token}",
        payload={
            "tenant_slug": "tenant-user-created",
            "owner_user_id": non_admin_user.id,
            "visibility": "private",
        },
        token_service=token_service,
        user_store=user_store,
        tenant_store=tenant_store,
    )
    assert non_admin_tenant_status == 403
    assert "missing required scope" in non_admin_tenant_response["error"]
