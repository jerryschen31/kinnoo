"""Auth middleware helpers for bearer token validation and scope enforcement."""

from __future__ import annotations

from server.auth.session import SessionService
from server.auth.token import TokenClaims, TokenService, TokenValidationError
from server.models.user import username_to_tenant_slug
from server.storage.user_store import UserStore


def authenticate_request(
    *,
    authorization_header: str | None,
    required_scope: str,
    token_service: TokenService,
    session_cookie_value: str | None = None,
    session_service: SessionService | None = None,
    user_store: UserStore | None = None,
) -> TokenClaims:
    claims: TokenClaims

    if authorization_header:
        parts = authorization_header.strip().split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            raise PermissionError("401 unauthorized: malformed bearer token")

        token = parts[1].strip()
        try:
            claims = token_service.validate_token(token)
        except TokenValidationError as error:
            raise PermissionError(str(error)) from error
    else:
        if session_service is None or user_store is None:
            raise PermissionError("401 unauthorized: missing bearer token")

        record = session_service.validate_session_cookie(cookie_value=session_cookie_value)
        user = user_store.get_by_id(record.user_id)
        if user is None:
            raise PermissionError("401 unauthorized: actor user not found")

        scopes: tuple[str, ...]
        if user.role == "admin":
            scopes = ("registry:read", "registry:publish", "registry:admin")
        else:
            scopes = ("registry:read",)

        claims = TokenClaims(
            iss="session-cookie",
            sub=user.id,
            tenant_slug=username_to_tenant_slug(user.username),
            scopes=scopes,
            token_id=f"session:{record.session_id}",
            exp=record.expires_at_epoch,
            iat=record.created_at_epoch,
        )

    if required_scope not in claims.scopes:
        raise PermissionError(f"403 forbidden: missing required scope '{required_scope}'")

    return claims


def authenticate_session_identity(
    *,
    cookie_value: str | None,
    session_service: SessionService,
    user_store: UserStore,
):
    record = session_service.validate_session_cookie(cookie_value=cookie_value)
    user = user_store.get_by_id(record.user_id)
    if user is None:
        raise PermissionError("401 unauthorized: actor user not found")
    return user
