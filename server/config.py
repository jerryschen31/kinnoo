"""Configuration helpers for registry server runtime."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import secrets
from typing import Literal


StorageBackendName = Literal["local", "mock", "s3"]
MetadataBackendName = Literal["json", "postgres"]

AUTH_ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "AUTH_ISSUER_URL": ("KINDE_ISSUER_URL",),
    "AUTH_JWKS_ENDPOINT_URL": ("JWKS_ENDPOINT_URL",),
    "AUTH_TOKEN_ENDPOINT": ("TOKEN_ENDPOINT",),
    "AUTH_AUTHORIZATION_ENDPOINT": ("AUTHORIZATION_ENDPOINT",),
    "AUTH_LOGOUT_ENDPOINT": ("LOGOUT_ENDPOINT",),
    "AUTH_USERINFO_ENDPOINT": ("USERINFO_ENDPOINT",),
    "AUTH_REVOCATION_ENDPOINT": ("REVOCATION_ENDPOINT",),
    "AUTH_AUDIENCE": ("KINDE_AUDIENCE",),
    "AUTH_WEB_CLIENT_ID": ("KINDE_WEB_CLIENT_ID",),
    "AUTH_WEB_CLIENT_SECRET": ("KINDE_WEB_CLIENT_SECRET",),
    "AUTH_CLI_CLIENT_ID": ("KINDE_CLI_CLIENT_ID",),
    "AUTH_WEB_REDIRECT_URI": ("KINDE_WEB_REDIRECT_URI",),
    "AUTH_LOGOUT_REDIRECT_URI": ("KINDE_LOGOUT_REDIRECT_URI",),
}

REQUIRED_AUTH_ENV_KEYS: tuple[str, ...] = (
    "AUTH_ISSUER_URL",
    "AUTH_JWKS_ENDPOINT_URL",
    "AUTH_TOKEN_ENDPOINT",
    "AUTH_AUTHORIZATION_ENDPOINT",
    "AUTH_LOGOUT_ENDPOINT",
    "AUTH_USERINFO_ENDPOINT",
    "AUTH_AUDIENCE",
    "AUTH_WEB_CLIENT_ID",
    "AUTH_WEB_CLIENT_SECRET",
    "AUTH_CLI_CLIENT_ID",
    "AUTH_WEB_REDIRECT_URI",
    "AUTH_LOGOUT_REDIRECT_URI",
)


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
    return value


@dataclass(frozen=True)
class ServerConfig:
    """Runtime configuration loaded from environment variables."""

    storage_backend: StorageBackendName
    local_storage_root: Path
    s3_bucket: str
    s3_region: str
    s3_endpoint_url: str | None
    s3_access_key_id: str | None
    s3_secret_access_key: str | None
    presign_ttl_seconds: int
    max_upload_mb: int
    kinnoo_env: Literal["dev", "production"] = "dev"
    cors_origins: tuple[str, ...] = ("*",)
    app_version: str = "0.30.0"
    uvicorn_workers: int = 1
    uvicorn_timeout_seconds: int = 30
    auth_rate_limit_requests: int = 5
    auth_rate_limit_window_seconds: int = 60
    publish_rate_limit_requests: int = 10
    publish_rate_limit_window_seconds: int = 3600
    search_rate_limit_requests: int = 60
    search_rate_limit_window_seconds: int = 60
    registry_admin_email: str | None = None
    registry_admin_password: str | None = None
    frontend_url: str = "http://localhost:3000"
    register_token_secret: str = ""
    password_reset_token_secret: str = ""
    metadata_backend: MetadataBackendName = "json"
    database_url: str = ""
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle_seconds: int = 1800

    @classmethod
    def from_env(cls) -> "ServerConfig":
        backend_raw = os.getenv("REGISTRY_STORAGE_BACKEND", "local").strip().lower()
        if backend_raw not in {"local", "mock", "s3"}:
            raise ValueError("REGISTRY_STORAGE_BACKEND must be one of: local, mock, s3")

        local_storage_root = Path(
            os.getenv("REGISTRY_LOCAL_STORAGE_ROOT", ".registry-storage")
        ).expanduser()

        env_raw = (os.getenv("KINNOO_ENV") or "dev").strip().lower()
        if env_raw not in {"dev", "production"}:
            raise ValueError("KINNOO_ENV must be one of: dev, production")

        cors_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
        if env_raw == "production":
            if not cors_origins_raw:
                # Restrictive defaults for beta deployment domains.
                cors_origins = ("https://dev.kinnoo.ai", "https://dev-api.kinnoo.ai")
            else:
                cors_origins = tuple(
                    origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()
                )
                if not cors_origins:
                    raise ValueError("CORS_ORIGINS must contain at least one origin in production")
        else:
            if not cors_origins_raw:
                cors_origins = ("*",)
            else:
                cors_origins = tuple(
                    origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()
                ) or ("*",)

        uvicorn_workers_default = 2 if env_raw == "production" else 1
        metadata_backend_raw = (os.getenv("REGISTRY_METADATA_BACKEND") or "json").strip().lower()
        if metadata_backend_raw not in {"json", "postgres"}:
            raise ValueError("REGISTRY_METADATA_BACKEND must be one of: json, postgres")

        return cls(
            storage_backend=backend_raw,
            local_storage_root=local_storage_root,
            s3_bucket=os.getenv("REGISTRY_S3_BUCKET", "kinnoo-registry-dev").strip(),
            s3_region=os.getenv("REGISTRY_S3_REGION", "us-east-1").strip(),
            s3_endpoint_url=os.getenv("REGISTRY_S3_ENDPOINT_URL") or None,
            s3_access_key_id=os.getenv("REGISTRY_S3_ACCESS_KEY_ID") or None,
            s3_secret_access_key=os.getenv("REGISTRY_S3_SECRET_ACCESS_KEY") or None,
            presign_ttl_seconds=_read_int_env("REGISTRY_PRESIGN_TTL_SECONDS", 900),
            max_upload_mb=_read_int_env("REGISTRY_MAX_UPLOAD_MB", 50),
            kinnoo_env=env_raw,
            cors_origins=cors_origins,
            app_version=(os.getenv("KINNOO_VERSION") or "0.30.0").strip() or "0.30.0",
            uvicorn_workers=_read_int_env("UVICORN_WORKERS", uvicorn_workers_default),
            uvicorn_timeout_seconds=_read_int_env("UVICORN_TIMEOUT_SECONDS", 30),
            auth_rate_limit_requests=_read_int_env("RATE_LIMIT_AUTH_REQUESTS", 5),
            auth_rate_limit_window_seconds=_read_int_env("RATE_LIMIT_AUTH_WINDOW_SECONDS", 60),
            publish_rate_limit_requests=_read_int_env("RATE_LIMIT_PUBLISH_REQUESTS", 10),
            publish_rate_limit_window_seconds=_read_int_env("RATE_LIMIT_PUBLISH_WINDOW_SECONDS", 3600),
            search_rate_limit_requests=_read_int_env("RATE_LIMIT_SEARCH_REQUESTS", 60),
            search_rate_limit_window_seconds=_read_int_env("RATE_LIMIT_SEARCH_WINDOW_SECONDS", 60),
            registry_admin_email=(os.getenv("REGISTRY_ADMIN_EMAIL") or "").strip() or None,
            registry_admin_password=os.getenv("REGISTRY_ADMIN_PASSWORD") or None,
            frontend_url=(os.getenv("FRONTEND_URL") or "http://localhost:3000").strip(),
            register_token_secret=(os.getenv("REGISTRY_REGISTER_TOKEN_SECRET") or "").strip()
            or secrets.token_urlsafe(32),
            password_reset_token_secret=(os.getenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET") or "").strip()
            or secrets.token_urlsafe(32),
            metadata_backend=metadata_backend_raw,
            database_url=(os.getenv("REGISTRY_DATABASE_URL") or "").strip(),
            db_pool_size=_read_int_env("REGISTRY_DB_POOL_SIZE", 10),
            db_max_overflow=_read_int_env("REGISTRY_DB_MAX_OVERFLOW", 20),
            db_pool_recycle_seconds=_read_int_env("REGISTRY_DB_POOL_RECYCLE_SECONDS", 1800),
        )


def resolve_auth_provider(*, env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    explicit = (source.get("AUTH_PROVIDER") or "").strip().lower()
    if explicit:
        return explicit

    resolved_contract = resolve_auth_env_contract(env=source)
    has_kinde_alias_signal = any(
        (source.get(key) or "").strip()
        for key in ("KINDE_ISSUER_URL", "KINDE_WEB_CLIENT_ID", "KINDE_CLI_CLIENT_ID")
    )
    kinnoo_env = (source.get("KINNOO_ENV") or "").strip().lower()
    should_infer_hosted_provider = kinnoo_env == "production" and has_kinde_alias_signal
    if should_infer_hosted_provider and all((resolved_contract.get(key) or "").strip() for key in REQUIRED_AUTH_ENV_KEYS):
        return "oidc_kinde"

    return "legacy"


def resolve_auth_env_contract(*, env: dict[str, str] | None = None) -> dict[str, str]:
    source = env if env is not None else os.environ
    resolved: dict[str, str] = {}
    for canonical_key, aliases in AUTH_ENV_ALIASES.items():
        value = (source.get(canonical_key) or "").strip()
        if value:
            resolved[canonical_key] = value
            continue
        for alias in aliases:
            alias_value = (source.get(alias) or "").strip()
            if alias_value:
                resolved[canonical_key] = alias_value
                break
        else:
            resolved[canonical_key] = ""
    return resolved


def is_legacy_auth_compatibility_enabled(*, env: dict[str, str] | None = None) -> bool:
    source = env if env is not None else os.environ
    raw = (source.get("AUTH_ENABLE_LEGACY_PATHS") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}
