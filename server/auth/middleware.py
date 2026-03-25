"""Auth middleware helpers for bearer token validation and scope enforcement."""

from __future__ import annotations

from server.auth.session import SessionService
from server.auth.token import TokenClaims, TokenService, TokenValidationError
from server.storage.user_store import UserStore


def authenticate_request(
    *,
    authorization_header: str | None,
    required_scope: str,
    token_service: TokenService,
) -> TokenClaims:
    if not authorization_header:
        raise PermissionError("401 unauthorized: missing bearer token")

    parts = authorization_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise PermissionError("401 unauthorized: malformed bearer token")

    token = parts[1].strip()
    try:
        claims = token_service.validate_token(token)
    except TokenValidationError as error:
        raise PermissionError(str(error)) from error

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
