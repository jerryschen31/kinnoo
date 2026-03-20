from __future__ import annotations

import json
from pathlib import Path
from urllib import request as urllib_request

from kinnoo.remote_client import RemoteRegistryClient


class _FakeHTTPResponse:
    def __init__(self, payload: object) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def test_remote_client_http_calls(monkeypatch, tmp_path: Path) -> None:
    captured_requests: list[urllib_request.Request] = []

    def fake_urlopen(request: urllib_request.Request, timeout: float = 0):
        captured_requests.append(request)

        if request.full_url.endswith("/api/publish"):
            return _FakeHTTPResponse({"ok": True, "request": "publish"})
        if "/download" in request.full_url:
            return _FakeHTTPResponse({"download_url": "https://example.test/file.kno"})
        if "/api/search" in request.full_url:
            return _FakeHTTPResponse({"items": [{"name": "demo"}]})
        if "/api/agents?tenant=" in request.full_url:
            return _FakeHTTPResponse({"items": [{"name": "demo", "version": "1.0.0"}]})

        return _FakeHTTPResponse({})

    monkeypatch.setattr(urllib_request, "urlopen", fake_urlopen)

    archive_path = tmp_path / "demo.kno"
    archive_path.write_text("archive-bytes", encoding="utf-8")

    client = RemoteRegistryClient(
        base_url="https://registry.example.test",
        token="secret-token",
        tenant_slug="acme",
    )

    publish_result = client.publish(name="demo", version="1.0.0", archive_path=archive_path)
    assert publish_result["ok"] is True

    resolve_result = client.resolve(name="demo", version="1.0.0")
    assert resolve_result["download_url"] == "https://example.test/file.kno"

    search_result = client.search(query="demo")
    assert search_result == [{"name": "demo"}]

    list_result = client.list_agents()
    assert list_result == [{"name": "demo", "version": "1.0.0"}]

    assert len(captured_requests) == 4

    publish_request = captured_requests[0]
    assert publish_request.get_method() == "POST"
    assert publish_request.full_url == "https://registry.example.test/api/publish"
    assert publish_request.get_header("Authorization") == "Bearer secret-token"
    publish_content_type = publish_request.get_header("Content-type") or ""
    assert "multipart/form-data" in publish_content_type
    publish_body = publish_request.data or b""
    assert b'name="archive"; filename="demo.kno"' in publish_body
    assert b"archive-bytes" in publish_body

    resolve_request = captured_requests[1]
    assert resolve_request.get_method() == "GET"
    assert resolve_request.full_url == "https://registry.example.test/api/agents/acme/demo/1.0.0/download"
    assert resolve_request.get_header("Authorization") == "Bearer secret-token"

    search_request = captured_requests[2]
    assert search_request.get_method() == "GET"
    assert search_request.full_url == "https://registry.example.test/api/search?q=demo"
    assert search_request.get_header("Authorization") == "Bearer secret-token"

    list_request = captured_requests[3]
    assert list_request.get_method() == "GET"
    assert list_request.full_url == "https://registry.example.test/api/agents?tenant=acme"
    assert list_request.get_header("Authorization") == "Bearer secret-token"
