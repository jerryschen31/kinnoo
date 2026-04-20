# Kinde Auth Setup Plan for Dev (`dev.kinnoo.ai`)

Date: 2026-04-19  
Source issue: https://github.com/jerryschen31/kinnoo/issues/335  
Scope: Replace current local SQLite/JSON auth flow with Kinde-backed auth in Dev, and wire registry ownership to Kinde-authenticated identities.

---

## 1) Goal and Definition of Done Mapping

This plan targets these exact outcomes:

1. Kinde tenant configured for Dev + Staging usage.
2. `server/` auth routes validate Kinde OIDC/JWT tokens (not local password JWTs).
3. `kinnoo login` uses Kinde hosted auth redirect flow and stores usable registry auth state.
4. `kinnoo logout` clears local auth state and logs out Kinde/browser session.
5. Web login/register moves from custom forms to Kinde auth entrypoints.
6. Existing SQLite-based auth (`user_store.py`, `session.py`, SQLite auth tables) is retired or reduced to non-auth identity mapping.
7. Invalid/expired Kinde tokens are rejected with clear errors.
8. Existing auth tests are updated/replaced and pass.
9. Token refresh works without forcing frequent re-login.
10. Registry links published agents to authenticated users/tenants (blank-registry reset is allowed).
11. Auth implementation remains provider-portable: switching from Kinde to another OIDC provider should be primarily config + adapter substitution, not a route-by-route rewrite.

---

## 2) Current-State Baseline (from repo)

Current auth is local/custom:

- API token issuance: `server/routes/auth.py` + `server/auth/token.py` (HMAC token service).
- Web session auth: `server/routes/web_auth.py` + `server/auth/session.py` + CSRF cookies.
- Local user persistence: `server/storage/user_store.py` (JSON files).
- SQLite auth tables: `server/storage/sqlite_auth_store.py` + `server/storage/sql/schema_auth.sql`.
- CLI login is username/password to `/api/auth/token`: `src/kinnoo/auth_command.py`.
- Web frontend login form posts to `/api/login`: `web/app/(public)/login/page.tsx` + `web/lib/auth-client.ts`.
- Worker proxies frontend `/api/*` to backend with `BACKEND_URL`: `web/lib/backend-proxy.ts`, `web/wrangler.jsonc`.

Related infra constraints:

- Dev frontend: `https://dev.kinnoo.ai`
- Dev backend: `https://dev-api.kinnoo.ai`
- ECS env wiring currently uses legacy secret names (`JWT_SECRET`, `SESSION_SECRET`) in IaC module `iac/modules/ecs-fargate/main.tf`; application code expects `REGISTRY_*` names.

---

## 3) Responsibilities Split (No Ambiguity)

Use these labels everywhere in execution:

- **[HUMAN]**: manual Kinde dashboard, Cloudflare, AWS/Secrets, DNS, approvals.
- **[SWE]**: code implementation and config/IaC changes.
- **[TEST]**: automated and manual validation implementation/execution.

No step should be executed without an owner label.

---

## 3.1) Vendor Lock-In Guardrails (Mandatory)

These are non-negotiable implementation constraints for SWE and TEST.

1. **Open standards only at protocol boundary**:
   - Use OIDC/OAuth2 standards (discovery document, JWKS, authorization code + PKCE, refresh token, standard claims).
   - Do not make route/middleware behavior depend on Kinde-only SDK semantics.
2. **Own internal identity keys**:
   - Internal user identity must remain UUID-based in kinnoo-owned storage.
   - External provider subject (`sub`) must be stored as mapped identity (`kinde_user_id` today), not used as internal PK.
   - Migration to another provider should preserve internal foreign keys and update only external subject mappings.
3. **Single auth abstraction per runtime**:
   - Server: one provider adapter boundary for token verification, auth URL construction, token exchange/refresh, logout URL generation.
   - Web: one auth hook/service (`useAuth`/`AuthService`) used by UI and API routes; no direct provider SDK calls spread across pages/components.
   - CLI: one auth service module encapsulating login, callback/device exchange, refresh, and logout behavior.
