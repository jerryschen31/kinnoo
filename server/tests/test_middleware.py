from __future__ import annotations

from server.middleware import InMemoryRateLimiter


def test_rate_limiter_window_behavior():
    limiter = InMemoryRateLimiter()

    allowed, _, _ = limiter.allow(
        path="/api/publish",
        client_id="127.0.0.1",
        requests=2,
        window_seconds=60,
        now=100.0,
    )
    assert allowed

    allowed, _, _ = limiter.allow(
        path="/api/publish",
        client_id="127.0.0.1",
        requests=2,
        window_seconds=60,
        now=101.0,
    )
    assert allowed

    allowed, _, _ = limiter.allow(
        path="/api/publish",
        client_id="127.0.0.1",
        requests=2,
        window_seconds=60,
        now=102.0,
    )
    assert not allowed

    # After 60s window passes from first event, requests should be allowed again.
    allowed, _, _ = limiter.allow(
        path="/api/publish",
        client_id="127.0.0.1",
        requests=2,
        window_seconds=60,
        now=161.0,
    )
    assert allowed
