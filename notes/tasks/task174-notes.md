# Task174 - feature42 schema and validator support for json input/output types

## Summary
- Implemented feature42 task174 support for manifest I/O type validation:
  - Added supported I/O type constants in `src/kinnoo/schema.py`:
    - `SUPPORTED_INPUT_TYPES = ["text", "string", "file", "json"]`
    - `SUPPORTED_OUTPUT_TYPES = ["text", "string", "file", "json"]`
  - Added semantic validator checks in `src/kinnoo/validator.py`:
    - `inputs.type` and `outputs.type` values are now validated against explicit allow-lists.
    - Unsupported values now produce deterministic, actionable errors that name the offending field and list supported values.
- Added task-specific tests in `tests/test_validator.py`:
  - `test_feature42_manifest_accepts_json_input_output_types` (test270)
  - `test_feature42_manifest_rejects_unsupported_io_types` (test271)
- Updated `task174` status in `TASKS.txt` to `needs-review`.

## Tests and results
- Ran scoped task174 regression slice only:
  - `python3 -m pytest tests/test_validator.py::test_feature42_manifest_accepts_json_input_output_types tests/test_validator.py::test_feature42_manifest_rejects_unsupported_io_types tests/test_validator.py::test_valid_manifest_passes tests/test_validator.py::test_type_field_normalization`
  - Result: `9 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Schema evolution pattern: define allowed values once in schema constants, then consume those constants in the validator. This avoids drift between docs, validation logic, and future CLI/runtime checks.
- Backward compatibility strategy: when introducing stricter semantic validation, include legacy aliases (`text` and `string`) that are already present in existing manifests/default injection logic.
- Validation UX principle: error messages should be specific enough to answer three questions immediately:
  - what field failed,
  - what value was rejected,
  - what values are allowed.
  This reduces triage time and makes manifest fixes straightforward.
