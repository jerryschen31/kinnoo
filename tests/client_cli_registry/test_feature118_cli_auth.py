from __future__ import annotations

import base64
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import parse as urllib_parse
from urllib import request as urllib_request

import pytest

from kinnoo.auth_command import (
    _tenant_slug_from_token,
    login_command,
    logout_command,
    refresh_registry_auth_if_needed,
)
from kinnoo.config import load_registry_config


def _jwt_with_tenant(tenant_slug: str) -> str:
    payload = {"tenant_slug": tenant_slug}
    payload_segment = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{payload_segment}.signature"


def _jwt_with_payload(payload: dict[str, str]) -> str:
    payload_segment = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{payload_segment}.signature"


class _OIDCTestServer:
    def __init__(self, *, access_token: str | None = None, userinfo_email: str = "alice@example.com") -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self.refresh_calls = 0
        self.access_token = access_token or _jwt_with_tenant("team-alpha")
        self.userinfo_email = userinfo_email

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        outer = self

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                params = urllib_parse.parse_qs(raw_body)

                if self.path == "/token":
                    grant_type = (params.get("grant_type") or [""])[0]
                    if grant_type == "authorization_code":
                        self._write_json(
                            200,
                            {
                                "access_token": outer.access_token,
                                "refresh_token": "refresh-1",
                                "expires_in": 30,
                                "token_type": "Bearer",
                            },
                        )
                        return
                    if grant_type == "refresh_token":
                        outer.refresh_calls += 1
                        self._write_json(
                            200,
                            {
                                "access_token": _jwt_with_tenant("team-alpha"),
                                "refresh_token": "refresh-2",
                                "expires_in": 3600,
                                "token_type": "Bearer",
                            },
                        )
                        return

                if self.path == "/revoke":
                    self._write_json(200, {"ok": True})
                    return

                self._write_json(404, {"error": "not found"})

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/userinfo":
                    self._write_json(
                        200,
                        {
                            "email": outer.userinfo_email,
                            "sub": "kinde-user-123",
                        },
                    )
                    return
                self._write_json(404, {"error": "not found"})

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                del format, args

            def _write_json(self, status_code: int, payload: dict[str, object]) -> None:
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return _Handler


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
@pytest.mark.client_cli_registry
def test_feature118_test710_hosted_login_persists_full_auth_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _OIDCTestServer()
    server.start()
    try:
        home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("KINDE_CLI_CLIENT_ID", "cli-client-id")
        monkeypatch.setenv("AUTHORIZATION_ENDPOINT", f"{server.base_url}/authorize")
        monkeypatch.setenv("TOKEN_ENDPOINT", f"{server.base_url}/token")
        monkeypatch.setenv("USERINFO_ENDPOINT", f"{server.base_url}/userinfo")
        monkeypatch.setenv("REVOCATION_ENDPOINT", f"{server.base_url}/revoke")
        monkeypatch.setenv("LOGOUT_ENDPOINT", f"{server.base_url}/logout")
        monkeypatch.setenv("KINDE_AUDIENCE", "https://api.kinnoo.local")
        monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.kinnoo.ai")

        def _fake_browser_open(url: str) -> bool:
            parsed = urllib_parse.urlparse(url)
            params = urllib_parse.parse_qs(parsed.query)
            scope = (params.get("scope") or [""])[0]
            assert "offline_access" not in scope
            assert scope == "openid profile email"
            redirect_uri = (params.get("redirect_uri") or [""])[0]
            state = (params.get("state") or [""])[0]
            urllib_request.urlopen(f"{redirect_uri}?code=abc123&state={state}", timeout=2).read()
            return True

        monkeypatch.setattr("kinnoo.auth_command.webbrowser.open", _fake_browser_open)

        result = login_command(email=None, password=None)
        assert result == 0

        config = load_registry_config()
        assert config.registry_token is not None
        assert config.refresh_token == "refresh-1"
        assert config.expires_at_epoch is not None
        assert config.tenant_slug == "alice"
        assert config.token_endpoint == f"{server.base_url}/token"
        assert config.oidc_client_id == "cli-client-id"
    finally:
        server.stop()


@pytest.mark.regression_integration
@pytest.mark.client_cli_logout
@pytest.mark.client_cli_registry
def test_feature118_test711_refresh_and_logout_no_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _OIDCTestServer()
    server.start()
    try:
        home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("TOKEN_ENDPOINT", f"{server.base_url}/token")
        monkeypatch.setenv("KINDE_CLI_CLIENT_ID", "cli-client-id")
        config_dir = home / ".kinnoo"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.yaml").write_text(
            "\n".join(
                [
                    "registry_url: 'https://registry.kinnoo.ai'",
                    f"token_endpoint: '{server.base_url}/token'",
                    "oidc_client_id: 'cli-client-id'",
                    "registry_token: 'old-token'",
                    "refresh_token: 'refresh-1'",
                    "tenant_slug: 'team-alpha'",
                    "expires_at_epoch: '1'",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        refreshed, refresh_error = refresh_registry_auth_if_needed()
        assert refresh_error is None
        assert refreshed.registry_token is not None
        assert refreshed.refresh_token == "refresh-2"
        assert server.refresh_calls == 1

        result = logout_command()
        assert result == 0

        second = logout_command()
        assert second == 0
    finally:
        server.stop()


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
def test_feature118_cli_tenant_slug_prefers_email(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    token = _jwt_with_payload({
        "email": "jerryschen@example.com",
        "org_code": "org_90bd1f158ac",
    })
    assert _tenant_slug_from_token(token) == "jerryschen"


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
def test_feature118_cli_tenant_slug_falls_back_to_org_code_when_email_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    token = _jwt_with_payload({
        "org_code": "org_90bd1f158ac",
    })
    assert _tenant_slug_from_token(token) == "org_90bd1f158ac"


@pytest.mark.regression_integration
@pytest.mark.client_cli_login
@pytest.mark.client_cli_registry
def test_feature118_hosted_login_prefers_userinfo_email_for_tenant_slug(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    token_without_email = _jwt_with_payload({
        "org_code": "org_90bd1f158ac",
        "sub": "kinde-user-123",
    })
    server = _OIDCTestServer(access_token=token_without_email, userinfo_email="jerryschen@example.com")
    server.start()
    try:
        home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("KINDE_CLI_CLIENT_ID", "cli-client-id")
        monkeypatch.setenv("AUTHORIZATION_ENDPOINT", f"{server.base_url}/authorize")
        monkeypatch.setenv("TOKEN_ENDPOINT", f"{server.base_url}/token")
        monkeypatch.setenv("USERINFO_ENDPOINT", f"{server.base_url}/userinfo")
        monkeypatch.setenv("KINDE_AUDIENCE", "https://api.kinnoo.local")
        monkeypatch.setenv("KINNOO_REGISTRY_URL", "https://registry.kinnoo.ai")

        def _fake_browser_open(url: str) -> bool:
            parsed = urllib_parse.urlparse(url)
            params = urllib_parse.parse_qs(parsed.query)
            redirect_uri = (params.get("redirect_uri") or [""])[0]
            state = (params.get("state") or [""])[0]
            urllib_request.urlopen(f"{redirect_uri}?code=abc123&state={state}", timeout=2).read()
            return True

        monkeypatch.setattr("kinnoo.auth_command.webbrowser.open", _fake_browser_open)

        result = login_command(email=None, password=None)
        assert result == 0
        config = load_registry_config()
        assert config.tenant_slug == "jerryschen"
    finally:
        server.stop()
