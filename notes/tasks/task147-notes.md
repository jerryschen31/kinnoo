# Task147 - feature24 validator rules for services objects and duplicates

## Summary
- Implemented strict feature24 validator enforcement for `services` entries in `src/kinnoo/validator.py`.
- Added required-field checks for each service object:
  - `services[i].name`
  - `services[i].type`
- Added allowed-value checks with explicit guidance for:
  - `services[i].type` against `SUPPORTED_SERVICE_TYPES`
  - `services[i].health_check.method` against `SUPPORTED_HEALTH_CHECK_METHODS`
- Added method-specific required-field validation for declared health-check methods:
  - `tcp` -> requires `port`
  - `http` -> requires `url`
  - `process` -> requires `process_name`
- Added deterministic duplicate service-name detection across a manifest.
- Added task147-linked tests in `tests/test_validator.py`:
  - `test_feature24_service_required_fields_and_type_validation` (test223)
  - `test_feature24_health_check_method_specific_validation` (test224)
  - `test_feature24_duplicate_service_names_rejected` (test227)
- Updated task147 status to `needs-review`.

## Files changed
- src/kinnoo/validator.py
- tests/test_validator.py
- TASKS.txt

## Linked tests (task147)
- test223: tests/test_validator.py::test_feature24_service_required_fields_and_type_validation
- test224: tests/test_validator.py::test_feature24_health_check_method_specific_validation
- test227: tests/test_validator.py::test_feature24_duplicate_service_names_rejected

## Test runs and results
- python3 -m pytest tests/test_validator.py::test_feature24_service_required_fields_and_type_validation tests/test_validator.py::test_feature24_health_check_method_specific_validation tests/test_validator.py::test_feature24_duplicate_service_names_rejected -> 3 passed
- python3 scripts/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- No repeated bug/error class encountered during task147 implementation.

## Teaching notes
- Good validator design separates concerns: shape/type safety first, then semantic constraints (allowed enums, conditional requirements, uniqueness).
- Deterministic error ordering matters for reliable tests and easier debugging. Sorting duplicate-name reports removes flaky failure output.
- Conditional schema rules are best expressed as explicit implication checks (for example, if method is `tcp`, then `port` must exist), which mirrors logic frequently used in production policy engines and interview design questions.
