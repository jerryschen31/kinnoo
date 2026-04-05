from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import _JsonLogFormatter, create_app
from server.config import ServerConfig


def _base_config(tmp_path: Path, *, env: str = "dev") -> ServerConfig:
    return ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=5,
        kinnoo_env=env,
        cors_origins=("https://dev.kinnoo.ai", "https://dev-api.kinnoo.ai"),
        app_version="0.30.0",
    )


def test_feature89_group1(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("REGISTRY_TOKEN_SIGNING_SECRET", "prod-token-signing-secret")
    monkeypatch.setenv("REGISTRY_SESSION_SIGNING_SECRET", "prod-session-signing-secret")
    monkeypatch.setenv("REGISTRY_REGISTER_TOKEN_SECRET", "prod-register-token-secret")
    monkeypatch.setenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET", "prod-password-reset-token-secret")

    config = _base_config(tmp_path, env="production")
    app = create_app(config=config)
    client = TestClient(app, base_url="https://testserver")

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok", "version": "0.30.0"}

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert ready.json()["checks"] == {"s3": True, "auth_store": True}

    not_allowed_preflight = client.options(
        "/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in {
        key.lower(): value for key, value in not_allowed_preflight.headers.items()
    }

    allowed_preflight = client.options(
        "/health",
        headers={
            "Origin": "https://dev.kinnoo.ai",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed_preflight.headers.get("access-control-allow-origin") == "https://dev.kinnoo.ai"

    monkeypatch.setattr("server.app._is_auth_store_ready", lambda _config: False)
    not_ready = client.get("/ready")
    assert not_ready.status_code == 503

    formatter = _JsonLogFormatter()
    payload = json.loads(
        formatter.format(
            logging.makeLogRecord(
                {"name": "feature89-test", "levelname": "INFO", "msg": "structured"}
            )
        )
    )
    assert payload["logger"] == "feature89-test"
    assert payload["level"] == "INFO"
    assert payload["message"] == "structured"


def test_feature89_group2(tmp_path: Path, monkeypatch) -> None:
    for name in (
        "REGISTRY_TOKEN_SIGNING_SECRET",
        "REGISTRY_SESSION_SIGNING_SECRET",
        "REGISTRY_REGISTER_TOKEN_SECRET",
        "REGISTRY_PASSWORD_RESET_TOKEN_SECRET",
    ):
        # Ensure missing-secret behavior is deterministic.
        monkeypatch.delenv(name, raising=False)

    try:
        create_app(config=_base_config(tmp_path, env="production"))
        assert False, "expected ValueError when production secrets are missing"
    except ValueError as error:
        assert "Missing required production secret" in str(error)

    monkeypatch.setenv("REGISTRY_TOKEN_SIGNING_SECRET", "prod-token-signing-secret")
    monkeypatch.setenv("REGISTRY_SESSION_SIGNING_SECRET", "prod-session-signing-secret")
    monkeypatch.setenv("REGISTRY_REGISTER_TOKEN_SECRET", "prod-register-token-secret")
    monkeypatch.setenv("REGISTRY_PASSWORD_RESET_TOKEN_SECRET", "prod-password-reset-token-secret")

    config = _base_config(tmp_path, env="production")
    app = create_app(config=config)
    uvicorn_config = app.state.uvicorn_config
    assert uvicorn_config["workers"] == 2
    assert uvicorn_config["timeout_seconds"] == 30
    assert uvicorn_config["graceful_shutdown"] is True