4. **Provider-neutral config contract**:
   - Add provider-neutral env names (example: `AUTH_PROVIDER`, `AUTH_ISSUER_URL`, `AUTH_CLIENT_ID`, `AUTH_CLIENT_SECRET`, `AUTH_AUDIENCE`, `AUTH_REDIRECT_URI`, `AUTH_LOGOUT_REDIRECT_URI`).
   - Kinde-specific names may remain as compatibility aliases during migration, but app runtime should resolve to provider-neutral config internally.
5. **Feature-flagged provider selection**:
   - Add provider selection flag (example: `AUTH_PROVIDER=oidc_kinde`), so future providers can be introduced via adapter selection.
6. **Test portability as a first-class requirement**:
   - Add adapter-level tests that run against mocked OIDC metadata/JWKS and assert behavior independent of vendor-specific SDKs.

Reference validation already present in planning:
- `notes/features/postgres-registry-db-planning.md` defines internal UUID PK for `users.id` and separate `kinde_user_id` mapping field.

---

## 4) Prerequisite Decisions (Blockers Before Coding)

These decisions must be explicitly recorded before implementation begins:

1. **Environment naming decision**: Issue DoD says Dev+Staging, current Kinde has Dev+Prod. Decide:
   - Option A: Rename existing Kinde “prod” to “staging” for now, or
   - Option B: keep Dev+Prod but treat Prod as staging until real production cutover.
2. **Tenant mapping strategy**:
   - Option A: Kinde org claim -> registry tenant slug (preferred),
   - Option B: first login auto-creates tenant from email slug.
3. **CLI auth UX decision**: ✅ RESOLVED — Browser-based PKCE authorization code flow with local loopback callback.
   - CLI opens browser to Kinde authorize endpoint, local temporary HTTP server listens on loopback for callback.
   - Uses dynamic port allocation (preferred 8765, fallbacks 8766/8767, then OS-assigned free port).
4. **Refresh token storage policy**:
   - local config file encrypted-at-rest vs plaintext in config directory.
5. **Blank registry reset confirmation**:
   - Explicit approval to discard current dev registry users/tenants/agents.
