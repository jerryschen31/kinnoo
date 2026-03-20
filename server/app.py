"""FastAPI server scaffold for remote registry API."""

from __future__ import annotations

import os
from typing import Any

from server.auth.token import SigningKey, TokenService
from server.config import ServerConfig
from server.metadata.manager import MetadataManager
from server.middleware import InMemoryRateLimiter, PathRateLimitMiddleware, RateLimitRule
from server.routes.agents import create_agents_router
from server.routes.auth import create_auth_router
from server.routes.download import create_download_router
from server.routes.publish import create_publish_router
from server.routes.search import create_search_router
from server.storage import build_storage_backend_from_config
from server.storage.user_store import UserStore


def create_app(*, config: ServerConfig | None = None) -> Any:
    """Create and return the server app instance."""
    try:
        from fastapi import FastAPI
    except ImportError as error:
        raise RuntimeError(
            "fastapi is required for server runtime. Install server/requirements.txt dependencies."
        ) from error

    resolved_config = config or ServerConfig.from_env()
    storage_backend = build_storage_backend_from_config(resolved_config)
    user_store = UserStore(resolved_config.local_storage_root / "auth")
    token_service = TokenService(
        issuer=os.getenv("REGISTRY_TOKEN_ISSUER", "kinnoo-registry"),
        current_signing_key=SigningKey(
            kid=os.getenv("REGISTRY_TOKEN_SIGNING_KID", "dev-k1"),
            secret=os.getenv("REGISTRY_TOKEN_SIGNING_SECRET", "dev-secret-change-me"),
        ),
        ttl_minutes=60,
    )
    metadata_manager = MetadataManager(storage=storage_backend)

    app = FastAPI(title="kinnoo-registry-server")
    app.add_middleware(
        PathRateLimitMiddleware,
        limiter=InMemoryRateLimiter(),
        rules={
            "/api/auth/token": RateLimitRule(requests_per_minute=20),
            "/api/publish": RateLimitRule(requests_per_minute=20),
        },
    )
    app.state.config = resolved_config
    app.state.storage_backend = storage_backend
    app.state.token_service = token_service
    app.state.metadata_manager = metadata_manager
    app.state.user_store = user_store

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(
        create_auth_router(
            token_service=token_service,
            user_store=user_store,
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
