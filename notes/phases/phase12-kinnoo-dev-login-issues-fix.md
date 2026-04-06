# Phase 12: `dev.kinnoo.ai` Login Incident Fix (Cloudflare Worker + Backend Auth)

Date: 2026-04-06  
Environment: Dev (`dev.kinnoo.ai`, `dev-api.kinnoo.ai`)  
Owner: SWE agent session

## Summary

Login on `https://dev.kinnoo.ai/login` failed with:

- "Unable to sign in. Check your credentials and try again."

This was initially suspected to be a credential/auth-store problem, but direct backend checks proved credentials were valid. The final root causes were in the Cloudflare Worker proxy layer:

1. Missing runtime `BACKEND_URL` in Worker environment, causing proxy fallback behavior and Cloudflare 1003 responses on `/api/login`.
2. Proxy response header handling dropped one of multiple `Set-Cookie` headers, so session cookie was lost and user remained unauthenticated.

Both issues were fixed and validated end-to-end.

## Symptoms Observed

### User-facing symptom

- Login page accepted email/password but displayed credential failure message.

### Probe symptom (`dev.kinnoo.ai`)

Direct probe against frontend API route:

- `GET https://dev.kinnoo.ai/api/login` -> `403`
- Body: Cloudflare Error 1003, "Direct IP access not allowed"

### Backend symptom (`dev-api.kinnoo.ai`)

Direct probe against backend host worked:

- `GET https://dev-api.kinnoo.ai/login` -> `200` with CSRF token
- `POST https://dev-api.kinnoo.ai/login` with valid credentials -> `303` redirect to `/agents`
- Response included both cookies:
  - `kinnoo_session` (HttpOnly)
  - `kinnoo_csrf`

This isolated the incident to frontend Worker proxy configuration/behavior.

## Detailed Root Cause Analysis

### Root cause 1: Worker had no runtime backend target variable

The proxy code resolves backend URL from runtime environment:

- `process.env.BACKEND_URL ?? process.env.KINNOO_API_BASE_URL`

The deployed Worker version lacked runtime `BACKEND_URL` binding. As a result, requests routed incorrectly (falling back to default behavior), producing Cloudflare 1003 HTML responses through `/api/login`.

### Root cause 2: Proxy header copy logic was not multi-cookie safe

On successful login, backend sends multiple `Set-Cookie` headers. Existing proxy header copy logic effectively overwrote repeated header keys. This dropped `kinnoo_session` while keeping only one cookie (commonly CSRF), so subsequent `/api/auth/me` returned:

- `401 unauthorized: missing session cookie`

## Cloudflare Worker Actions (Wrangler/OpenNext)

### 0) Create a new Worker with Wrangler (explicit workflow)

In this incident we deployed to existing Worker `kinnoo`, but for a brand-new environment the create path is:

```bash
cd web
# Ensure wrangler.jsonc has desired name, e.g. "name": "kinnoo-dev"
npx opennextjs-cloudflare build
npx opennextjs-cloudflare deploy
```

If the Worker name does not already exist, deploy creates a new Worker script under that name.

Recommended immediate post-create checks:

```bash
npx wrangler versions list --name <worker-name>
npx wrangler versions view <version-id> --name <worker-name>
```

Confirm required runtime bindings (`vars`, services, assets) before routing production traffic.

### 1) Verify deployed Worker versions and bindings

Commands used:

```bash
cd web
npx wrangler versions list --name kinnoo
npx wrangler versions view <version-id> --name kinnoo
```

This confirmed versions and showed that `BACKEND_URL` binding was absent before fix.

### 2) Add runtime Worker variable in `wrangler.jsonc`

File edited: `web/wrangler.jsonc`

Added:

```json
"vars": {
  "BACKEND_URL": "https://dev-api.kinnoo.ai"
}
```

### 3) Redeploy Worker

Commands used:

```bash
cd web
npx opennextjs-cloudflare deploy
```

