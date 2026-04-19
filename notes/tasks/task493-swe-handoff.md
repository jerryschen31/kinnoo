# Task493 SWE Handoff - OpenClaw `--from` Workspace Import Flow

## Objective
Implement the workspace import flow `kinnoo import --from openclaw <target> <workspace-path>` with deterministic include/exclude copy behavior and validated manifest generation.

## Contract
- Copy required workspace content (SOUL.md, IDENTITY.md, memory/, skills/, and relevant agent files).
- Exclude `.git/`, `.openclaw/`, `.clawhub/`, `node_modules/`, `.venv/`.
- Generate and validate `kinnoo.yaml` in target with `framework: openclaw`.
- Emit deterministic error for invalid workspace sources.

## Primary Files
- `src/kinnoo/import_command.py`
- `src/kinnoo/analyzer.py`
- `src/kinnoo/cli.py`
- `tests/client_cli_import/test_cli_import.py`

## Required Tests
- `test702`

## Execution Guidance
1. Add parser/argument validation before copy execution.
2. Keep source/target path handling robust for relative and absolute paths.
3. Validate output manifest before success return.
