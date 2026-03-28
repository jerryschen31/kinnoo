# Feature 56 Smoke Tests - Auth Fallback, Admin Bootstrap, and Local Publish Path

## 1) Bearer-first then session-cookie fallback
1. Call JSON API route with Bearer token only.
2. Call with session cookie only.
3. Call with neither.

Pass if:
- First two authorize; third fails.

## 2) Local admin bootstrap
1. Set REGISTRY_ADMIN_EMAIL and REGISTRY_ADMIN_PASSWORD in environment.
2. Start backend bootstrap path.
3. Repeat startup.

Pass if:
- Admin account exists and bootstrap is idempotent.
- No secret values are printed.

## 3) Local publish tenant path
1. Publish a test agent locally.
2. Inspect mocked S3 storage tree.

Pass if:
- Artifact and metadata are in tenant-scoped folder.

## 4) Prefix-scoped storage compatibility
1. Verify resulting paths follow existing prefix conventions.
2. Confirm behavior still works for search/list/install flows.

Pass if:
- Storage layout remains compatible with existing backend logic.

## 5) Integration regression run
1. Run feature56 integration tests.

Pass if:
- Fallback auth, admin bootstrap, and publish path tests all pass.
