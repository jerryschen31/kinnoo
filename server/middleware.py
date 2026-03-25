"""Auth context and rate-limiting middleware helpers for API routes."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
import time
from typing import Deque
import uuid

from server.auth.middleware import authenticate_request
from server.auth.token import TokenClaims, TokenService


def validate_and_inject_user_context(
    *,
    request,
    authorization_header: str | None,
    token_service: TokenService,
    required_scope: str,
    session_cookie_value: str | None = None,
    session_service=None,
    user_store=None,
) -> TokenClaims:
    claims = authenticate_request(
        authorization_header=authorization_header,
        required_scope=required_scope,
        token_service=token_service,
        session_cookie_value=session_cookie_value,
        session_service=session_service,
        user_store=user_store,
    )
    request.state.user_claims = claims
    return claims


@dataclass(frozen=True)
class RateLimitRule:
    requests_per_minute: int


class InMemoryRateLimiter:
    """Simple fixed-window limiter keyed by (path, client)."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], Deque[float]] = defaultdict(deque)

    def allow(self, *, path: str, client_id: str, requests_per_minute: int, now: float | None = None) -> bool:
        timestamp = now if now is not None else time.time()
        key = (path, client_id)
        events = self._events[key]
        window_start = timestamp - 60.0

        while events and events[0] < window_start:
            events.popleft()

        if len(events) >= requests_per_minute:
            return False

        events.append(timestamp)
        return True


class PathRateLimitMiddleware:
    """ASGI middleware applying per-path request limits."""

    def __init__(
        self,
        app,
        *,
        limiter: InMemoryRateLimiter,
        rules: dict[str, RateLimitRule],
    ) -> None:
        self.app = app
        self._limiter = limiter
        self._rules = rules

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        rule = self._rules.get(path)
        if rule is None:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        client_host = client[0] if client else "unknown"
        allowed = self._limiter.allow(
            path=path,
            client_id=client_host,
            requests_per_minute=rule.requests_per_minute,
        )
        if allowed:
            await self.app(scope, receive, send)
            return

        request_id = _request_id_from_scope(scope)
        body = json.dumps(
            {
                "error": {
                    "code": "too_many_requests",
                    "message": "429 too many requests",
                    "request_id": request_id,
                }
            }
        ).encode("utf-8")
        headers = [(b"content-type", b"application/json")]
        await send({"type": "http.response.start", "status": 429, "headers": headers})
        await send({"type": "http.response.body", "body": body})


def _request_id_from_scope(scope) -> str:
    headers = scope.get("headers") or []
    for key, value in headers:
        if key == b"x-request-id":
            try:
                decoded = value.decode("utf-8").strip()
            except UnicodeDecodeError:
                decoded = ""
            if decoded:
                return decoded
    return uuid.uuid4().hex
