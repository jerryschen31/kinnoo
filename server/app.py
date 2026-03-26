"""FastAPI server scaffold for remote registry API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from server.auth.session import SessionService
from server.auth.token import SigningKey, TokenService
from server.auth.tokens import PasswordResetTokenService, RegistrationTokenService
from server.bootstrap import bootstrap_admin_from_env
from server.config import ServerConfig
from server.metadata.manager import MetadataManager
from server.middleware import InMemoryRateLimiter, PathRateLimitMiddleware, RateLimitRule
from server.routes.agents import create_agents_router
from server.routes.auth import create_auth_router
from server.routes.download import create_download_router
from server.routes.publish import create_publish_router
from server.routes.search import create_search_router
from server.routes.web_agents import create_web_agents_router
from server.routes.web_auth import create_web_auth_router
from server.storage import build_storage_backend_from_config
from server.storage.sqlite_auth_store import SQLiteAuthStore
from server.storage.user_store import UserStore


def create_app(*, config: ServerConfig | None = None) -> Any:
    """Create and return the server app instance."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import RedirectResponse
        from fastapi.staticfiles import StaticFiles
        from fastapi.templating import Jinja2Templates
    except ImportError as error:
        raise RuntimeError(
            "fastapi is required for server runtime. Install server/requirements.txt dependencies."
        ) from error

    resolved_config = config or ServerConfig.from_env()
    storage_backend = build_storage_backend_from_config(resolved_config)
    user_store = UserStore(resolved_config.local_storage_root / "auth")
    bootstrap_admin_from_env(
        store_root=resolved_config.local_storage_root / "auth",
        admin_email=resolved_config.registry_admin_email,
        admin_password=resolved_config.registry_admin_password,
    )
    session_service = SessionService(
        root=resolved_config.local_storage_root / "auth",
        signing_secret=os.getenv("REGISTRY_SESSION_SIGNING_SECRET", "dev-session-secret-change-me"),
        ttl_hours=8,
    )
    token_service = TokenService(
        issuer=os.getenv("REGISTRY_TOKEN_ISSUER", "kinnoo-registry"),
        current_signing_key=SigningKey(
            kid=os.getenv("REGISTRY_TOKEN_SIGNING_KID", "dev-k1"),
            secret=os.getenv("REGISTRY_TOKEN_SIGNING_SECRET", "dev-secret-change-me"),
        ),
        ttl_minutes=60,
    )
    metadata_manager = MetadataManager(storage=storage_backend)
    registration_token_service = RegistrationTokenService(
        signing_secret=os.getenv("REGISTRY_REGISTER_TOKEN_SECRET", "dev-register-token-secret-change-me"),
    )
    password_reset_token_service = PasswordResetTokenService(
        signing_secret=os.getenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET", "dev-password-reset-token-secret-change-me"),
    )
    sqlite_auth_store = SQLiteAuthStore(db_path=resolved_config.local_storage_root / "auth" / "auth.db")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    email_log_sink: list[dict[str, str]] = []

    app = FastAPI(title="kinnoo-registry-server")
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).parent / "templates" / "static")),
        name="static",
    )
    app.add_middleware(
        PathRateLimitMiddleware,
        limiter=InMemoryRateLimiter(),
        rules={
            "/api/auth/token": RateLimitRule(requests_per_minute=20),
            "/api/auth/register-request": RateLimitRule(requests_per_minute=5),
            "/api/auth/password-reset-request": RateLimitRule(requests_per_minute=5),
            "/api/publish": RateLimitRule(requests_per_minute=20),
        },
    )
    app.state.config = resolved_config
    app.state.storage_backend = storage_backend
    app.state.token_service = token_service
    app.state.metadata_manager = metadata_manager
    app.state.user_store = user_store
    app.state.session_service = session_service
    app.state.registration_token_service = registration_token_service
    app.state.password_reset_token_service = password_reset_token_service
    app.state.sqlite_auth_store = sqlite_auth_store
    app.state.frontend_url = frontend_url
    app.state.email_log_sink = email_log_sink
    app.state.templates = templates

    @app.middleware("http")
    async def require_web_session(request, call_next):
        path = request.url.path
        protected_prefixes = ("/agents", "/search")
        if not path.startswith(protected_prefixes):
            return await call_next(request)

        cookie_value = request.cookies.get(session_service.cookie_name)
        try:
            record = session_service.validate_session_cookie(cookie_value=cookie_value)
        except PermissionError:
            return RedirectResponse(url="/login", status_code=307)

        request.state.session = record
        return await call_next(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(
        create_auth_router(
            token_service=token_service,
            user_store=user_store,
            session_service=session_service,
            registration_token_service=registration_token_service,
            password_reset_token_service=password_reset_token_service,
            sqlite_auth_store=sqlite_auth_store,
            frontend_url=frontend_url,
            email_log_sink=email_log_sink,
        )
    )
    app.include_router(
        create_web_auth_router(
            session_service=session_service,
            user_store=user_store,
            login_csrf_secret=os.getenv("REGISTRY_LOGIN_CSRF_SECRET", "dev-login-csrf-secret-change-me"),
        )
    )
    app.include_router(
        create_web_agents_router(
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
        )
    )

    app.include_router(
        create_publish_router(
            token_service=token_service,
            storage_backend=storage_backend,
            metadata_manager=metadata_manager,
            max_upload_mb=resolved_config.max_upload_mb,
        )
    )
    app.include_router(
        create_agents_router(
            token_service=token_service,
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
        )
    )
    app.include_router(
        create_download_router(
            token_service=token_service,
            metadata_manager=metadata_manager,
            storage_backend=storage_backend,
            presign_ttl_seconds=resolved_config.presign_ttl_seconds,
        )
    )
    app.include_router(
        create_search_router(
            token_service=token_service,
            metadata_manager=metadata_manager,
        )
    )

    return app
