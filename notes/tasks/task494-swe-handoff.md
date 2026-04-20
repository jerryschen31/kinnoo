# Task494 SWE Handoff - Dependency Inference + Generic LLM Agent Support

## Objective
Improve import dependency inference for Poetry and generic LLM agent projects across Python and JS/TS without requiring framework-specific adapter selection.

## Contract
- Parse `tool.poetry.dependencies` in `pyproject.toml`.
- Merge and deduplicate dependency signals from files/imports.
- Improve generic LLM env-var/dependency inference.
- Preserve validation-clean manifest outputs.

## Primary Files
- `src/kinnoo/analyzer.py`
- `src/kinnoo/import_command.py`
- `tests/client_cli_import/test_cli_import.py`
- `tests/validator_integration/test_analyzer.py`

## Required Tests
- `test703`
- `test704`

## Execution Guidance
1. Keep dependency normalization stable and deterministic.
2. Ensure generic-agent behavior does not regress framework-specific paths.
3. Validate with targeted analyzer/import subsets.
