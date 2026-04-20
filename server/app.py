"""FastAPI server scaffold for remote registry API."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import secrets
from typing import Any

from server.auth.oidc import KindeOIDCProvider, OIDCProviderConfig, OIDCTokenService
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
from server.services.email_console import ConsoleEmailService
from server.storage import build_storage_backend_from_config
from server.storage.sqlite_auth_store import SQLiteAuthStore
from server.storage.user_store import UserStore


class _JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _configure_production_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonLogFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def _validate_production_secrets() -> None:
    required_names = (
        "REGISTRY_TOKEN_SIGNING_SECRET",
        "REGISTRY_SESSION_SIGNING_SECRET",
        "REGISTRY_REGISTER_TOKEN_SECRET",
        "REGISTRY_PASSWORD_RESET_TOKEN_SECRET",
    )
    missing = [name for name in required_names if not (os.getenv(name) or "").strip()]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing required production secret(s): {joined}")


def _is_s3_ready(storage_backend: Any, config: ServerConfig) -> bool:
    if config.storage_backend != "s3":
        return True
    client = getattr(storage_backend, "_client", None)
    bucket = getattr(storage_backend, "_bucket", None)
    if client is None or not bucket:
        return False
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        return False
    return True


def _is_auth_store_ready(config: ServerConfig) -> bool:
    auth_root = config.local_storage_root / "auth"
    try:
        auth_root.mkdir(parents=True, exist_ok=True)
        probe_file = auth_root / ".readiness-check"
        probe_file.write_text("ok", encoding="utf-8")
        _ = probe_file.read_text(encoding="utf-8")
        probe_file.unlink(missing_ok=True)
    except OSError:
        return False
    return True


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
    if resolved_config.kinnoo_env == "production":
        _validate_production_secrets()
        _configure_production_logging()

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
    register_token_secret = resolved_config.register_token_secret or (
        os.getenv("REGISTRY_REGISTER_TOKEN_SECRET") or ""
    ).strip()
    if not register_token_secret:
        register_token_secret = secrets.token_urlsafe(32)

    password_reset_token_secret = resolved_config.password_reset_token_secret or (
        os.getenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET") or ""
    ).strip()
    if not password_reset_token_secret:
        password_reset_token_secret = secrets.token_urlsafe(32)

    auth_provider = (os.getenv("AUTH_PROVIDER") or "legacy").strip().lower()
    oidc_provider: KindeOIDCProvider | None = None
    token_service: Any
    if auth_provider in {"oidc", "oidc_kinde", "kinde"}:
        oidc_config = OIDCProviderConfig.from_env(env=os.environ, strict=True)
        assert oidc_config is not None
        oidc_provider = KindeOIDCProvider(config=oidc_config)
        token_service = OIDCTokenService(provider=oidc_provider)
    else:
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
        signing_secret=register_token_secret,
    )
    password_reset_token_service = PasswordResetTokenService(
        signing_secret=password_reset_token_secret,
    )
    sqlite_auth_store = SQLiteAuthStore(db_path=resolved_config.local_storage_root / "auth" / "auth.db")
    frontend_url = resolved_config.frontend_url
    email_log_sink: list[dict[str, str]] = []
    email_service = ConsoleEmailService(sink=email_log_sink)

    app = FastAPI(title="kinnoo-registry-server")
    try:
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as error:
        raise RuntimeError(
            "fastapi CORS middleware is unavailable. Install server dependencies."
        ) from error

    allow_origins = list(resolved_config.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
            "/api/auth": RateLimitRule(
                requests=resolved_config.auth_rate_limit_requests,
                window_seconds=resolved_config.auth_rate_limit_window_seconds,
                key_by="ip",
            ),
            "/api/publish": RateLimitRule(
                requests=resolved_config.publish_rate_limit_requests,
                window_seconds=resolved_config.publish_rate_limit_window_seconds,
                key_by="tenant",
            ),
            "/api/search": RateLimitRule(
                requests=resolved_config.search_rate_limit_requests,
                window_seconds=resolved_config.search_rate_limit_window_seconds,
                key_by="ip",
            ),
            "/api/download": RateLimitRule(
                requests=resolved_config.search_rate_limit_requests,
                window_seconds=resolved_config.search_rate_limit_window_seconds,
                key_by="ip",
            ),
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
    app.state.email_service = email_service
    app.state.templates = templates
    app.state.uvicorn_config = {
        "workers": max(2, resolved_config.uvicorn_workers)
        if resolved_config.kinnoo_env == "production"
        else resolved_config.uvicorn_workers,
        "timeout_seconds": resolved_config.uvicorn_timeout_seconds,
        "graceful_shutdown": True,
    }

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
        return {"status": "ok", "version": resolved_config.app_version}

    @app.get("/ready")
    def ready():
        s3_ready = _is_s3_ready(storage_backend, resolved_config)
        auth_ready = _is_auth_store_ready(resolved_config)
        if s3_ready and auth_ready:
            return {"status": "ready", "checks": {"s3": True, "auth_store": True}}

        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": {"s3": s3_ready, "auth_store": auth_ready},
            },
        )

    app.include_router(
        create_auth_router(
            token_service=token_service,
            user_store=user_store,
            session_service=session_service,
            registration_token_service=registration_token_service,
            password_reset_token_service=password_reset_token_service,
            sqlite_auth_store=sqlite_auth_store,
            frontend_url=frontend_url,
            email_service=email_service,
        )
    )
    app.include_router(
        create_web_auth_router(
            session_service=session_service,
            user_store=user_store,
            login_csrf_secret=os.getenv("REGISTRY_LOGIN_CSRF_SECRET", "dev-login-csrf-secret-change-me"),
            oidc_provider=oidc_provider,
            sqlite_auth_store=sqlite_auth_store,
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
            user_store=user_store,
            sqlite_auth_store=sqlite_auth_store,
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
