"""Auth API routes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib
from typing import Any

from starlette.requests import Request

from server.api.endpoints import post_auth_token
from server.auth.password_policy import (
    validate_account_password_policy,
    validate_registration_email,
    validate_registration_password,
)
from server.auth.services import (
    build_password_reset_link,
    build_registration_verification_link,
    password_reset_generic_success_message,
    registration_generic_success_message,
)
from server.auth.middleware import authenticate_session_identity
from server.auth.session import SessionService
from server.auth.token import TokenService
from server.auth.tokens import PasswordResetTokenService, RegistrationTokenService
from server.models.user import PASSWORD_MANAGER, username_to_tenant_slug
from server.routes.errors import build_error_envelope, resolve_request_id
from server.services.email_service import EmailService
from server.storage.sqlite_auth_store import SQLiteAuthStore
from server.storage.user_store import UserStore


def create_auth_router(
    *,
    token_service: TokenService,
    user_store: UserStore,
    session_service: SessionService,
    registration_token_service: RegistrationTokenService,
    password_reset_token_service: PasswordResetTokenService,
    sqlite_auth_store: SQLiteAuthStore,
    frontend_url: str,
    email_service: EmailService,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")

    responses_module = importlib.import_module("fastapi.responses")
    JSONResponse = getattr(responses_module, "JSONResponse")

    router = APIRouter()

    @router.post("/api/auth/token")
    async def issue_token(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        status, response_payload = post_auth_token(
            payload=payload,
            token_service=token_service,
            user_store=user_store,
        )
        if status >= 400:
            envelope = build_error_envelope(
                status_code=status,
                message=str(response_payload.get("error", "request failed")),
                request_id=request_id,
            )
            retry_after = response_payload.get("retry_after")
            if isinstance(retry_after, int):
                envelope["error"]["retry_after"] = retry_after
            return JSONResponse(
                status_code=status,
                content=envelope,
            )

        return response_payload

    @router.post("/api/auth/register-request")
    async def register_request(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        email = str(payload.get("email", ""))
        validation_error = validate_registration_email(email)
        if validation_error is not None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message=validation_error,
                    request_id=request_id,
                ),
            )

        normalized_email = email.strip().lower()
        existing_user = user_store.get_by_username(normalized_email)
        if existing_user is None:
            token = registration_token_service.issue_token(email=normalized_email)
            verification_link = build_registration_verification_link(frontend_url=frontend_url, token=token)
            email_service.send_registration_verification(
                email=normalized_email,
                verification_link=verification_link,
            )

        return {"message": registration_generic_success_message()}

    @router.post("/api/auth/register-confirm")
    async def register_confirm(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        token = str(payload.get("token", "")).strip()
        password = str(payload.get("password", ""))

        token_payload = registration_token_service.verify_token(token=token)
        if token_payload is None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="invalid or expired registration token",
                    request_id=request_id,
                ),
            )

        token_hash = registration_token_service.hash_token(token=token)
        token_marked = sqlite_auth_store.mark_registration_token_consumed(token_hash=token_hash)
        if not token_marked:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="registration token already consumed",
                    request_id=request_id,
                ),
            )

        email = str(token_payload.get("email", "")).strip().lower()
        if not email:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="registration token missing email",
                    request_id=request_id,
                ),
            )

        password_error = validate_registration_password(password)
        if password_error is None:
            password_error = validate_account_password_policy(password, account_identifier=email)
        if password_error is not None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message=password_error,
                    request_id=request_id,
                ),
            )

        existing_user = user_store.get_by_username(email)
        if existing_user is not None:
            return JSONResponse(
                status_code=409,
                content=build_error_envelope(
                    status_code=409,
                    message="user already exists",
                    request_id=request_id,
                ),
            )

        user = user_store.create_user(
            username=email,
            plaintext_password=password,
            role="user",
        )

        sqlite_auth_store.upsert_local_identity(
            user_id=user.id,
            provider_user_id=email,
            provider_email=email,
        )
        base_slug = username_to_tenant_slug(email)
        reserved_tenant = sqlite_auth_store.reserve_tenant_slug(base_slug=base_slug, owner_user_id=user.id)

        session_record, session_cookie = session_service.create_session(user_id=user.id)
        response = JSONResponse(
            status_code=200,
            content={
                "message": "Account created successfully",
                "redirect_to": "/registry",
                "tenant_slug": reserved_tenant.tenant_slug,
                "username": user.username,
            },
        )
        response.set_cookie(
            key=session_cookie.name,
            value=session_cookie.value,
            max_age=session_cookie.max_age_seconds,
            httponly=session_cookie.http_only,
            secure=session_cookie.secure,
            samesite=session_cookie.same_site.lower(),
            path=session_cookie.path,
        )
        response.set_cookie(
            key="kinnoo_csrf",
            value=session_record.csrf_token,
            httponly=False,
            secure=True,
            samesite="lax",
            path="/",
        )
        return response

    @router.post("/api/auth/password-reset-request")
    async def password_reset_request(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        email = str(payload.get("email", ""))
        validation_error = validate_registration_email(email)
        if validation_error is not None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message=validation_error,
                    request_id=request_id,
                ),
            )

        normalized_email = email.strip().lower()
        existing_user = user_store.get_by_username(normalized_email)
        if existing_user is not None:
            token = password_reset_token_service.issue_token(email=normalized_email)
            reset_link = build_password_reset_link(frontend_url=frontend_url, token=token)
            email_service.send_password_reset(
                email=normalized_email,
                reset_link=reset_link,
            )

        return {"message": password_reset_generic_success_message()}

    @router.post("/api/auth/password-reset-confirm")
    async def password_reset_confirm(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)

        try:
            payload = await request.json()
        except Exception:
            payload = {}

        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="request body must be a JSON object",
                    request_id=request_id,
                ),
            )

        token = str(payload.get("token", "")).strip()
        new_password = str(payload.get("new_password", ""))

        token_payload = password_reset_token_service.verify_token(token=token)
        if token_payload is None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="invalid or expired password reset token",
                    request_id=request_id,
                ),
            )

        email = str(token_payload.get("email", "")).strip().lower()
        if not email:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="password reset token missing email",
                    request_id=request_id,
                ),
            )

        existing_user = user_store.get_by_username(email)
        if existing_user is None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="invalid or expired password reset token",
                    request_id=request_id,
                ),
            )

        password_error = validate_registration_password(new_password)
        if password_error is None:
            password_error = validate_account_password_policy(new_password, account_identifier=email)
        if password_error is not None:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message=password_error,
                    request_id=request_id,
                ),
            )

        token_hash = password_reset_token_service.hash_token(token=token)
        token_marked = sqlite_auth_store.mark_password_reset_token_consumed(token_hash=token_hash)
        if not token_marked:
            return JSONResponse(
                status_code=400,
                content=build_error_envelope(
                    status_code=400,
                    message="password reset token already consumed",
                    request_id=request_id,
                ),
            )

        updated_user = replace(
            existing_user,
            password_hash=PASSWORD_MANAGER.hash_password(new_password),
            updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )
        user_store.save(updated_user)

        session_service.invalidate_user_sessions(user_id=existing_user.id)

        return {
            "message": "Password reset successful",
            "redirect_to": "/login",
        }

    @router.get("/api/auth/me")
    async def auth_me(request: Request) -> dict[str, object]:
        request_id = resolve_request_id(request)
        cookie_value = request.cookies.get(session_service.cookie_name)

        try:
            user = authenticate_session_identity(
                cookie_value=cookie_value,
                session_service=session_service,
                user_store=user_store,
            )
        except PermissionError as error:
            return JSONResponse(
                status_code=401,
                content=build_error_envelope(
                    status_code=401,
                    message=str(error),
                    request_id=request_id,
                ),
            )

        return {
            "user_id": user.id,
            "tenant_slug": username_to_tenant_slug(user.username),
            "username": user.username,
        }

    return router
