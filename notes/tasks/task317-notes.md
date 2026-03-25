# Task317 Notes - Forwarded IP Rate-Limiter Compatibility

## Summary
- Updated `server/middleware.py` rate-limiter client-id derivation to prefer `X-Forwarded-For` when present.
- Added explicit migration TODO in rate-limiter middleware for Redis/Upstash-backed distributed limiting.
- Kept InMemoryRateLimiter as active development behavior.
- Added forwarding contract note in `web/next.config.ts` comments.
- Added `test_feature57_forwarded_ip_rate_limit_path` in `tests/test_registry.py` to verify:
  - forwarded IP drives limiter identity
  - migration TODO remains present in code

## Why this implementation
- Enables backend rate-limit behavior to track real client identity in proxied/BFF setups.
- Preserves current local/development behavior while documenting production-scale migration direction.

## Teaching Notes
- In proxied architectures, limiter keys should prioritize trusted forwarding headers before socket-origin IP.
- Always parse only the first `X-Forwarded-For` hop as client identity and preserve fallback behavior.
- Migration TODOs should be explicit and test-visible when they represent roadmap-critical operational constraints.

## Task-scoped regression
- Command: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests --testmon -k test_feature57_forwarded_ip_rate_limit_path`
- Result: pass (`1 passed`)
