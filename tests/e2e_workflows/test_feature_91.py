from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path

from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig
from server.middleware import InMemoryRateLimiter, PathRateLimitMiddleware, RateLimitRule


def _b64url(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unverified_tenant_token(tenant_slug: str) -> str:
    return f"{_b64url({'alg': 'HS256', 'typ': 'JWT'})}.{_b64url({'tenant_slug': tenant_slug})}.sig"


def _start_event_from_middleware_call(
    middleware,
    *,
    path: str,
    headers: list[tuple[bytes, bytes]],
    client_host: str,
):
    events = []
    scope = {
        "type": "http",
        "path": path,
        "client": (client_host, 443),
        "headers": headers,
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        events.append(message)

    asyncio.run(middleware(scope, receive, send))
    for event in events:
        if event.get("type") == "http.response.start":
            return event
    return None


def _status_from_middleware_call(middleware, *, path: str, headers: list[tuple[bytes, bytes]], client_host: str) -> int:
    event = _start_event_from_middleware_call(
        middleware,
        path=path,
        headers=headers,
        client_host=client_host,
    )
    if event is None:
        return 0
    return int(event.get("status", 0))


def test_feature91_group1(tmp_path: Path) -> None:
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
        auth_rate_limit_requests=2,
        auth_rate_limit_window_seconds=60,
        publish_rate_limit_requests=2,
        publish_rate_limit_window_seconds=3600,
        search_rate_limit_requests=2,
        search_rate_limit_window_seconds=60,
    )

    app = create_app(config=config)
    client = TestClient(app, base_url="https://testserver")

    for _ in range(2):
        response = client.post("/api/auth/token", json={"username": "u", "password": "p"})
        assert response.status_code in {400, 401}
    blocked_auth = client.post("/api/auth/token", json={"username": "u", "password": "p"})
    assert blocked_auth.status_code == 429

    limiter = InMemoryRateLimiter()

    class _StubApp:
        async def __call__(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

    middleware = PathRateLimitMiddleware(
        _StubApp(),
        limiter=limiter,
        rules={
            "/api/publish": RateLimitRule(requests=2, window_seconds=3600, key_by="tenant"),
            "/api/search": RateLimitRule(requests=2, window_seconds=60, key_by="ip"),
        },
    )

    token = _unverified_tenant_token("tenant-alpha")
    for ip in ("198.51.100.10", "198.51.100.11"):
        status = _status_from_middleware_call(
            middleware,
            path="/api/publish",
            headers=[(b"authorization", f"Bearer {token}".encode("utf-8"))],
            client_host=ip,
        )
        assert status == 200

    blocked_publish = _status_from_middleware_call(
        middleware,
        path="/api/publish",
        headers=[(b"authorization", f"Bearer {token}".encode("utf-8"))],
        client_host="198.51.100.12",
    )
    assert blocked_publish == 429

    for _ in range(2):
        status = _status_from_middleware_call(
            middleware,
            path="/api/search",
            headers=[],
            client_host="203.0.113.99",
        )
        assert status == 200
    blocked_search = _status_from_middleware_call(
        middleware,
        path="/api/search",
        headers=[],
        client_host="203.0.113.99",
    )
    assert blocked_search == 429


def test_feature91_group2() -> None:
    limiter = InMemoryRateLimiter()

    class _StubApp:
        async def __call__(self, scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

    middleware = PathRateLimitMiddleware(
        _StubApp(),
        limiter=limiter,
        rules={"/api/auth": RateLimitRule(requests=1, window_seconds=60, key_by="ip")},
    )

    first = _start_event_from_middleware_call(
        middleware,
        path="/api/auth/token",
        headers=[(b"x-request-id", b"feature91")],
        client_host="127.0.0.1",
    )
    second = _start_event_from_middleware_call(
        middleware,
        path="/api/auth/token",
        headers=[(b"x-request-id", b"feature91")],
        client_host="127.0.0.1",
    )

    assert first is not None
    assert second is not None
    assert int(first["status"]) == 200
    assert int(second["status"]) == 429

    first_headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in first["headers"]}
    second_headers = {k.decode("utf-8").lower(): v.decode("utf-8") for k, v in second["headers"]}

    assert "x-ratelimit-limit" in first_headers
    assert "x-ratelimit-remaining" in first_headers
    assert "x-ratelimit-reset" in first_headers

    assert "x-ratelimit-limit" in second_headers
    assert "x-ratelimit-remaining" in second_headers
    assert "x-ratelimit-reset" in second_headers
    assert "retry-after" in second_headers
