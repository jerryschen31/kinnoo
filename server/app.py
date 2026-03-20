"""FastAPI server scaffold for remote registry API."""

from __future__ import annotations

import os
from typing import Any

from server.auth.token import SigningKey, TokenService
from server.config import ServerConfig
from server.metadata.manager import MetadataManager
from server.routes.agents import create_agents_router
from server.routes.publish import create_publish_router
from server.storage import build_storage_backend_from_config


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
    app.state.config = resolved_config
    app.state.storage_backend = storage_backend
    app.state.token_service = token_service
    app.state.metadata_manager = metadata_manager

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

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
        )
    )

    return app
