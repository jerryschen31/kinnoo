# Task381 Notes

## Summary
Implemented Feature85 task381 by adding deterministic runtime deprecation warnings for legacy OpenClaw bridge paths while preserving non-breaking compatibility behavior, and by annotating legacy bridge tests as deprecated-path coverage.

## What Was Implemented
- Updated `src/kinnoo/cli.py`:
  - added `_emit_bridge_path_deprecation_warning(path, replacement)` helper
  - emits deterministic deprecation warning when `kinnoo run ... --experimental-openclaw-adapter` is used
  - emits deterministic deprecation warning when `kinnoo sync clawhub` is used
  - warnings include stable category and migration replacement guidance strings
- Updated legacy test annotations:
  - `tests/test_cli.py` feature66 tests now explicitly document deprecated-path coverage intent
  - `tests/test_registry.py` feature63/feature67 tests now explicitly document deprecated-path coverage intent
- Added compatibility regression:
  - `tests/test_cli_registry_modes.py::test_feature85_deprecated_paths_warn_and_remain_compatible`

## Test Coverage
- Added/validated:
  - `tests/test_cli_registry_modes.py::test_feature85_deprecated_paths_warn_and_remain_compatible`
- Verifies:
  - legacy run path (`--experimental-openclaw-adapter`) prints deterministic deprecation warning and still executes successfully
  - legacy sync path (`sync clawhub`) prints deterministic deprecation warning and still completes successfully
  - warning output includes migration replacement commands

## Smoke Tests
- `notes/tasks/task381-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why warn in dispatch layer:
  - Emitting warnings in CLI command dispatch keeps behavior centralized and deterministic, independent of downstream command-module internals.
- Why deterministic warning fields matter:
  - Stable `category=...` and `path=...` tokens make regression tests robust and support future machine parsing of deprecation telemetry.
