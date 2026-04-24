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


# [agent] test used during UAT or migration, currently not used for regression
# def test_feature119_test726_health_and_outage_paths(tmp_path, postgres_database_url: str, postgres_available: bool) -> None:
#     ...
