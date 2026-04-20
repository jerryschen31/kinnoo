# Task491 SWE Handoff - Import Core Error Hardening and Validation Gate

## Objective
Harden the base `kinnoo import` command path so edge-case inputs are deterministic, generated manifests are validated before final success, and all import failure paths use consistent actionable messaging.

## Contract
- Handle empty, unsupported-language, ambiguous-structure, and large-project inputs without traceback.
- Validate generated kinnoo.yaml before final success messaging.
- Keep failure output concise and actionable with consistent formatting.

## Primary Files
- `src/kinnoo/import_command.py`
- `src/kinnoo/analyzer.py`
- `src/kinnoo/validator.py`
- `tests/client_cli_import/test_cli_import.py`

## Required Tests
- `test696`
- `test697`
- `test698`

## Execution Guidance
1. Implement guardrails first, then run validation gate checks.
2. Keep behavior backward compatible for successful imports.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest tests/client_cli_import/test_cli_import.py -q -k "feature117"`
