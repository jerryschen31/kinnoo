# Phase3 Remote Registry Implementation Notes

## Scope and Status
This note captures all planning-manifest changes added for remote registry build-out based on `notes/phases/phase3-registry-planning.notes` and Jerry decisions.

Primary scope:
- Updated `feature28` (client abstraction + remote client details)
- Updated `feature29` (server architecture, metadata model, storage abstraction)
- Updated `feature30` (authenticated web UI model)
- Added `feature43` (auth, bootstrap, user/tenant management prerequisite)
- Added tasks `task229` through `task248`
- Added tests `test327` through `test346`

Validation status:
- `python3 scripts/validate_project_manifests.py` passes
- Merge conflict markers removed from `TASKS.txt`
- Feature43 duplicate status formatting fixed

## Feature-Level Summary

### feature28 - Registry Backend Abstraction & Remote Client
What changed:
- Added concrete task linkage: `task229`-`task233`
- Tightened ACs to multi-tenant pathing and authenticated-only remote reads
- Added explicit config contract for URL/token/tenant slug and env var precedence
- Expanded error handling coverage to include 403/409/429 in addition to existing classes

Design intent:
- Keep local behavior unchanged while introducing a protocol seam for remote backends
- Make remote read/write behavior explicit and secure-by-default (auth required)

### feature29 - Remote Registry Server
What changed:
- Added concrete task linkage: `task239`-`task244`
- Updated architecture to S3-compatible storage abstraction with three backends:
  - local filesystem
  - mock S3 (moto)
  - real S3/MinIO
- Added three-tier JSON metadata model and canonical object key layout
- Updated API endpoint descriptions to include tenant paths and auth requirement
- Added scoped JWT enforcement/rate limiting/max upload constraints in ACs

Design intent:
- Keep V1 simple but production-mappable
- Ensure local development can run entirely without real AWS resources
- Preserve easy transition to real S3 by configuration only

### feature30 - Registry Web UI
What changed:
- Added concrete task linkage: `task245`-`task248`
- Switched from anonymous browsing to authenticated session-required browsing
- Clarified CSRF and secure cookie expectations
- Updated page routes to tenant-aware paths

Design intent:
- Align web UI behavior with Jerry decision: authenticated-only reads
- Reuse server auth/session mechanisms from feature43

### feature43 - Auth, User & Tenant Management (new)
What changed:
- Added new prerequisite feature with tasks `task234`-`task238`
- Encodes bootstrap-admin policy and admin-only user/tenant creation
- Adds JWT claims model, token denylist, key rotation, and session auth constraints

Design intent:
- Isolate account/bootstrap/auth concerns into a prerequisite feature instead of scattering in feature29/30
- Match Jerry decisions directly:
  - user-chosen unique tenant slugs
  - no tenant transfer in V1
  - authenticated-only reads
  - bootstrap admin first
  - soft delete acceptable for V1

## Tasks Added

### feature28 tasks
- `task229` RegistryBackend protocol + LocalRegistryBackend refactor
- `task230` RemoteRegistryClient HTTP implementation
- `task231` Registry config system (URL, token, tenant)
- `task232` CLI integration with backend abstraction
- `task233` Remote client error handling

### feature43 tasks
- `task234` User model and password hashing
- `task235` Bootstrap admin CLI command
- `task236` Tenant model and slug management
- `task237` JWT access token issuance and validation
- `task238` Session cookie auth for web UI

### feature29 tasks
- `task239` FastAPI scaffold + S3 storage abstraction
- `task240` JSON metadata model (3-tier)
- `task241` Publish endpoint
- `task242` List/detail endpoints
- `task243` Download endpoint with presigned URLs
- `task244` Search endpoint + auth middleware + rate limiting

### feature30 tasks
- `task245` Jinja2 setup + base layout
- `task246` Login page + session auth flow
- `task247` Agent listing + search pages
- `task248` Agent profile + download pages

## Tests Added

### feature28 tests
- `test327` protocol + local backend compatibility
- `test328` remote client HTTP contract and auth headers
- `test329` config/env precedence
- `test330` CLI backend selection behavior
- `test331` remote error handling matrix

### feature43 tests
- `test332` password hashing/verification
- `test333` bootstrap lifecycle
- `test334` tenant slug uniqueness/admin-only creation
- `test335` JWT issuance/validation/scope/revocation/rotation
- `test336` session security/CSRF/invalidation

### feature29 tests
- `test337` storage protocol across local/mock/real S3 backends
- `test338` metadata model consistency (3-tier)
- `test339` publish endpoint behavior and constraints
- `test340` list/detail endpoint behavior and authorization
- `test341` presigned download behavior
- `test342` search behavior and visibility controls

### feature30 tests
- `test343` template and base layout configuration
- `test344` login/session/CSRF flow
- `test345` listing/search page behavior
- `test346` profile/download behavior

## SWE Implementation Notes

