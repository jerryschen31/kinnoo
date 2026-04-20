"""Web auth routes for login/logout using session cookies."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import hmac
import importlib
import secrets
from typing import Any

from starlette.requests import Request

from server.auth.oidc import KindeOIDCProvider
from server.auth.session import SessionService
from server.config import resolve_auth_provider
from server.models.user import PASSWORD_MANAGER, username_to_tenant_slug
from server.storage.sqlite_auth_store import SQLiteAuthStore
from server.storage.user_store import UserStore


SESSION_CSRF_COOKIE = "kinnoo_csrf"
OIDC_STATE_COOKIE = "kinnoo_oidc_state"


def create_web_auth_router(
    *,
    session_service: SessionService,
    user_store: UserStore,
    login_csrf_secret: str,
    oidc_provider: KindeOIDCProvider | None = None,
    sqlite_auth_store: SQLiteAuthStore | None = None,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Form = getattr(fastapi_module, "Form")

    responses_module = importlib.import_module("fastapi.responses")
    HTMLResponse = getattr(responses_module, "HTMLResponse")
    RedirectResponse = getattr(responses_module, "RedirectResponse")

    router = APIRouter()
    oidc_provider_name = resolve_auth_provider()
    if oidc_provider_name in {"", "legacy"}:
        oidc_provider_name = "oidc_kinde"

    if oidc_provider is not None:
        @router.get("/login")
        async def oidc_login_page() -> Any:
            state = secrets.token_urlsafe(32)
            login_url = oidc_provider.build_login_url(state=state)
            response = RedirectResponse(url=login_url, status_code=307)
            response.set_cookie(
                key=OIDC_STATE_COOKIE,
                value=state,
                httponly=True,
                secure=True,
                samesite="lax",
                path="/",
                max_age=10 * 60,
            )
            return response

        @router.get("/auth/callback")
        async def oidc_callback(request: Request, code: str = "", state: str = "", error: str = "") -> Any:
            expected_state = request.cookies.get(OIDC_STATE_COOKIE, "")
            if error:
                response = RedirectResponse(url="/login?error=auth_callback_error", status_code=303)
                response.delete_cookie(OIDC_STATE_COOKIE, path="/")
                return response

            if not code or not state or not expected_state or state != expected_state:
                response = RedirectResponse(url="/login?error=auth_state_invalid", status_code=303)
                response.delete_cookie(OIDC_STATE_COOKIE, path="/")
                return response

            try:
                token_payload = oidc_provider.exchange_code_for_tokens(code=code)
            except Exception:
                response = RedirectResponse(url="/login?error=auth_exchange_failed", status_code=303)
                response.delete_cookie(OIDC_STATE_COOKIE, path="/")
                return response

            access_token = token_payload.get("access_token")
            if not isinstance(access_token, str) or not access_token.strip():
                response = RedirectResponse(url="/login?error=auth_missing_token", status_code=303)
                response.delete_cookie(OIDC_STATE_COOKIE, path="/")
                return response

            try:
                userinfo = oidc_provider.fetch_userinfo(access_token=access_token.strip())
            except Exception:
                userinfo = {}

            email_raw = userinfo.get("email")
            sub_raw = userinfo.get("sub")
            provider_subject = sub_raw.strip() if isinstance(sub_raw, str) and sub_raw.strip() else ""
            if isinstance(email_raw, str) and email_raw.strip():
                username = email_raw.strip().lower()
            elif provider_subject:
                username = f"{provider_subject}@kinde.local"
            else:
                response = RedirectResponse(url="/login?error=auth_missing_profile", status_code=303)
                response.delete_cookie(OIDC_STATE_COOKIE, path="/")
                return response

            user = None
            if sqlite_auth_store is not None and provider_subject:
                identity_mapping = sqlite_auth_store.get_identity_mapping(
                    provider=oidc_provider_name,
                    provider_user_id=provider_subject,
                )
                if identity_mapping is not None:
                    user = user_store.get_by_id(identity_mapping.user_id)

            if user is None:
                user = user_store.get_by_username(username)
            if user is None:
                user = user_store.create_user(
                    username=username,
                    plaintext_password=secrets.token_urlsafe(32),
                    role="user",
                    force_password_change=False,
                )

            if sqlite_auth_store is not None:
                if provider_subject:
                    sqlite_auth_store.upsert_external_identity(
                        provider=oidc_provider_name,
                        provider_user_id=provider_subject,
                        user_id=user.id,
                        provider_email=(username if "@" in username else None),
                    )
                sqlite_auth_store.upsert_tenant_owner(
                    tenant_slug=username_to_tenant_slug(username),
                    owner_user_id=user.id,
                )

            session_record, session_cookie = session_service.create_session(user_id=user.id)
            response = RedirectResponse(url="/registry", status_code=303)
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
                key=SESSION_CSRF_COOKIE,
                value=session_record.csrf_token,
                httponly=False,
                secure=True,
                samesite="lax",
                path="/",
            )
            response.delete_cookie(OIDC_STATE_COOKIE, path="/")
            return response

        @router.post("/logout")
        async def oidc_logout(request: Request) -> Any:
            cookie_value = request.cookies.get(session_service.cookie_name)
            csrf_token = (await request.form()).get("csrf_token", "")
            try:
                session_service.validate_post_request(
                    cookie_value=cookie_value,
                    csrf_token=csrf_token,
                )
            except PermissionError:
                return HTMLResponse("forbidden", status_code=403)

            session_service.logout(cookie_value=cookie_value)

            response = RedirectResponse(url=oidc_provider.build_logout_url(), status_code=303)
            response.delete_cookie(session_service.cookie_name, path="/")
            response.delete_cookie(SESSION_CSRF_COOKIE, path="/")
            response.delete_cookie(OIDC_STATE_COOKIE, path="/")
            return response

        return router

    @router.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request) -> HTMLResponse:
        csrf_token = _issue_login_csrf_token(secret=login_csrf_secret)
        response = request.app.state.templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "csrf_token": csrf_token,
                "error_message": "",
            },
        )
        return response

    @router.post("/login")
    async def login_submit(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        csrf_token: str = Form(default=""),
    ) -> Any:
        if not _validate_login_csrf_token(token=csrf_token, secret=login_csrf_secret):
            return HTMLResponse("forbidden: invalid csrf token", status_code=403)

        user = user_store.get_by_username(username)
        if user is None or not user.verify_password(password):
            refreshed_csrf = _issue_login_csrf_token(secret=login_csrf_secret)
            response = request.app.state.templates.TemplateResponse(
                request=request,
                name="login.html",
                context={
                    "csrf_token": refreshed_csrf,
                    "error_message": "Invalid username or password",
                },
                status_code=401,
            )
            return response

        if PASSWORD_MANAGER.needs_rehash(user.password_hash):
            upgraded_user = replace(
                user,
                password_hash=PASSWORD_MANAGER.hash_password(password),
                updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
            user_store.save(upgraded_user)
            user = upgraded_user

        session_record, session_cookie = session_service.create_session(user_id=user.id)
        response = RedirectResponse(url="/agents", status_code=303)
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
            key=SESSION_CSRF_COOKIE,
            value=session_record.csrf_token,
            httponly=False,
            secure=True,
            samesite="lax",
            path="/",
        )
        return response

    @router.post("/logout")
    async def logout_submit(
        request: Request,
        csrf_token: str = Form(default=""),
    ) -> Any:
        cookie_value = request.cookies.get(session_service.cookie_name)
        try:
            session_service.validate_post_request(
                cookie_value=cookie_value,
                csrf_token=csrf_token,
            )
        except PermissionError:
            return HTMLResponse("forbidden", status_code=403)

        session_service.logout(cookie_value=cookie_value)

        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(session_service.cookie_name, path="/")
        response.delete_cookie(SESSION_CSRF_COOKIE, path="/")
        return response

    return router


def _issue_login_csrf_token(*, secret: str) -> str:
    nonce = secrets.token_urlsafe(24)
    signature = hmac.new(secret.encode("utf-8"), nonce.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{nonce}.{signature}"


def _validate_login_csrf_token(*, token: str, secret: str) -> bool:
    if not token:
        return False
    parts = token.split(".", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return False
    nonce, provided_signature = parts
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        nonce.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(provided_signature, expected_signature)
