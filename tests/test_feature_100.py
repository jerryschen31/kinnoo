from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


def _build_app(tmp_path: Path):
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
    client = TestClient(app, base_url="https://testserver")
    return app, client


def test_feature100_group1(tmp_path: Path) -> None:
    app, client = _build_app(tmp_path)
    app.state.user_store.create_user(
        username="locked-user@example.com",
        plaintext_password="correct-password-123",
        role="user",
    )

    for _ in range(4):
        response = client.post(
            "/api/auth/token",
            json={
                "username": "locked-user@example.com",
                "password": "wrong-password",
                "tenant_slug": "tenant-alpha",
            },
            headers={"x-forwarded-for": "198.51.100.10"},
        )
        assert response.status_code == 401

    lock_trigger = client.post(
        "/api/auth/token",
        json={
            "username": "locked-user@example.com",
            "password": "wrong-password",
            "tenant_slug": "tenant-alpha",
        },
        headers={"x-forwarded-for": "198.51.100.10"},
    )
    assert lock_trigger.status_code == 423
    error_payload = lock_trigger.json()["error"]
    assert error_payload["message"] == "account_locked"
    assert int(error_payload["retry_after"]) > 0

    locked = client.post(
        "/api/auth/token",
        json={
            "username": "locked-user@example.com",
            "password": "correct-password-123",
            "tenant_slug": "tenant-alpha",
        },
        headers={"x-forwarded-for": "198.51.100.11"},
    )
    assert locked.status_code == 423

    user = app.state.user_store.get_by_username("locked-user@example.com")
    assert user is not None
    expired_user = replace(
        user,
        locked_until=(datetime.now(timezone.utc) - timedelta(minutes=16)).isoformat().replace("+00:00", "Z"),
    )
    app.state.user_store.save(expired_user)

    unlocked = client.post(
        "/api/auth/token",
        json={
            "username": "locked-user@example.com",
            "password": "correct-password-123",
            "tenant_slug": "tenant-alpha",
        },
        headers={"x-forwarded-for": "198.51.100.12"},
    )
    assert unlocked.status_code == 200

    reset_user = app.state.user_store.get_by_username("locked-user@example.com")
    assert reset_user is not None
    assert reset_user.failed_login_attempts == 0
    assert reset_user.locked_until is None


def test_feature100_group2(tmp_path: Path) -> None:
    app, client = _build_app(tmp_path)
    _ = (app, client)


def test_feature100_group3(tmp_path: Path) -> None:
    app, client = _build_app(tmp_path)
    _ = (app, client)
