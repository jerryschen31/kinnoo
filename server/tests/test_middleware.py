from __future__ import annotations

from server.middleware import InMemoryRateLimiter


def test_rate_limiter_window_behavior():
    limiter = InMemoryRateLimiter()

    assert limiter.allow(path="/api/publish", client_id="127.0.0.1", requests_per_minute=2, now=100.0)
    assert limiter.allow(path="/api/publish", client_id="127.0.0.1", requests_per_minute=2, now=101.0)
    assert not limiter.allow(path="/api/publish", client_id="127.0.0.1", requests_per_minute=2, now=102.0)

    # After 60s window passes from first event, requests should be allowed again.
    assert limiter.allow(path="/api/publish", client_id="127.0.0.1", requests_per_minute=2, now=161.0)
