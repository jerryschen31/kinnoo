# Task339 Notes

## Summary
Implemented Feature64 requirement hinting and deterministic unresolved guidance for ClawHub imports, and surfaced provenance + hint metadata clearly in inspect output.

## What Changed
- `src/kinnoo/import_command.py`
  - Added requirement hint extraction for ClawHub mirror metadata into deterministic categories:
    - `env`
    - `config`
    - `bin`
  - Added deterministic unresolved guidance generation based on present hint categories.
  - Added operator-facing output blocks:
    - `Requirement hints:`
    - `Unresolved guidance:`
  - Extended import report artifact (`kinnoo-import-report.json`) with:
    - `requirements` object (env/config/bin)
    - deterministic `unresolved` list
    - mirror metadata passthrough

- `src/kinnoo/inspect_command.py`
  - Added explicit provenance rendering in standard inspect output when manifest includes `provenance`.
  - Added imported report rendering for directory targets via `kinnoo-import-report.json`:
    - `Imported Requirement Hints`
    - `Unresolved Guidance`

- `src/kinnoo/registry.py`
  - Extended mirror record model to retain metadata payload (`metadata`) for downstream hint generation.

- `docs/manifest-schema-reference.md`
  - Added Feature64 import guidance section for `kinnoo import --source clawhub`.
  - Documented report artifact structure and deterministic missing-slug remediation guidance.

- `tests/test_cli_import.py`
  - Added `test_feature64_clawhub_import_requirements_report` (test498).
  - Verifies hint extraction, output text, report structure, and inspect visibility of provenance/hints.

## Teaching Notes
- Separating import-time guidance into structured categories (`env`, `config`, `bin`) makes remediation scripts and docs easier to automate and maintain.
- Deterministic ordering is important for reliable regression tests and for reducing operator confusion in repeated CI runs.
- Keeping import report and inspect output aligned gives a useful two-step debugging flow: import captures what is unresolved, inspect confirms current project readiness context.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k "test_feature64_clawhub_import_requirements_report"`
- Result:
  - `1 passed, 460 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task339-smoke-tests.md`.
