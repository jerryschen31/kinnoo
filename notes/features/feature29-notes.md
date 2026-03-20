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
