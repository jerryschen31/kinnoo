# Task165 - feature19 analyzer integration and confirm-first wizard

## Summary
- Integrated analyzer as the single inference backend in [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
  - Calls `analyze_project(target_path)` and consumes report via `as_dict()`
  - Surfaces detected values and analyzer warnings in import output
- Implemented confirm-first wizard behavior:
  - Shows detected value summary first
  - Prompts for proceed confirmation before any follow-up questions
  - Prompts only for unresolved/low-confidence core fields (`entrypoint`, `runtime.type`, `framework`)
- Added analyzer-to-manifest mapping for import output:
  - Uses inferred `entrypoint`, `runtime`, `dependencies`, `env_vars`, and optional `framework`
  - Preserves deterministic fallback values when inference is missing
- Added focused task165 tests in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature19_import_uses_analyzer_inference_and_warnings` (test257)
  - `test_feature19_confirm_first_wizard_prompt_minimization` (test258)
- Updated `task165` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature19_import_uses_analyzer_inference_and_warnings tests/test_cli_import.py::test_feature19_confirm_first_wizard_prompt_minimization` -> `2 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For agentic onboarding flows, keep inference and orchestration separated: analyzer computes facts; import command decides interaction policy. This improves explainability and testability.
- Confirm-first wizard design reduces user friction and cognitive load by showing a full inferred plan before asking targeted follow-ups.
- Confidence-threshold gating is a practical pattern: only ask humans to resolve uncertain fields while accepting high-confidence defaults automatically.
