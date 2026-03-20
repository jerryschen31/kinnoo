"""FastAPI server scaffold for remote registry API."""

from __future__ import annotations

from typing import Any

from server.config import ServerConfig
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

    app = FastAPI(title="kinnoo-registry-server")
    app.state.config = resolved_config
    app.state.storage_backend = storage_backend

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
