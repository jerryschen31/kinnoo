from __future__ import annotations

from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.routes.web_auth import create_web_auth_router


def _build_client(session_service: Mock, oidc_provider: Mock) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_web_auth_router(
            session_service=session_service,
            user_store=Mock(),
            login_csrf_secret="dev-login-csrf-secret-change-me",
            oidc_provider=oidc_provider,
        )
    )
    return TestClient(app)


def test_oidc_logout_rejects_get_requests() -> None:
    session_service = Mock()
    session_service.cookie_name = "kinnoo_session"
    oidc_provider = Mock()
    oidc_provider.build_logout_url.return_value = "https://issuer.example.com/logout"

    client = _build_client(session_service, oidc_provider)

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 405


def test_oidc_logout_requires_csrf_validation() -> None:
    session_service = Mock()
    session_service.cookie_name = "kinnoo_session"
    session_service.validate_post_request.side_effect = PermissionError("forbidden")
    oidc_provider = Mock()
    oidc_provider.build_logout_url.return_value = "https://issuer.example.com/logout"

    client = _build_client(session_service, oidc_provider)
    client.cookies.set("kinnoo_session", "signed-session-cookie")

    response = client.post(
        "/logout",
        data={},
        follow_redirects=False,
    )
    assert response.status_code == 403
    assert response.text == "forbidden"
    session_service.logout.assert_not_called()


def test_oidc_logout_uses_post_csrf_then_redirects_to_provider_logout() -> None:
    session_service = Mock()
    session_service.cookie_name = "kinnoo_session"
    oidc_provider = Mock()
    oidc_provider.build_logout_url.return_value = "https://issuer.example.com/logout"

    client = _build_client(session_service, oidc_provider)
    client.cookies.set("kinnoo_session", "signed-session-cookie")

    response = client.post(
        "/logout",
        data={"csrf_token": "csrf-123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "https://issuer.example.com/logout"
    session_service.validate_post_request.assert_called_once_with(
        cookie_value="signed-session-cookie",
        csrf_token="csrf-123",
    )
    session_service.logout.assert_called_once_with(cookie_value="signed-session-cookie")
