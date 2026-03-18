# Task178 - feature32 daemon runtime schema and validation

## Summary
- Implemented schema support for daemon runtime mode:
	- Updated `src/kinnoo/schema.py` to include `daemon` in `SUPPORTED_RUNTIME_TYPES`.
- Added focused validator coverage for Feature32 AC1 in `tests/test_validator.py`:
	- `test_feature32_runtime_type_daemon_validation` (test276)
	- Verifies `runtime.type` accepts `daemon`, `one-shot`, and `mcp-server`.
	- Verifies unsupported runtime values fail with actionable allowed-values guidance.
- Updated `TASKS.txt`:
	- `task178` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature32_runtime_type_daemon_validation` -> `1 passed`

## Bug/error notes
- No implementation/test bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Schema-first expansion pattern:
	- Adding a new runtime mode should start with central schema constants (`SUPPORTED_RUNTIME_TYPES`) and then be verified through validator tests before runtime behavior changes. This isolates contract expansion from execution semantics and reduces regression risk.
- Compatibility guardrail:
	- A good acceptance test for schema extension should validate both the new value and existing accepted values in one place; this catches accidental regressions in legacy support while introducing new capability.
- Error-message quality:
	- For operator-facing validators, “unsupported value + explicit allowed values” is a strong pattern because it turns failures into immediate remediation guidance.