### 1) Build order (recommended)
1. feature43 (auth/bootstrap/users/tenants)
2. feature28 (client abstraction and CLI backend wiring)
3. feature29 (server API + storage + metadata)
4. feature30 (web UI)

Rationale:
- feature29/30 rely on auth semantics finalized in feature43
- feature28 can proceed in parallel once API contracts are stable

### 2) Storage abstraction guidance
- Implement a strict `StorageBackend` protocol first
- Keep route code unaware of storage implementation details
- Use identical key schema across local/mock/s3
- Ensure presign method exists on all backends (local can return deterministic internal URLs for tests)

### 3) JSON metadata consistency
- Treat version metadata as source of truth
- Agent index/global index should be derived/update-projected views
- Add a rebuild utility to regenerate aggregate indexes from version docs
- Use schema_version field in payload and filename suffix (`.v1.json`)

### 4) Auth and security defaults
- Short-lived access tokens (default 60m)
- Strong password hashing (argon2 preferred)
- Never log tokens/passwords/secrets
- Secure session cookie flags always set in production mode
- CSRF for all POST forms in web UI
- Rate limit `/api/auth/token` and `/api/publish`

### 5) Multi-tenant contract details
- Tenant slugs are user-chosen, unique, validated
- Namespace path contract: `tenant_slug/agent_slug/version`
- V1 policy: no cross-tenant transfer
- V1 policy: only authenticated reads

### 6) Regression and compatibility checks
- Preserve all existing `--local` behavior and CLI UX
- Keep local pack/install/publish workflows unchanged when remote config absent
- Add contract tests for response error envelopes and status codes

### 7) Implementation risk watchlist
- Concurrent metadata writes causing index drift
- Auth scope mismatches between CLI and server route policy
- Inconsistent presigned URL TTL handling per backend
- Missing env var validation leading to partial startup failures

### 8) Definition of done for SWE handoff
- All new task-linked tests exist and pass
- Existing regression suites remain green
- Manifest validator passes
- Route docs and config docs updated for registry/auth env vars
- No merge conflict markers, no schema/key duplicates in manifests

## Compact Review Checklist

Use this section as a quick approval gate per feature.

### Feature28 Review Gate
- [ ] Scope sanity: Tasks `task229`-`task233` and tests `test327`-`test331` are present and linked.
- [ ] Local regression safety: existing `--local` publish/install/list/search behavior remains unchanged.
- [ ] Remote contract: tenant-aware remote pathing and auth header usage are implemented.
- [ ] Config precedence: env vars override config for URL/token/tenant.
- [ ] Error UX: 401/403/404/409/429/500 map to actionable user-facing messages.
- [ ] Approval decision: `APPROVE` / `BLOCK` / `NEEDS-CHANGES`

### Feature43 Review Gate
- [ ] Scope sanity: Tasks `task234`-`task238` and tests `test332`-`test336` are present and linked.
- [ ] Bootstrap policy: one-time first-admin bootstrap works, then disables itself.
- [ ] Admin controls: only admin can create users/tenants in V1; no self-signup path.
- [ ] Tenant policy: user-chosen slug uniqueness enforced; invalid slug handling clear.
- [ ] Auth security: JWT claims/scopes, denylist, and key-rotation path are implemented.
- [ ] Session security: secure cookie flags + CSRF + server-side invalidation are implemented.
- [ ] Approval decision: `APPROVE` / `BLOCK` / `NEEDS-CHANGES`

### Feature29 Review Gate
- [ ] Scope sanity: Tasks `task239`-`task244` and tests `test337`-`test342` are present and linked.
- [ ] Storage abstraction: local/mock-s3/real-s3 backends conform to one protocol.
- [ ] Metadata contract: global index + agent index + version metadata are consistent.
- [ ] API contract: publish/list/detail/download/search routes match documented behavior.
- [ ] Security controls: auth required on reads/writes, upload limits, rate limiting, stable error envelope.
- [ ] Mock-first readiness: local dev and tests run without real AWS credentials.
- [ ] Approval decision: `APPROVE` / `BLOCK` / `NEEDS-CHANGES`

### Feature30 Review Gate
- [ ] Scope sanity: Tasks `task245`-`task248` and tests `test343`-`test346` are present and linked.
- [ ] Auth-only browsing: unauthenticated access redirects to login for UI routes.
- [ ] Session + CSRF: login/logout/session lifecycle and CSRF checks are complete.
- [ ] UI correctness: listing/search/profile/download pages render expected data.
- [ ] Download flow: UI triggers presigned URL redirect; server does not proxy binary.
- [ ] Approval decision: `APPROVE` / `BLOCK` / `NEEDS-CHANGES`

### Global Merge Gate
- [ ] Manifest check: `python3 scripts/validate_project_manifests.py` passes.
- [ ] Regression check: existing non-registry baseline tests still pass.
- [ ] Docs check: feature notes and phase notes reflect final decisions/policies.
- [ ] Security check: no secrets/tokens/passwords are logged in code paths or docs.
- [ ] Final recommendation: `READY TO IMPLEMENT` / `HOLD`
