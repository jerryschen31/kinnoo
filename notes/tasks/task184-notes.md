# Task184 - feature33 runtime.package_manager schema and validator support

## Summary
- Extended manifest schema support in `src/kinnoo/schema.py`:
  - Added optional field `runtime.package_manager` to schema optional fields.
  - Added type contract for `runtime.package_manager` as `str`.
- Extended validator behavior in `src/kinnoo/validator.py`:
  - Added semantic validation for `runtime.package_manager`.
  - Accepted values are constrained to `npm` and `pnpm`.
  - Unsupported values return deterministic, actionable error guidance listing supported values.
- Added task-linked automated coverage in `tests/test_validator.py`:
  - Added `test_feature33_runtime_package_manager_validation` (test282).
  - Verifies valid `npm` and `pnpm` values pass.
  - Verifies unsupported values fail with explicit guidance.
- Updated `TASKS.txt`:
  - `task184` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature33_runtime_package_manager_validation` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Optional manifest fields should be introduced in two layers:
  1. Schema/type acceptance layer (field exists + expected type).
  2. Semantic constraints layer (allowed values and business rules).
- Keeping allowed-value sets centralized (here in schema constants) improves consistency and avoids drift between validation and runtime behavior.
- Targeted regression tests for a single acceptance criterion should include both:
  - positive controls (supported values), and
  - a negative control (unsupported value with explicit error guidance).
