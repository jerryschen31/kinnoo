# API contract baseline (Stage 0)

This document captures current contract constants and endpoint surfaces that must remain in lockstep across the public CLI/web code and private backend/auth code.

## Canonical location recommendation

- Maintain the canonical API contract as **`docs/api-contract.md` in the public repo**.
- Mirror that same document in the private repo (or consume it as a synced artifact) so both sides use one source of truth.

## Auth-flow constants (must remain lockstep)

From `src/kinnoo/auth_command.py`:

- `CALLBACK_PATH = "/auth/callback"`
- `CALLBACK_SERVER_PORTS = (8765, 8766, 9872, 49527)`
- `HOSTED_LOGIN_SCOPE = "openid profile email"`
- `TOKEN_REFRESH_SKEW_SECONDS = 120`

Hosted auth discovery and token endpoints used by CLI:

- `GET /api/auth/config`
- `POST /api/auth/token`

## CLI remote registry client endpoint surface

From `src/kinnoo/remote_client.py`:

- `POST /api/publish`
- `GET /api/agents/{tenant_slug}/{agent_slug}/{version}/download`
- `GET /api/search?q=...`
- `GET /api/agents?tenant=...`
- `GET /api/mirror/clawhub/{slug}`
- `GET /api/mirror/clawhub?mode=...&since=...`

Behavioral contract notes:

- Bearer auth header required for remote client requests
- JSON responses expected by default; invalid JSON raises actionable client error
- Relative `download_url` values are normalized to absolute URLs by CLI

## Server route baseline (private backend)

From `server/routes/*` and `server/api/*`:

- Auth endpoints include `GET /api/auth/config`, `POST /api/auth/token`, registration/password-reset endpoints, and `GET /api/auth/me`
- Registry endpoints include publish/search/list/download/archive routes under `/api/*`
- Web auth includes callback route at `/auth/callback`

## Web frontend/backend contract

From `web/lib/backend-proxy.ts` and `web/app/api/[...path]/route.ts`:

- Frontend proxy forwards `/api/{path}` to backend URL from `BACKEND_URL` or `KINNOO_API_BASE_URL`
- Proxy preserves response headers/cookies and forwards request method/query/body
- Default fallback backend URL is local (`http://localhost:8000`)

## Contract-test requirement

Public repo should include contract tests (against fake HTTP backend fixtures) that verify:

1. Auth constants and callback semantics expected by CLI
2. Remote client request/response shape and error handling
3. Web proxy forwarding semantics

Private repo should retain end-to-end tests validating actual server implementation against the same contract.
