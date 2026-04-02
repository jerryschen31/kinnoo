# Task366 Notes

## Summary
Implemented Feature78 task366 by adding deterministic OpenClaw workspace-candidate detection and importing through the OpenClaw preflight gate before continuing import analysis.

## What Was Implemented
- Added `_is_openclaw_workspace_candidate(target_path)` in `src/kinnoo/import_command.py`.
- Candidate detection now checks strong OpenClaw signals:
  - `openclaw.json`
  - `AGENTS.md`
  - `SOUL.md`
- Added fallback signal pair detection:
  - `skills/` directory
  - `memory/` directory
- Added conditional preflight in import flow:
  - if target looks like OpenClaw, run `run_openclaw_preflight_for_command("import")`
  - fail fast with deterministic error text on preflight failure.

## Test Coverage
- Added/validated:
  - `tests/test_cli_import.py::test_feature78_import_detection_manifest_and_error_paths`
- Verifies:
  - OpenClaw-like workspace import succeeds and writes `kinnoo.yaml`
  - generated manifest contains OpenClaw framework/runtime fields
  - missing target path returns deterministic error
  - non-directory target returns deterministic error

## Teaching Notes
- Why candidate gating is conditional:
  - Import should remain generic for non-OpenClaw projects while still enforcing OpenClaw safety requirements when signals are present.
- Why deterministic errors matter:
  - Stable wording makes CLI behavior easier for users to understand and straightforward to assert in regression tests.
