from __future__ import annotations

from server.api.endpoints import post_auth_token
from server.auth.middleware import authenticate_request
from server.auth.token import SigningKey, TokenService
from server.storage.user_store import UserStore


def test_jwt_lifecycle(tmp_path):
    store_root = tmp_path / "registry-store"
    user_store = UserStore(store_root)
    admin_user = user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )
    user_store.create_user(
        username="reader",
        plaintext_password="reader-secret",
        role="user",
    )

    current_key = SigningKey(kid="k1", secret="current-secret")
    previous_key = SigningKey(kid="k0", secret="previous-secret")

    token_service = TokenService(
        issuer="kinnoo-registry",
        current_signing_key=current_key,
        previous_signing_key=previous_key,
        ttl_minutes=60,
    )

    status_code, token_response = post_auth_token(
        payload={
            "username": "admin",
            "password": "admin-secret",
            "tenant_slug": "tenant-alpha",
        },
        token_service=token_service,
        user_store=user_store,
    )
    assert status_code == 200
    assert token_response["token_type"] == "Bearer"
    assert token_response["expires_in"] == 60 * 60
    assert isinstance(token_response["access_token"], str)

    invalid_status_code, invalid_response = post_auth_token(
        payload={
            "username": "admin",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
        token_service=token_service,
        user_store=user_store,
    )
    assert invalid_status_code == 401
    assert "invalid username or password" in invalid_response["error"]

    admin_token = token_service.issue_token_for_credentials(
        username="admin",
        plaintext_password="admin-secret",
        user_store=user_store,
        tenant_slug="tenant-alpha",
    )
    admin_claims = token_service.validate_token(admin_token)
    assert admin_claims.iss == "kinnoo-registry"
    assert admin_claims.sub == admin_user.id
    assert admin_claims.tenant_slug == "tenant-alpha"
    assert "registry:admin" in admin_claims.scopes

    admin_default_tenant_token = token_service.issue_token_for_credentials(
        username="admin",
        plaintext_password="admin-secret",
        user_store=user_store,
    )
    admin_default_claims = token_service.validate_token(admin_default_tenant_token)
    assert admin_default_claims.tenant_slug == "admin"

    try:
        token_service.issue_token_for_credentials(
            username="admin",
            plaintext_password="wrong-password",
            user_store=user_store,
            tenant_slug="tenant-alpha",
        )
        raise AssertionError("Expected invalid credentials rejection.")
    except PermissionError as error:
        assert "401" in str(error)

    granted_claims = authenticate_request(
        authorization_header=f"Bearer {admin_token}",
        required_scope="registry:publish",
        token_service=token_service,
    )
    assert granted_claims.sub == admin_user.id

    expired_claims = admin_claims.to_dict()
    expired_claims["exp"] = expired_claims["iat"] - 1
    expired_token = token_service.issue_token(
        subject=expired_claims["sub"],
        tenant_slug=expired_claims["tenant_slug"],
        scopes=expired_claims["scopes"],
    )
    # Force expiration deterministically by validating far in the future.
    future_epoch = int(expired_claims["iat"]) + 10_000
    try:
        token_service.validate_token(expired_token, now_epoch=future_epoch)
        raise AssertionError("Expected expired token rejection.")
    except Exception as error:
        assert "expired" in str(error)

    reader_token = token_service.issue_token_for_credentials(
        username="reader",
        plaintext_password="reader-secret",
        user_store=user_store,
        tenant_slug="tenant-alpha",
    )
    try:
        authenticate_request(
            authorization_header=f"Bearer {reader_token}",
            required_scope="registry:publish",
            token_service=token_service,
        )
        raise AssertionError("Expected missing scope rejection.")
    except PermissionError as error:
        assert "403" in str(error)

    token_service.revoke_token_id(admin_claims.token_id)
    try:
        token_service.validate_token(admin_token)
        raise AssertionError("Expected revoked token rejection.")
    except Exception as error:
        assert "revoked" in str(error)

    old_service = TokenService(
        issuer="kinnoo-registry",
        current_signing_key=previous_key,
        previous_signing_key=None,
        ttl_minutes=60,
    )
    old_token = old_service.issue_token(
        subject=admin_user.id,
        tenant_slug="tenant-alpha",
        scopes=["registry:read"],
    )

    rotated_service = TokenService(
        issuer="kinnoo-registry",
        current_signing_key=current_key,
        previous_signing_key=previous_key,
        ttl_minutes=60,
    )
    rotated_claims = rotated_service.validate_token(old_token)
    assert rotated_claims.sub == admin_user.id
    assert "registry:read" in rotated_claims.scopes
