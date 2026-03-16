# Task141 - feature23 schema support for mcp-server runtime type

## Summary
- Added `mcp-server` to supported runtime types in schema constants.
- Preserved validator behavior for unsupported runtime values with explicit allowed-values guidance.
- Added linked test214 coverage to verify:
  - `runtime.type: mcp-server` is accepted.
  - unknown runtime values are rejected with actionable allowed-values messaging.

## Files changed
- src/kinnoo/schema.py
- tests/test_validator.py
- TASKS.txt

## Linked tests (task141)
- test214: tests/test_validator.py::test_feature23_runtime_type_mcp_server_supported

## Test runs and results
- python3 -m pytest tests/test_validator.py::test_feature23_runtime_type_mcp_server_supported -> 1 passed
- python3 -m pytest tests/test_validator.py::test_invalid_runtime_type -> 1 passed
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- No repeated bug/error class encountered during task141 implementation.

## Teaching notes
- This is a low-risk schema evolution pattern: expand the allowed enum values while preserving strict rejection semantics for unknown values.
- Keep validator error messages dynamically tied to the source-of-truth constant list so future enum changes do not require duplicate string updates.
- Pair the new acceptance-path test (`mcp-server`) with a negative-path regression test (unknown value) to prevent accidental over-permissive validation.
