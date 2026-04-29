# Feature 89 — SWE Handoff: Production Server Configuration

## Context
Harden the registry server for production deployment. Currently the server has dev-friendly defaults. This feature adds structured logging, CORS configuration, health/readiness endpoints, and production-safe startup validation.

## Files to Modify
- `server/config.py` (~77 lines) — Add:
  - `KINNOO_ENV` (dev|production) with behavior switches
  - `CORS_ORIGINS` (comma-separated allowed origins)
  - `UVICORN_WORKERS` (default: 2 for production, 1 for dev)
  - Validation: refuse to start if `KINNOO_ENV=production` and required secrets are missing
- `server/app.py` (194 lines) — Add:
  - CORS middleware with configured origins (dev.kinnoo.ai, dev-api.kinnoo.ai)
  - Health endpoint: `GET /health` → `{"status": "ok", "version": "X.Y.Z"}`
  - Readiness endpoint: `GET /ready` → checks S3 connectivity and auth store accessibility
  - Structured JSON logging configuration when `KINNOO_ENV=production`

## Implementation Notes
- Health endpoint should be lightweight (no I/O)
- Readiness endpoint should check: (1) S3 bucket accessible via HeadBucket, (2) auth store file readable
- CORS: Only allow origins from `CORS_ORIGINS` env var. Default in dev: `*`. In production: must be explicit.
- Structured logging: Use Python's `logging` module with JSON formatter (no external deps needed)
- Graceful shutdown: handle SIGTERM by finishing in-flight requests
- Uvicorn config: expose via `server/run.py` or document in Dockerfile CMD

## Testing
- Test /health returns 200 with correct format
- Test /ready returns 200 when dependencies are available, 503 when not
- Test CORS headers are set correctly
- Test that production mode refuses to start without required env vars
- Test structured JSON log output format

## Dependencies
- None

## Acceptance Criteria Summary
1. JSON logging in production mode
2. CORS configured for allowed origins
3. /health and /ready endpoints
4. Refuse to start without secrets in production
5. Uvicorn production config (2 workers, 30s timeout, graceful shutdown)
