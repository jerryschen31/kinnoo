# Feature 57 Smoke Tests - Security Headers, Error States, and Rate-Limit Signals

## 1) Security headers baseline
1. Request a frontend page.
2. Inspect response headers.

Pass if:
- X-Frame-Options, X-Content-Type-Options, Referrer-Policy, CSP are present.

## 2) HSTS production gating
1. Run in development mode and inspect headers.
2. Run in production mode and inspect headers.

Pass if:
- HSTS appears only in production.

## 3) Auth loading and error pages
1. Simulate loading state in (auth) route.
2. Simulate 401, 429, and generic downtime errors.

Pass if:
- loading.tsx and error.tsx render clear and actionable UX.

## 4) Forwarded IP for limiter path
1. Send proxied request with X-Forwarded-For context.
2. Observe backend limiter behavior/logs.

Pass if:
- Limiter keys use forwarded client IP path.

## 5) Redis/Upstash migration note
1. Inspect relevant limiter/proxy code comments.

Pass if:
- TODO note for Redis/Upstash migration exists.

## 6) Non-regression check
1. Re-run core login and /registry flows.

Pass if:
- Hardening changes do not break existing functionality.
