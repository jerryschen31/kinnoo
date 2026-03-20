# Feature29 Notes

## Intent
Feature29 delivers the remote registry server with secure multi-tenant API behavior, storage abstraction, and JSON metadata indexing.

## Scope Implemented in Planning
- Updated feature definition and ACs in `FEATURES.txt`
- Added tasks `task239`-`task244`
- Added tests `test337`-`test342`

## Core Architecture
- Server framework: FastAPI in `server/`
- Storage abstraction:
  - Local filesystem backend
  - Mock S3 backend (moto)
  - Real S3/MinIO backend
- Metadata model:
  - global index
  - per-agent index
  - per-version metadata
- Namespace: `tenant_slug/agent_slug/version`
- Auth: JWT required for all API reads/writes in V1

## Task-by-Task Implementation Guidance

### task239
- Scaffold server package and startup entrypoint.
- Define `StorageBackend` protocol with read/write/list/delete/presign methods.
- Implement backend factory selected by `REGISTRY_STORAGE_BACKEND`.
- Ensure local and mock backends support identical key semantics.

### task240
- Implement strongly typed metadata models and manager.
- Treat version metadata as source of truth.
- Keep global/agent indexes synchronized on publish and soft-delete operations.
- Include schema version fields in payload and filenames.

### task241
- Publish endpoint responsibilities:
  - archive validation
  - SHA256 recompute server-side
  - duplicate version guard (409)
  - object write to canonical path
  - metadata update in all tiers
- Enforce upload size and authenticated publish scope.

### task242
- `GET /api/agents`: paginated list with optional tenant filter.
- `GET /api/agents/{tenant}/{agent}`: version history/detail.
- Always require valid auth token and enforce visibility rules.

### task243
- Generate presigned URLs from storage backend.
- Do not proxy binaries through API server.
- Validate version existence from metadata before presign.

### task244
- Search over name/description with paging.
- Add auth middleware and route scope checks.
- Add rate limiting to auth and publish endpoints.

## Test Strategy
- `test337`: backend protocol parity across implementations
- `test338`: metadata consistency and schema versioning
- `test339`: publish happy/error paths
- `test340`: list/detail auth + visibility + pagination
- `test341`: presign endpoint behavior
- `test342`: search behavior and access filtering

## Security Notes for SWE
- Never log token values, passwords, signing keys, or raw secrets.
- Keep JWT scope checks close to route definitions.
- Treat denylist and key-rotation paths as first-class test cases.
- Enforce consistent error envelope shape across all routes.

## SWE Risks
- Metadata index drift on concurrent updates
- Backend differences causing environment-specific bugs
- Incomplete auth checks on read endpoints

## SWE Done Checklist
- Full server tests pass in local + mock S3 mode
- Endpoint contract and error schema documented
- Storage backend switch is config-only, no code changes needed

## Tech Lead Review 1

### Review Scope and Evidence
- Checked feature/task/test linkage for `feature29` and `task239`-`task244` with mapped tests `test337`-`test342`.
- Reviewed server implementation in storage, metadata, and route modules.
- Executed requested gates:
  - `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
  - `python3 -m pytest --testmon` -> failed during collection (missing `fastapi`/`starlette` in current environment)
  - Sensitive-data scan across `server/` with credential/token/key patterns
  - Large-file audit across repository and git-tracked files

### Feature29 Review Gate
- [x] Scope sanity: Tasks `task239`-`task244` and tests `test337`-`test342` are present and linked.
- [x] Storage abstraction: local/mock/s3 adapters conform to one protocol and are backend-config selectable.
- [x] Metadata contract: three-tier metadata model is implemented and synchronized on publish.
- [ ] API contract: **not fully met**.
- [ ] Security controls: **partially met**.
- [ ] Mock-first readiness: **not yet proven in this environment**.
- [x] Approval decision: `BLOCK`.

### Blocking Findings
1. Missing `POST /api/auth/token` FastAPI route integration.
  - `server/app.py` wires publish/list/detail/download/search routers but does not include an auth-token router.
  - A handler exists only as a plain function (`server/api/endpoints.py::post_auth_token`).
  - This leaves the configured rate-limit rule for `/api/auth/token` effectively unexercised.
2. AC7 error-envelope contract is not implemented.
  - Feature29 AC7 requires JSON error bodies with `error.code`, `error.message`, and `error.request_id`.
  - Current route wrappers raise `HTTPException(..., detail=<string>)`, e.g. in publish/agents/download/search routes.
  - Tests also assert status behavior but do not validate the required structured envelope.
3. `GET /api/agents` response shape is incomplete against AC4.
  - AC4 expects metadata including description/author/archive size.
  - Current list payload includes tenant, slug, visibility, latest version, and updated-at only.
4. Required regression gate command did not pass in current review environment.
  - `python3 -m pytest --testmon` failed collection for server tests due missing FastAPI/Starlette runtime dependencies.
  - Merge approval is blocked until requested regression command succeeds in the target review environment.

### Security and Repository Hygiene
- Sensitive-data scan findings were expected auth-domain identifiers and test fixtures only; no hardcoded real tokens, credentials, or private keys were identified in `server/`.
- Repository-wide large-file scan found >10 MB files under `scratch/` virtualenv/test artifacts.
- Git-tracked file audit found **no tracked files >10 MB**.

### Recommended Improvements Before Re-Review
1. Add and wire an auth router exposing `POST /api/auth/token` (and ensure rate-limit coverage for auth + publish paths).
2. Introduce a shared error-envelope builder and return AC7-compliant `{error: {code, message, request_id}}` bodies across all feature29 endpoints.
3. Extend `/api/agents` metadata response to include AC4-required fields (description, author, archive size) and update tests accordingly.
4. Ensure review environment installs `server/requirements.txt` (or equivalent test dependencies) so `python3 -m pytest --testmon` passes.
5. Add explicit tests for rate-limit behavior on `/api/publish` and `/api/auth/token` plus AC7 envelope shape assertions.

### Verdict
- `BLOCK` for merge to `phase3/main` until blockers above are remediated and regression gate passes.
