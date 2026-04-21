from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def _base_config(tmp_path) -> ServerConfig:
    return ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="test",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=900,
        max_upload_mb=50,
        metadata_backend="json",
        database_url="",
    )


def test_feature119_test726_health_and_outage_paths(tmp_path, postgres_database_url: str, postgres_available: bool) -> None:
    invalid = _base_config(tmp_path)
    invalid = ServerConfig(**{**invalid.__dict__, "metadata_backend": "postgres", "database_url": "postgresql+psycopg://invalid:invalid@127.0.0.1:6543/missing"})
    with pytest.raises(Exception):
        create_app(config=invalid)

    if not postgres_available:
        pytest.skip("Postgres is not available")

    valid = _base_config(tmp_path)
    valid = ServerConfig(**{**valid.__dict__, "metadata_backend": "postgres", "database_url": postgres_database_url})
    app = create_app(config=valid)
    with TestClient(app) as client:
        ready_response = client.get("/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["checks"]["db"] is True
