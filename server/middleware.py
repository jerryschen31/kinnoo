"""Auth context and rate-limiting middleware helpers for API routes."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import base64
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
    requests: int
    window_seconds: int
    key_by: str = "ip"

    def __init__(
        self,
        requests_per_minute: int | None = None,
        *,
        requests: int | None = None,
        window_seconds: int | None = None,
        key_by: str = "ip",
    ) -> None:
        if requests_per_minute is not None:
            object.__setattr__(self, "requests", int(requests_per_minute))
            object.__setattr__(self, "window_seconds", 60)
        else:
            resolved_requests = int(requests or 1)
            resolved_window = int(window_seconds or 60)
            object.__setattr__(self, "requests", resolved_requests)
            object.__setattr__(self, "window_seconds", resolved_window)
        object.__setattr__(self, "key_by", key_by)


class InMemoryRateLimiter:
    """Simple fixed-window limiter keyed by (path, client)."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], Deque[float]] = defaultdict(deque)

    def allow(
        self,
        *,
        path: str,
        client_id: str,
        requests: int,
        window_seconds: int,
        now: float | None = None,
    ) -> bool:
        timestamp = now if now is not None else time.time()
        key = (path, client_id)
        events = self._events[key]
        window_start = timestamp - float(window_seconds)

        while events and events[0] < window_start:
            events.popleft()

        if len(events) >= requests:
            return False

        events.append(timestamp)
        return True


class PathRateLimitMiddleware:
    """ASGI middleware applying per-path request limits."""

    # TODO(feature57): migrate rate limiter state to Redis/Upstash for distributed deployments.

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
        rule = self._match_rule(path)
        if rule is None:
            await self.app(scope, receive, send)
            return

        if rule.key_by == "tenant":
            client_host = _tenant_or_client_from_scope(scope)
        else:
            client_host = _client_id_from_scope(scope)
        allowed = self._limiter.allow(
            path=path,
            client_id=client_host,
            requests=rule.requests,
            window_seconds=rule.window_seconds,
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

    def _match_rule(self, path: str) -> RateLimitRule | None:
        best_prefix = ""
        best_rule = None
        for prefix, rule in self._rules.items():
            if path.startswith(prefix) and len(prefix) >= len(best_prefix):
                best_prefix = prefix
                best_rule = rule
        return best_rule


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


def _client_id_from_scope(scope) -> str:
    headers = scope.get("headers") or []
    for key, value in headers:
        if key == b"x-forwarded-for":
            try:
                forwarded = value.decode("utf-8")
            except UnicodeDecodeError:
                forwarded = ""
            candidate = forwarded.split(",", 1)[0].strip()
            if candidate:
                return candidate

    client = scope.get("client")
    return client[0] if client else "unknown"


def _tenant_or_client_from_scope(scope) -> str:
    headers = scope.get("headers") or []
    auth_value = ""
    for key, value in headers:
        if key == b"authorization":
            try:
                auth_value = value.decode("utf-8")
            except UnicodeDecodeError:
                auth_value = ""
            break

    if auth_value.lower().startswith("bearer "):
        token = auth_value.split(" ", 1)[1].strip()
        tenant_slug = _tenant_from_unverified_jwt(token)
        if tenant_slug:
            return f"tenant:{tenant_slug}"

    return _client_id_from_scope(scope)


def _tenant_from_unverified_jwt(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload_part = parts[1]
        padding = "=" * (-len(payload_part) % 4)
        payload_raw = base64.urlsafe_b64decode((payload_part + padding).encode("ascii"))
        payload = json.loads(payload_raw.decode("utf-8"))
    except Exception:
        return None

    tenant = payload.get("tenant_slug")
    if isinstance(tenant, str) and tenant.strip():
        return tenant.strip()
    return None