Deployment output confirmed binding presence:

- `env.BACKEND_URL` -> `"https://dev-api.kinnoo.ai"`

### 4) Build + deploy after proxy code fix

Commands used:

```bash
cd web
npm run build
npx opennextjs-cloudflare build
npx opennextjs-cloudflare deploy
```

## Code Edits in Worker Proxy Layer

### File: `web/lib/backend-proxy.ts`

#### Problematic behavior

Header copying logic did not preserve multiple `Set-Cookie` values.

#### Fix implemented

- Preserve all cookies with `getSetCookie()` when available.
- `append("set-cookie", ...)` each cookie value instead of overwrite semantics.
- Skip reprocessing `set-cookie` in generic header loop.
- Use `append` for other headers to preserve multi-value semantics.

Conceptual diff:

- Before: generic header copy with `set(...)`
- After: explicit multi-cookie handling + `append(...)`

## Verification Steps and Results

### A) Credential validity in live ECS auth store

Executed in running ECS task:

- Confirmed user exists.
- Confirmed `password_verify` for temporary password = `True`.
- Confirmed account unlocked and active.

### B) Frontend endpoint after runtime var fix

- `GET /api/login` moved from `403` to `200`.
- CSRF token extraction succeeded.

### C) Frontend endpoint after cookie-forwarding fix

- `POST /api/login` -> `303`.
- Response headers included both:
  - `set-cookie: kinnoo_session=...`
  - `set-cookie: kinnoo_csrf=...`
- Follow-up `GET /api/auth/me` with returned cookies -> `200` and user payload:

```json
{"user_id":"...","tenant_slug":"jerryschen","username":"jerryschen@gmail.com"}
```

Result: login flow restored end-to-end on `dev.kinnoo.ai`.

## Incident Timeline (Condensed)

1. User login failed from browser despite known credentials.
2. API probe on `dev.kinnoo.ai/api/login` returned Cloudflare 1003 (`403`).
3. Direct `dev-api.kinnoo.ai/login` succeeded (`303`, cookies set).
4. Identified missing Worker runtime `BACKEND_URL` binding.
5. Added `vars.BACKEND_URL` in `wrangler.jsonc`; redeployed.
6. Login improved to `303`, but auth still missing session cookie.
7. Identified `Set-Cookie` overwrite in proxy header copy.
8. Patched proxy to preserve all `Set-Cookie` headers; redeployed.
9. Final probe: `/api/auth/me` returned `200` with authenticated user.

## Lessons Learned

1. Worker runtime bindings must be explicit; build-time env alone is not sufficient for this runtime proxy pattern.
2. Any proxy handling auth must preserve repeated `Set-Cookie` headers exactly.
3. Cloudflare 1003 responses can masquerade as credential issues at UI layer when proxy target is wrong.
4. Always validate both layers independently:
   - frontend route (`dev.kinnoo.ai/api/login`)
   - backend host (`dev-api.kinnoo.ai/login`)

## Follow-up: Production CLI Automation Scripts (Planned)

We should create command-line scripts for Cloudflare Worker operations before production rollout.

### Why

- Reduce manual dashboard drift.
- Ensure reproducible deploy/config across environments.
- Speed incident response for auth/proxy failures.

### Suggested scripts

1. `scripts/cf-worker-deploy.sh`
- Build + deploy OpenNext worker.
- Print version ID and active bindings.

2. `scripts/cf-worker-verify.sh`
- Validate worker route, `BACKEND_URL` binding, and health probes:
  - `/api/login` GET status
  - CSRF extraction
  - optional auth smoke tests

3. `scripts/cf-worker-vars-sync.sh`
- Set/check required runtime vars (`BACKEND_URL`, etc.) from env files or CI secrets.

4. `scripts/cf-worker-versions.sh`
- List versions, show current version details, and highlight binding diffs.

### Production readiness requirement

Add these scripts before production cutover and run them in CI/CD after each deployment.
