from __future__ import annotations

import re

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.routes.web_auth import SESSION_CSRF_COOKIE


def _extract_hidden_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    assert match is not None
    return match.group(1)


def test_login_flow(tmp_path):
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

    app.state.user_store.create_user(
        username="admin",
        plaintext_password="admin-secret",
        role="admin",
    )

    unauth_client = TestClient(app, base_url="https://testserver")
    redirect_response = unauth_client.get("/agents", follow_redirects=False)
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "/login"

    client = TestClient(app, base_url="https://testserver")

    login_page = client.get("/login")
    assert login_page.status_code == 200
    assert "<form" in login_page.text
    csrf_token = _extract_hidden_csrf_token(login_page.text)

    csrf_missing = client.post(
        "/login",
        data={"username": "admin", "password": "admin-secret"},
        follow_redirects=False,
    )
    assert csrf_missing.status_code == 403

    invalid_login = client.post(
        "/login",
        data={"username": "admin", "password": "wrong-password", "csrf_token": csrf_token},
        follow_redirects=False,
    )
    assert invalid_login.status_code == 401
    assert "Invalid username or password" in invalid_login.text

    valid_csrf_token = _extract_hidden_csrf_token(invalid_login.text)
    valid_login = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin-secret",
            "csrf_token": valid_csrf_token,
        },
        follow_redirects=False,
    )
    assert valid_login.status_code == 303
    assert valid_login.headers["location"] == "/agents"
    session_cookie = client.cookies.get(app.state.session_service.cookie_name)
    assert session_cookie
    csrf_cookie = client.cookies.get(SESSION_CSRF_COOKIE)
    assert csrf_cookie

    logout = client.post(
        "/logout",
        data={"csrf_token": csrf_cookie},
        follow_redirects=False,
    )
    assert logout.status_code == 303
    assert logout.headers["location"] == "/login"

    post_logout_redirect = client.get("/agents", follow_redirects=False)
    assert post_logout_redirect.status_code == 307
    assert post_logout_redirect.headers["location"] == "/login"
