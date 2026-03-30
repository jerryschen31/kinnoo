# Task335 Notes

## Summary
Implemented Feature62 migration coverage by adding validator fixture matrix tests, an import-path regression for deterministic legacy-field/provenance errors, and a docs consistency test that validates canonical YAML examples directly.

## What Changed
- `tests/test_validator.py`
  - Added `test_feature62_openclaw_skill_schema_fixture_matrix`.
  - Added positive fixtures for canonical provenance shapes:
    - slug-only (`source_slug` + required fields)
    - url-only (`source_url` + required fields)
  - Added negative fixtures for:
    - missing `provenance.source_version`
    - disallowed metadata fields (`channels`, `skills`, `state_dirs`) with deterministic guidance assertions.

- `tests/test_cli_import.py`
  - Added `test_feature62_import_openclaw_manifest_migration_guidance`.
  - Verifies OpenClaw import emits `type: openclaw-skill` and omits disallowed metadata fields.
  - Injects invalid migration state (`provenance` missing slug/url + `state_dirs`) and validates deterministic inspect-time errors.

- `tests/test_docs.py`
  - Added `test_feature62_openclaw_schema_docs_consistency`.
  - Verifies Feature62 docs section includes required provenance contract language and minimal metadata guidance.
  - Parses Feature62 YAML examples from docs and validates each example via `validate_manifest_data` to prevent docs/schema drift.

## Teaching Notes
- Migration-safe schema evolution works best when you pair:
  1. validator fixture matrices (positive + negative),
  2. end-to-end CLI path checks (import -> inspect/validate), and
  3. docs assertions that execute examples as test fixtures.
- The docs-as-fixtures approach is valuable in interviews and production systems because it prevents “correct docs, broken runtime” drift.
- Deterministic error strings are part of the contract: they make migration tooling and user remediation automation reliable.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k "feature62_openclaw_skill_schema_fixture_matrix or feature62_import_openclaw_manifest_migration_guidance or feature62_openclaw_schema_docs_consistency"`
- Result:
  - `3 passed, 454 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task335-smoke-tests.md`.
