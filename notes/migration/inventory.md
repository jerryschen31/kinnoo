# Public/Private inventory (Stage 0)

This is the Stage 0 first-pass inventory for issue #394.

## Top-level classification

- **Public**: `src/kinnoo/`, `web/`, `docs/`, selected `tests/` (CLI/frontend-oriented), selected `scripts/`, selected root metadata/docs files, selected `.github/workflows/`
- **Private**: `server/`, `iac/`, `lambda_handler.py`, `Dockerfile`, `Dockerfile.lambda`, `docker-compose.yml`, `notes/` (except migration planning artifacts), infra/auth deployment scripts and workflows with private deployment concerns
- **Split**: `tests/`, `scripts/`, `.github/workflows/`, manifest files (`FEATURES.txt`, `TASKS.txt`, `TESTS.txt`)

## First-pass manifest visibility counts

- Features: 18 public / 104 private
- Tasks: 172 public / 358 private
- Tests: 78 public / 675 private

## Explicit deprecations (public migration scope)

Per user guidance, these are set to private for migration and are not copied into `mock-public/`:

- `web/__tests__/wrangler-prod-config.test.ts`
- `tests/e2e_workflows/test_web_frontend_setup.py`

## Notes migration sanity-check guidance

Candidate migration for `notes/features/feature*-*.md` and `notes/tasks/task*-*.md` is based on first-pass public feature/task IDs.
Before copying any note to public, run a manual scrub for:

1. Private infra references (AWS account IDs, Terraform state/bucket names, internal hostnames)
2. Secrets/token examples
3. Internal-only operational runbooks
4. Backend/server implementation details that should remain private

A candidate list is generated in `notes/migration/public-notes-candidates.md`.
