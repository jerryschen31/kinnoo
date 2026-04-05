"""Framework-agnostic endpoint handlers for auth and admin API routes."""

from __future__ import annotations

from typing import Any

from server.auth.middleware import authenticate_request
from server.auth.token import TokenService
from server.storage.tenant_store import TenantStore
from server.storage.user_store import UserStore


def post_auth_token(
    *,
    payload: dict[str, Any],
    token_service: TokenService,
    user_store: UserStore,
) -> tuple[int, dict[str, Any]]:
    """Handle POST /api/auth/token request payload."""
    username = payload.get("username")
    password = payload.get("password")
    tenant_slug = payload.get("tenant_slug", "global")

    if not isinstance(username, str) or not username.strip():
        return 400, {"error": "username is required"}
    if not isinstance(password, str) or not password:
        return 400, {"error": "password is required"}
    if not isinstance(tenant_slug, str) or not tenant_slug.strip():
        return 400, {"error": "tenant_slug must be a non-empty string"}

    try:
        token = token_service.issue_token_for_credentials(
            username=username,
            plaintext_password=password,
            user_store=user_store,
            tenant_slug=tenant_slug,
        )
    except PermissionError as error:
        message = str(error)
        if message.startswith("423 account_locked"):
            retry_after = 900
            if "retry_after=" in message:
                try:
                    retry_after = int(message.rsplit("retry_after=", 1)[1])
                except ValueError:
                    retry_after = 900
            return 423, {"error": "account_locked", "retry_after": retry_after}
        return 401, {"error": "invalid username or password"}

    return 200, {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": token_service.ttl_minutes * 60,
    }


def post_admin_create_user(
    *,
    authorization_header: str | None,
    payload: dict[str, Any],
    token_service: TokenService,
    user_store: UserStore,
) -> tuple[int, dict[str, Any]]:
    """Handle POST /api/admin/users request payload."""
    try:
        authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:admin",
            token_service=token_service,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    username = payload.get("username")
    password = payload.get("password")
    role = payload.get("role", "user")

    if not isinstance(username, str) or not username.strip():
        return 400, {"error": "username is required"}
    if not isinstance(password, str) or not password:
        return 400, {"error": "password is required"}
    if role not in {"admin", "user"}:
        return 400, {"error": "role must be either 'admin' or 'user'"}

    try:
        created = user_store.create_user(
            username=username,
            plaintext_password=password,
            role=role,
        )
    except ValueError as error:
        return 409, {"error": str(error)}

    return 201, {
        "id": created.id,
        "username": created.username,
        "role": created.role,
        "force_password_change": created.force_password_change,
        "created_at": created.created_at,
        "updated_at": created.updated_at,
    }


def post_admin_create_tenant(
    *,
    authorization_header: str | None,
    payload: dict[str, Any],
    token_service: TokenService,
    user_store: UserStore,
    tenant_store: TenantStore,
) -> tuple[int, dict[str, Any]]:
    """Handle POST /api/admin/tenants request payload."""
    try:
        claims = authenticate_request(
            authorization_header=authorization_header,
            required_scope="registry:admin",
            token_service=token_service,
        )
    except PermissionError as error:
        status = 403 if "403" in str(error) else 401
        return status, {"error": str(error)}

    actor = user_store.get_by_id(claims.sub)
    if actor is None:
        return 401, {"error": "401 unauthorized: actor user not found"}

    tenant_slug = payload.get("tenant_slug")
    owner_user_id = payload.get("owner_user_id")
    visibility = payload.get("visibility", "private")

    if not isinstance(tenant_slug, str) or not tenant_slug.strip():
        return 400, {"error": "tenant_slug is required"}
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
        return 400, {"error": "owner_user_id is required"}
    if visibility not in {"public", "private"}:
        return 400, {"error": "visibility must be either 'public' or 'private'"}

    try:
        created = tenant_store.create_tenant(
            tenant_slug=tenant_slug,
            owner_user_id=owner_user_id,
            created_by=actor,
            visibility=visibility,
        )
    except PermissionError as error:
        return 403, {"error": str(error)}
    except ValueError as error:
        return 409, {"error": str(error)}

    return 201, {
        "tenant_slug": created.tenant_slug,
        "owner_user_id": created.owner_user_id,
        "visibility": created.visibility,
        "created_at": created.created_at,
    }
