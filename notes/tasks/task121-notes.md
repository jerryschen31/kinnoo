# Task121 Notes - Add inputs.required manifest field

## Scope implemented
- Added support for optional `inputs.required` in manifest schema validation.
- Preserved default behavior when `inputs.required` is omitted (legacy required-input semantics remain unchanged).
- Added associated automated tests for valid boolean values, invalid non-boolean values, and default-required run behavior.

## Files changed
- `src/kinnoo/schema.py`
- `tests/test_validator.py`
- `tests/test_cli.py`
- `TASKS.txt`

## Implementation details
- Updated schema optional field definitions:
  - Added `inputs.required` to `OPTIONAL_FIELDS`.
  - Added `"inputs.required": bool` to `OPTIONAL_FIELD_TYPES`.
- Existing validator optional-field path handling (`_get_nested` + type checks) now validates `inputs.required` automatically.
- Kept compatibility invariant: manifest files without `inputs.required` still validate and current run behavior still requires positional input by default.

## Tests implemented
- `tests/test_validator.py::test_inputs_required_boolean_values_accepted` (test167)
- `tests/test_validator.py::test_inputs_required_non_boolean_rejected` (test168)
- `tests/test_cli.py::test_run_without_input_defaults_to_required` (test169)

## Validation results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_validator.py -k "inputs_required" -q` -> `2 passed, 20 deselected`
- `python3 -m pytest tests/test_cli.py -k "run_without_input_defaults_to_required or run" -q` -> `10 passed, 1 deselected`
- `python3 -m pytest -q` -> `161 passed, 1 skipped`

## Teaching notes
- Backward-compatible schema evolution is safest when new fields are optional and type-checked only when present. This allows staged rollout without breaking existing manifests.
- A useful migration pattern is: introduce schema support first (task121), then broaden parser/runtime behavior in later tasks. This reduces blast radius and makes regressions easier to localize.
- From an AI-agent systems perspective, `inputs.required` is an interface contract field: it helps runtime orchestrators reason about whether user prompt input is mandatory or optional before tool execution.
- Interview framing tip: call this “additive schema versioning with strict optional typing,” and emphasize pairing positive + negative tests with one backward-compatibility regression test.