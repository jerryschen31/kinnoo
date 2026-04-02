# Task369 Notes

## Summary
Implemented Feature79 task369 by adding deterministic pack excludes for runtime artifacts and validating roundtrip-oriented fixture contracts in both Python and Vitest tests.

## What Was Implemented
- In `src/kinnoo/pack_command.py` added deterministic excluded runtime directory parts:
  - `.git`, `.openclaw`, `node_modules`, `.pytest_cache`, `__pycache__`
- Added helpers:
  - `_is_runtime_artifact_path(relative_path)`
  - `_filter_excluded_pack_entries(entries)`
- Applied excludes across pack inputs:
  - additional files (`files`/`extra_file`)
  - asset files
  - state snapshot files
  - OpenClaw workspace files from `skills/` and `memory/`

## Test Coverage
- Added/validated Python tests:
  - `tests/test_pack_robustness.py::test_feature79_openclaw_pack_excludes_runtime_artifacts`
  - `tests/test_pack_size_reporting.py::test_feature79_openclaw_pack_size_reporting_preserved`
- Added/validated Vitest fixture contract:
  - `web/__tests__/openclaw-pack-fixtures.test.ts`
- Verifies:
  - runtime-only artifacts are excluded from OpenClaw pack archives
  - required OpenClaw workspace content still included
  - archive size reporting output remains present for OpenClaw packs
  - JS/TS fixture contract catches forbidden runtime prefixes

## Teaching Notes
- Why excludes are path-part based:
  - Checking path components instead of suffixes makes exclusion behavior deterministic and resilient to nested directory structures.
- Why keep fixture contracts in Vitest:
  - Lightweight contract tests provide quick guardrails for frontend/shared expectations without requiring full Python archive orchestration.
