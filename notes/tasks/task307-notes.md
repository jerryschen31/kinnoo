# Task307 Notes - Next.js BFF Rewrite Contract

## Summary
- Updated `web/next.config.ts` to use `BACKEND_URL` (with fallback to `KINNOO_API_BASE_URL`) and default `http://localhost:8000`.
- Added `/api/:path*` rewrite to backend `/api/:path*`.
- Added explicit login/logout bridge rewrites (`/api/login` -> `/login`, `/api/logout` -> `/logout`) to keep web auth flows proxyable.
- Added `web/.env.example` documenting `BACKEND_URL` contract.
- Added `test_feature55_proxy_rewrite_forwarding` in `tests/test_cli_registry_modes.py`.

## Why this implementation
- Keeps the BFF proxy env-driven and production-ready while preserving local defaults.
- Provides a single `/api/*` proxy surface plus targeted bridge routes for existing form-based auth endpoints.

## Teaching Notes
- In BFF architectures, rewrites are most maintainable when they are env-driven and centralized in one place.
- Preserve backward compatibility during env variable migration by supporting both old and new names for one transition period.
- Proxy and auth flows should be tested by contract (expected paths and env usage), not by framework internals.

## Task-scoped regression
- Command: `python3 -m pytest tests --testmon -k test_feature55_proxy_rewrite_forwarding`
- Result: pass (`1 passed`)