6. **Kinde application topology**: ✅ RESOLVED — Option B: separate Kinde apps for web and CLI (cleaner separation).
   - **Application A — Kinnoo Web Dev**: Backend type, Python framework. Confidential client with client secret. Used for browser-based web login where auth orchestration is in FastAPI.
   - **Application B — Kinnoo CLI Dev**: Frontend/Native type (Other native). Public client with PKCE, no client secret at runtime. Used for CLI `kinnoo login` with loopback callback.
   - Both apps created in Kinde by human (completed per issue #350).
7. **CLI callback port (if loopback flow is used)**: ✅ RESOLVED — Dynamic port allocation with Kinde wildcard callback.
   - Kinde CLI app callback URL: `http://127.0.0.1:*/auth/callback` (wildcard port).
   - CLI runtime: prefer port 8765, fallback 8766/8767, then OS-assigned free port via `socket.bind(('127.0.0.1', 0))`.
   - No single fixed port required; wildcard in Kinde allows any loopback port.

If any decision is unresolved, pause implementation.

---

## 5) Human-Run Setup in Kinde (Manual Checklist)

### 5.1 [HUMAN] Kinde tenant and application configuration

> **Two-app topology (resolved in issue #350 followup):** Web and CLI use separate Kinde applications. Both have been created by human.

1. Open Kinde admin and select target tenant.
2. Ensure two non-prod environments are available for this phase:
   - `dev`
   - `staging` (or temporary use of current "prod" as staging per decision above).

#### 5.1.1 Application A — Kinnoo Web Dev (Backend, Python)

This is the confidential-client app for browser-based web login where auth orchestration is in FastAPI.

1. Type: **Backend application**
2. Framework: **Python**
3. Confirm OIDC/OAuth2 enabled, Authorization Code + PKCE supported, refresh token issuance enabled, token signing defaults enabled.
4. Configure **Application homepage URI**: `https://dev.kinnoo.ai`
5. Configure **Application login URI**: `https://dev.kinnoo.ai/login`
6. Configure **Allowed callback URLs** (exact):
   - `https://dev.kinnoo.ai/auth/callback`
   - `https://dev-api.kinnoo.ai/auth/callback` (keep for backend-first callback option)
   - `http://localhost:3000/auth/callback` (local web dev)
   - `http://127.0.0.1:8000/auth/callback` (local backend dev)
7. Configure **Allowed logout redirect URLs** (exact):
   - `https://dev.kinnoo.ai/login`
   - `http://localhost:3000/login`
8. Configure **Allowed origins / CORS**:
   - `https://dev.kinnoo.ai`
   - `https://dev-api.kinnoo.ai`
   - `http://localhost:3000`
   - `http://127.0.0.1:8000`
9. Configure API audience/scopes for registry:
   - `registry:read`
   - `registry:publish`
   - `registry:admin`
10. Export and securely store required values:
    - Kinde domain/issuer URL,
    - Web app client ID,
    - Web app client secret,
    - audience,
    - JWKS endpoint URL,
    - authorize/token/logout endpoints.

#### 5.1.2 Application B — Kinnoo CLI Dev (Frontend/Native, Public Client, PKCE)

This is the public-client app for `kinnoo login` CLI flow. No client secret at runtime.

1. Type: **Frontend application** (choose "Other native" subcategory)
2. Framework: **Generic/Other** (standard OIDC PKCE in Python, not framework SDK)
3. Important: configure for **PKCE** with no hard dependency on a client secret at runtime.
4. Configure **Application homepage URI**: `https://dev.kinnoo.ai` (or docs page; not functionally critical for CLI)
5. Configure **Application login URI**: `https://dev.kinnoo.ai/login` (optional)
6. Configure **Allowed callback URLs** (exact):
   - `http://127.0.0.1:*/auth/callback` (wildcard port — allows dynamic port allocation by CLI)
7. Configure **Allowed logout redirect URLs** (exact):
   - `https://dev.kinnoo.ai/login`
8. Export and securely store required values:
   - CLI app client ID (no client secret — public client).

#### 5.1.3 Shared tenant-level setup

1. Create at least two test users in Kinde:
   - one admin-equivalent user,
   - one regular user.
2. If using org-based tenancy, create at least one org mapped to one tenant slug.

### 5.2 [HUMAN] Secrets and environment injection setup

1. Add dev secrets in AWS Secrets Manager (or existing secret mechanism):
   - `KINDE_ISSUER_URL`
   - `KINDE_WEB_CLIENT_ID` (Web app confidential client ID)
   - `KINDE_WEB_CLIENT_SECRET` (Web app client secret)
   - `KINDE_CLI_CLIENT_ID` (CLI app public client ID — no secret needed)
   - `KINDE_AUDIENCE`
   - `KINDE_LOGOUT_REDIRECT_URI`
   - `KINDE_WEB_REDIRECT_URI`
   - Note: CLI redirect URI is dynamic (loopback + assigned port) and resolved at runtime, not stored as a secret.
2. For local runs (non-production), keep fallback values in a local `.env` file or equivalent local env file, but do **not** assume `server/` auto-loads `.env` files.
   - Recommended path: repository root `.env` (so local commands and scripts can share one env source).
   - Developers must explicitly export/source those variables before starting the backend.
   - Example from repository root: `set -a; . ./.env; set +a` (or `direnv` if already used in your environment).
3. Update Cloudflare Worker runtime vars if needed:
   - keep `BACKEND_URL=https://dev-api.kinnoo.ai`
   - add auth-related frontend vars only if required by web implementation.
4. Confirm ECS task definition injects app-expected env names (not only legacy `JWT_SECRET`/`SESSION_SECRET`).

---

## 6) Implementation Plan for SWE Agent

### Phase A — Auth Architecture Cutover (Server)

#### A1 [SWE] Introduce OIDC token verification abstraction (Kinde first adapter)

Create new auth verifier module(s) under `server/auth/` with a provider-agnostic boundary:

- define adapter interface/class contract (example: `OIDCAuthProvider`),
- implement Kinde adapter first (example: `KindeOIDCProvider`),
- keep route/middleware code dependent on interface, not concrete provider type,
- isolate provider-specific endpoint formats and claim quirks inside adapter only.

Core verifier requirements:

- fetch OIDC discovery document,
- resolve JWKS,
- validate RS256 JWT signature,
- validate issuer, audience, expiration (`exp`), not-before (`nbf`), issued-at (`iat`),
- map claims to internal auth context (`sub`, email, org/tenant claim, scopes).

Replace dependency on local HMAC token validation from `server/auth/token.py` in request auth path.

#### A2 [SWE] Add internal identity upsert (JIT provisioning)

On first valid Kinde-authenticated request:

- upsert local `users` reference record keyed by Kinde `sub`,
- update denormalized fields (email/display name),
- derive role and tenant linkage policy from decision in Section 4.

For this phase, if full Postgres auth tables are not yet live, implement transitional store with explicit migration path; do not reintroduce password/session logic.

#### A3 [SWE] Replace auth routes and session routes

Update:

- `server/routes/auth.py`
- `server/routes/web_auth.py`
- `server/app.py`
- `server/auth/middleware.py`

Required behavior:

1. `/api/auth/token` no longer accepts raw username/password for Kinde users.
2. Add redirect-based login start endpoint(s) and callback endpoint(s).
3. Add logout endpoint that clears local state and redirects through Kinde logout.
4. `/api/auth/me` derives identity from Kinde session/token-backed context.
5. Error envelopes remain consistent (`build_error_envelope` usage preserved).

#### A4 [SWE] Retire local password/session-only components

Deprecate/remove usage from runtime path:

- `server/auth/session.py` (if replaced completely),
- `server/auth/tokens.py` registration/reset flows,
- `server/storage/sqlite_auth_store.py` tables related to sessions/password reset,
- registration/password-reset endpoints in `server/routes/auth.py`.

Keep a compatibility boundary only if required for phased rollout, behind explicit feature flag and defaulted OFF in Dev cutover.

---

### Phase B — Web Frontend Auth Migration

#### B1 [SWE] Replace custom login UI flow with Kinde redirects

Update:

- `web/app/(public)/login/page.tsx`
- `web/lib/auth-client.ts`
- `web/app/api/login/route.ts`
- `web/app/api/logout/route.ts`
- relevant auth layout and tests.

Required behavior:

1. Login button initiates Kinde hosted login (no password form submission to backend).
2. Callback route finalizes auth and redirects to `/registry`.
3. Logout terminates app session + Kinde session and returns to `/login`.
4. Auth-protected layout still redirects unauthenticated users to `/login`.

Portability requirement:
- implement/retain a single web auth abstraction (`web/lib/auth-client.ts` and/or `web/lib/use-auth.ts`) so provider switch does not require page-level rewrites.

#### B2 [SWE] Remove obsolete signup/reset-password UI flows or re-point them

Evaluate and update:

- `web/app/(public)/signup/page.tsx`
- forgot/reset password pages.

Expected Dev behavior:

- either redirect users to Kinde-hosted signup/reset,
- or hide these routes until Kinde-hosted paths are confirmed.

---

### Phase C — CLI (`kinnoo login/logout`) Kinde integration

#### C1 [SWE] Implement browser/device login flow in CLI

> **Uses Kinnoo CLI Dev app (public client, PKCE)**. CLI uses its own Kinde application (separate from Web app) with no client secret dependency.

Update `src/kinnoo/auth_command.py`:

1. `kinnoo login` initiates browser-based PKCE authorization code flow using the CLI app's client ID.
2. CLI starts a temporary local HTTP server on `127.0.0.1` (preferred port 8765, fallback 8766/8767, then OS-assigned free port via `socket.bind(('127.0.0.1', 0))`).
3. Browser opens to Kinde authorize endpoint; callback returns to `http://127.0.0.1:<port>/auth/callback`.
4. CLI exchanges authorization code + PKCE code verifier for tokens.
5. CLI stores auth state with:
   - access token,
   - refresh token,
   - expiration metadata,
   - tenant context.
6. Remove dependency on direct username/password prompt for Dev Kinde auth flow.

Portability requirement:
- implement provider interactions through one CLI auth service boundary so changing providers mostly updates adapter/config, not command UX wiring.

#### C2 [SWE] Implement refresh behavior

Before remote calls (`publish`, `list`, `search`, `install`, `fetch`):

1. if access token is close to expiry, refresh using refresh token;
2. if refresh fails, prompt re-login with actionable message.

#### C3 [SWE] Logout

`kinnoo logout` must:

1. clear local auth state,
2. optionally open Kinde logout URL for full session termination,
3. keep current success/no-state behavior semantics.

---

### Phase D — Registry User/Tenant Linking

#### D1 [SWE] Ownership linkage updates

Publishing must persist publisher identity from Kinde subject/user mapping, not legacy local username.

Touch points likely include:

- publish route(s) under `server/routes/publish.py`,
- metadata ownership fields used by `MetadataManager`,
- future Postgres user/tenant tables per `notes/features/postgres-registry-db-planning.md`.

#### D2 [SWE] Blank registry reset execution

For Dev cutover:

1. reset auth-related local stores (and metadata store if approved),
2. bootstrap only Kinde-mapped users/tenants on first login/publish,
3. document exact reset procedure and one-command script if possible.

---

### Phase E — Infrastructure and Deployment

#### E1 [SWE] Config surface additions

Add config keys in `server/config.py` (or equivalent) for:

- provider selection (`AUTH_PROVIDER`),
- provider-neutral issuer/client/audience/redirect settings,
- Kinde issuer/domain,
- Web app client ID/secret (`KINDE_WEB_CLIENT_ID`, `KINDE_WEB_CLIENT_SECRET`),
- CLI app client ID (`KINDE_CLI_CLIENT_ID` — public client, no secret),
- audience,
- redirect/logout URLs (web redirect URI stored; CLI redirect URI resolved at runtime),
- optional org/tenant claim mapping key,
- token verification cache/jwks refresh settings.

Config rule:
- provider-neutral env names are canonical in app runtime; Kinde-prefixed names are optional aliases during transition.
- Server only needs the Web app client ID/secret for server-mediated auth flows.
- CLI only needs the CLI app client ID for PKCE flows (no secret).

#### E2 [SWE] IaC/env wiring

Update IaC and deployment wiring:

- `iac/modules/ecs-fargate/main.tf`
- `iac/modules/secrets/main.tf`
- env tfvars where needed.

Ensure app-required names are injected exactly, and remove naming mismatch risks.

#### E3 [HUMAN + SWE] Cloudflare Worker verification

Keep and verify:

- `web/wrangler.jsonc` runtime `BACKEND_URL=https://dev-api.kinnoo.ai`
- cookie/header forwarding behavior intact (multi-`Set-Cookie` safe).

---

## 7) Test Agent Plan (Detailed)

### 7.1 Automated test updates/additions

### Server tests

Update or replace:

- `server/tests/test_auth_route.py`
- `server/tests/test_jwt_auth.py`
- `server/tests/test_session_auth.py`
- `server/tests/test_web_auth.py`

New required coverage:

1. valid Kinde token accepted,
2. expired token rejected (`401` clear message),
3. invalid signature / wrong issuer / wrong audience rejected,
4. missing scope -> `403`,
5. login callback success/failure behavior,
6. logout invalidates local session linkage.
7. provider adapter contract tests pass using mocked OIDC discovery/JWKS responses.
8. switching provider selection flag fails fast with clear errors when required provider config is missing.

### CLI tests

Update/add under `tests/client_cli_*`:

1. `kinnoo login` initiates browser/device flow successfully,
2. login failure paths are actionable,
3. refresh token path exercised,
4. logout clears state.

### Web tests

Update:

- `web/__tests__/login-page.test.tsx`
- `web/__tests__/auth-layout.test.tsx`

Add coverage:

1. login page uses redirect CTA (not password POST),
2. callback route success/failure handling,
3. protected layout with unauthenticated/expired session behavior,
4. logout integration and redirect.

### 7.2 Smoke/e2e validation matrix (must pass)

1. Browser login on `https://dev.kinnoo.ai/login` succeeds.
2. Browser logout succeeds and protected page redirects to login.
3. CLI login against `https://dev-api.kinnoo.ai` succeeds without password prompt.
4. CLI publish after login associates artifact with correct user/tenant identity.
5. Access token expiry simulation triggers refresh, not forced re-login.
6. Corrupted token simulation returns clear auth error.
7. Existing non-auth registry workflows remain functional.

### 7.3 Recommended command execution set

- Python tests: `python3 -m pytest`
- Focused server auth: `python3 -m pytest server/tests/test_auth_route.py server/tests/test_web_auth.py`
- Focused CLI auth: `python3 -m pytest tests -m "client_cli_login or client_cli_logout or client_cli_publish"`
- Web tests: `cd web && npm test`

---

## 8) Acceptance Criteria by Stream

### 8.1 Auth correctness

- No active runtime path depends on local password validation for Dev login.
- All protected API routes accept Kinde token/session-backed identity.
- Invalid/expired tokens produce deterministic error envelope.
- Auth provider is selected through config/adapter boundary rather than hardcoded Kinde calls in route handlers.

### 8.2 User/tenant linkage

- First authenticated request creates/updates local user reference record.
- Publish ownership is tied to Kinde-authenticated user identity.
- Tenant context resolution is deterministic and documented.

### 8.3 Operational readiness

- Dev deploy has all required Kinde env vars/secrets.
- Cloudflare Worker proxy remains functional for login/callback/logout.
- `/health` and `/ready` remain green after deploy.

---

## 9) Rollout Sequence (Dev)

1. [HUMAN] Complete Kinde dashboard setup + secrets creation.
2. [SWE] Ship backend token verification + callback/login/logout routes.
3. [SWE] Ship web redirect-based auth changes.
4. [SWE] Ship CLI Kinde login/refresh/logout.
5. [SWE] Ship identity linkage changes for publish.
6. [TEST] Run automated suites.
7. [HUMAN + TEST] Run live Dev smoke matrix.
8. [HUMAN] Approve Dev cutover and blank-registry reset.

Do not reorder unless explicitly approved.

---

## 10) Rollback Plan (If Cutover Fails)

1. Revert to pre-cutover branch/tag.
2. Redeploy previous backend + frontend worker artifact.
3. Restore previous env var set (disable Kinde-only routes).
4. Re-enable legacy login flow only temporarily for service continuity.
5. Document failure cause and keep Kinde creds intact for next attempt.

Rollback trigger examples:

- login success rate drops below acceptable threshold,
- publish workflow blocked for authenticated users,
- token refresh broken causing frequent forced logins.

---

## 11) Risk Register and Controls

1. **Risk**: Kinde callback URL mismatch -> login loop/fail.
   - **Control**: exact callback URL checklist (Section 5.1).
2. **Risk**: audience/issuer mismatch -> all API calls unauthorized.
   - **Control**: startup validation on required Kinde config.
3. **Risk**: Cloudflare proxy drops auth cookies/headers.
   - **Control**: preserve multi-`Set-Cookie`; run `/api/login` and `/api/auth/me` probes.
4. **Risk**: secret name mismatch in ECS/IaC.
   - **Control**: explicit env var contract test during deploy.
5. **Risk**: tenant mapping errors publish into wrong namespace.
   - **Control**: deterministic mapping tests with two users/two tenants.
6. **Risk**: refresh token mishandling in CLI.
   - **Control**: expiry simulation tests + secure local storage review.

---

## 12) Artifacts to Produce During Execution

Mandatory implementation artifacts:

1. Updated code across server/web/cli as listed above.
2. Updated tests (server, CLI, web) and passing test outputs.
3. Dev deployment runbook update for Kinde setup and secret wiring.
4. One concise cutover report in `notes/` containing:
   - exact deployed commit SHA,
   - validated smoke results,
   - known limitations.

---

## 13) “Done Done” Checklist

- [ ] Kinde dev/staging environment config complete and verified by human.
- [ ] Web login/logout works end-to-end on `dev.kinnoo.ai`.
- [ ] CLI login/logout uses Kinde and works end-to-end.
- [ ] Backend validates Kinde tokens and rejects invalid/expired tokens clearly.
- [ ] Agent publish associates with authenticated user/tenant identity.
- [ ] Legacy password/session auth paths removed or fully disabled in Dev.
- [ ] Automated tests updated and passing.
- [ ] Smoke matrix complete and recorded.
- [ ] Rollback procedure validated.
