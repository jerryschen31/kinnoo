# Task244 - feature29 search endpoint, auth context injection, and rate limiting

## Summary
- Added `server/routes/search.py` implementing `GET /api/search` with:
  - required `registry:read` token validation,
  - substring matching across agent slug and latest version description,
  - tenant visibility filtering (`private` visible only to same-tenant token),
  - pagination (`offset`, `limit`) and response envelope (`items`, `offset`, `limit`, `total`).
- Added `server/middleware.py` with:
  - `validate_and_inject_user_context(...)` helper to authenticate and attach claims to request state,
  - `InMemoryRateLimiter` fixed-window limiter,
  - `PathRateLimitMiddleware` and `RateLimitRule` for path-based throttling.
- Updated `server/app.py` to:
  - apply rate limits on `/api/auth/token` and `/api/publish` (`20` requests/minute each),
  - include the new search router.
- Added task tests:
  - `server/tests/test_search.py` mapped regression `test_search_endpoint` for name/description matching, visibility filtering, pagination, empty query, and missing auth.
  - `server/tests/test_middleware.py` for in-memory rate limiter window behavior.

## Tests and results
- `python3 -m pytest server/tests/test_search.py::test_search_endpoint` -> `1 passed`
- `python3 -m pytest server/tests/test_middleware.py::test_rate_limiter_window_behavior` -> `1 passed`

## Bug/error notes
- Bug class: FastAPI request parameter annotation resolution under postponed annotations (`request` treated as query field, causing `422`).
- Attempts for this bug class: `1` (cap: `5`).
- Resolution: import `Request` at module scope and use that type in route signature.

## Teaching notes
- With `from __future__ import annotations`, framework-resolved annotations should reference module-level symbols, not function-local aliases, to avoid runtime dependency-injection issues.
- Keep search logic deterministic and side-effect free (`search_payload`) so behavior remains easy to validate with focused integration tests.
- Rate limiting on auth/publish endpoints is a pragmatic first-line defense against brute-force or abuse while preserving low implementation complexity.
