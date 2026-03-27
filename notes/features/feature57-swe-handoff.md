# Feature 57 SWE Handoff - Production Hardening: Security Headers, Error States, and Rate-Limiter Proxy Signals

## Scope
- Feature: feature57
- Tasks: task315, task316, task317, task318
- Tests: test463, test464, test465, test466
- Depends on: feature55, feature56

## Goal
Apply Sub-phase 4 production hardening without regressions:
1. Security headers middleware.
2. Auth route-group loading/error UX.
3. X-Forwarded-For rate limiter compatibility + Redis/Upstash TODO.
4. Env contract clarity and regression safety.

## Task details

### task315 - Security headers middleware
Implement in:
- web/middleware.ts
- web/next.config.ts

Headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- CSP: default-src 'self' (restrictive baseline)
- HSTS in production only

### task316 - Auth loading/error routes
Implement in:
- web/app/(auth)/loading.tsx
- web/app/(auth)/error.tsx
- web/app/(auth)/layout.tsx

Requirements:
- Friendly handling for API downtime, 401, 429.
- Clear retry/login next steps in UX.

### task317 - Forwarded IP + limiter TODO
Implement in:
- web/next.config.ts
- server/middleware/rate_limit.py
- server/routes/api.py

Requirements:
- Ensure forwarded client IP reaches limiter path.
- Keep InMemoryRateLimiter for now.
- Add explicit TODO for Redis/Upstash migration.

### task318 - Sub-phase 4 hardening test suite
Implement in:
- tests/test_run_preflight.py
- tests/test_registry.py
- tests/test_cli_registry_modes.py
- web/__tests__/auth-layout.test.tsx

Requirements:
- Validate headers, auth guard, CSRF/proxy behavior, env contract, non-regression.

## Acceptance criteria mapping
- AC1 -> test463
- AC2 -> test464
- AC3 -> test465
- AC4 -> test466
- AC5 -> test466
- AC6 -> test466

## Notes
- Keep AWS credentials out of web layer.
- Ensure hardening changes do not break existing dashboard and login flows.
