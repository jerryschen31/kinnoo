# Feature 56 SWE Handoff - API Auth Compatibility, Local Admin Bootstrap, and Mocked S3 Publish Path

## Scope
- Feature: feature56
- Tasks: task311, task312, task313, task314
- Tests: test459, test460, test461, test462
- Depends on: feature55

## Goal
Improve backend compatibility and local testability:
1. Bearer-first + session-cookie fallback on JSON API auth.
2. Local admin bootstrap via environment variables.
3. Ensure local kinnoo publish writes tenant-scoped mocked S3 paths.

## Task details

### task311 - Middleware fallback auth
Implement in:
- server/auth/middleware.py
- server/routes/api.py

Requirements:
- Keep Bearer token as primary path.
- Add session cookie fallback when Bearer missing.
- Cover /api/agents, /api/agents/{tenant_slug}/{agent_slug}, /api/search.

### task312 - Admin bootstrap
Implement in:
- server/bootstrap.py
- server/config.py
- server/auth/services.py

Requirements:
- Read REGISTRY_ADMIN_EMAIL and REGISTRY_ADMIN_PASSWORD from environment.
- Ensure admin account exists idempotently.
- Never log or expose secret values.

### task313 - Local publish tenant path
Implement in:
- src/kinnoo/publish_command.py
- server/storage/s3_backend.py
- server/metadata/manager.py

Requirements:
- Local publish writes artifacts into tenant-scoped mocked S3 folder.
- Keep path conventions aligned with existing prefix-scoped logic.
- Keep easy migration path to real S3 later.

### task314 - Integration tests
Implement in:
- tests/test_registry.py
- tests/test_cli_registry.py
- tests/test_cli_registry_modes.py

Requirements:
- Validate fallback auth behavior.
- Validate admin bootstrap and no secret leakage.
- Validate tenant-scoped local publish path.

## Acceptance criteria mapping
- AC1 -> test459
- AC2 -> test460
- AC3 -> test461
- AC4 -> test461
- AC5 -> test462
- AC6 -> test460

## Notes
- Do not print secret values in test failures or logs.
- Reuse existing storage/auth primitives instead of re-architecting.
