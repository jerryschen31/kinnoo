from __future__ import annotations

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def test_auth_token_route_and_rate_limit(tmp_path):
    config = ServerConfig(
        storage_backend="local",
        local_storage_root=tmp_path / "storage",
        s3_bucket="kinnoo-registry-dev",
        s3_region="us-east-1",
        s3_endpoint_url=None,
        s3_access_key_id=None,
        s3_secret_access_key=None,
        presign_ttl_seconds=120,
        max_upload_mb=5,
    )

    app = create_app(config=config)
    client = TestClient(app)

    app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )

    auth_ok = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "admin-secret",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert auth_ok.status_code == 200
    ok_body = auth_ok.json()
    assert ok_body["token_type"] == "Bearer"
    assert isinstance(ok_body["access_token"], str)
    assert ok_body["expires_in"] > 0

    invalid = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert invalid.status_code == 401
    invalid_body = invalid.json()
    assert invalid_body["error"]["code"] == "unauthorized"
    assert invalid_body["error"]["message"]
    assert invalid_body["error"]["request_id"]

    # 20 requests/minute are allowed; the 21st request should be throttled.
    for _ in range(20):
        response = client.post(
            "/api/auth/token",
            json={
                "username": "admin",
                "password": "wrong-password",
                "tenant_slug": "tenant-alpha",
            },
        )
        assert response.status_code in {401, 429}

    final = client.post(
        "/api/auth/token",
        json={
            "username": "admin",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
    )
    assert final.status_code == 429
    throttled_body = final.json()
    assert throttled_body["error"]["code"] == "too_many_requests"
    assert throttled_body["error"]["message"] == "429 too many requests"
    assert throttled_body["error"]["request_id"]
