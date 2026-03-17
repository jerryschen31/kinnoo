# Task167 - feature19 interruption safety and in-place runnability gate

## Summary
- Implemented interruption-safe import wizard behavior in [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
  - Added `ImportWizardInterrupted` and explicit handling for `EOFError`/`KeyboardInterrupt` during wizard prompts.
  - Import now exits non-zero on Ctrl+C/EOF with a stable user-facing interruption message.
  - Added cleanup guarantees so interrupted flows leave no partial artifacts (`kinnoo.yaml`, optional wrapper).
- Hardened rollback semantics:
  - If optional wrapper is generated but manifest write fails/collides, wrapper artifact is also cleaned up.
- Added task167 scoped tests in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature19_interrupt_cleanup_and_exit_code` (test261)
  - `test_feature19_imported_project_runs_in_place` (test262)
- Added feature19 regression gate wiring in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature19_import_interrupt_and_runnability_regression_gate`
- Updated `task167` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature19_interrupt_cleanup_and_exit_code tests/test_cli_import.py::test_feature19_imported_project_runs_in_place` -> `2 passed`

## Bug/error notes
- Encountered one failing test scenario during task262 due interruption-safe prompt behavior requiring complete scripted inputs for all unresolved prompt fields.
- Fixes applied:
  - Added explicit blank responses for optional framework and services prompts in task262 scripted input stream.
- Same bug/error class fix attempts: `2`.

## Teaching notes
- Interactive CLI flows become more robust when interruption (`Ctrl+C`, `EOF`) is modeled as a first-class control path rather than a generic exception.
- For migration/onboarding commands that can generate multiple artifacts, cleanup should be transaction-like: if final commit fails, remove intermediate artifacts too.
- Integration tests for interactive CLIs should treat prompt transcripts as contracts; when prompt policy changes, update scripted input streams intentionally rather than relying on implicit EOF fallbacks.

## TechLead review remediation
- Addressed automation-safety for non-interactive stdin:
  - EOF now follows defaults in non-interactive mode so CI/test harnesses can run import deterministically without scripted answers.
- Addressed prompt minimization regression:
  - Empty inferred list values (notably `services: []`) no longer force follow-up prompts.
- Addressed collision preflight UX:
  - Existing `kinnoo.yaml` is now checked before wizard prompts and returns immediate actionable error.
- Implemented explicit override path for AC7:
  - Added `kinnoo import [path] --force` to explicitly override an existing manifest.
- Narrowed optional wrapper prompt behavior:
  - Wrapper offer now appears only for true entrypoint contract mismatch warnings, not missing-entrypoint warnings.

## Verification after remediation
- `python3 -m pytest tests/test_cli_import.py` -> `11 passed`
