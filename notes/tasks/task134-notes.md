# Task134 Notes - Feature21 optional kinnoo.yaml model metadata field

## Scope implemented
- Added optional `model` manifest metadata support with backward compatibility when omitted.
- Emitted `model` in generated `kinnoo.yaml` only for frameworks with known default underlying models.
- Added task134-linked tests for validator behavior and template-generation emission logic.

## Files changed
- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `src/kinnoo/init_command.py`
- `tests/test_validator.py`
- `tests/test_init.py`
- `TASKS.txt`

## Implementation details
- Updated optional schema metadata in `schema.py`:
  - Added optional field `model`.
  - Added optional type constraint `model: str`.
- Updated validator in `validator.py`:
  - Kept `model` optional (non-breaking when absent).
  - Added semantic check that `model`, when present, must be a non-empty string.
- Updated init emission logic in `init_command.py`:
  - Added `KNOWN_FRAMEWORK_DEFAULT_MODELS` map.
  - Appended `model: <value>` into generated `kinnoo.yaml` when framework has known default model.
  - Left `model` omitted for frameworks where default model is unknown/variable.

## Tests implemented
- `tests/test_validator.py::test_feature21_optional_model_metadata_field` (test200)
- `tests/test_init.py::test_feature21_templates_emit_optional_model_metadata_when_known` (test201)

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_validator.py::test_feature21_optional_model_metadata_field tests/test_init.py::test_feature21_templates_emit_optional_model_metadata_when_known -q` -> `2 passed`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `23 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `6 passed, 19 deselected`
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `1 passed, 2 deselected`
- `python3 -m pytest` -> skipped in this run (tool call explicitly skipped)

## Bug/error notes
- No implementation bug required fix iterations.
- 5-attempt cap was not approached.

## Teaching notes
- Optional metadata changes are safest when split into two layers: schema/type acceptance first, then emission rules that add values only when confidence is high.
- Backward compatibility means treating absence as valid and validating only when the optional field is present.
- For scaffold generators, centralize known defaults in a single map so model metadata behavior remains explicit and easy to review during framework updates.
