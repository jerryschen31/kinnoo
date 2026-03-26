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

from server.auth.session import SessionService
from server.models.user import PASSWORD_MANAGER
from server.storage.user_store import UserStore


SESSION_CSRF_COOKIE = "kinnoo_csrf"


def create_web_auth_router(
    *,
    session_service: SessionService,
    user_store: UserStore,
    login_csrf_secret: str,
) -> Any:
    fastapi_module = importlib.import_module("fastapi")
    APIRouter = getattr(fastapi_module, "APIRouter")
    Form = getattr(fastapi_module, "Form")

    responses_module = importlib.import_module("fastapi.responses")
    HTMLResponse = getattr(responses_module, "HTMLResponse")
    RedirectResponse = getattr(responses_module, "RedirectResponse")

    router = APIRouter()

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
