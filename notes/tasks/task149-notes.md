# Task149 - feature24 AC coverage and regression gate

## Summary
- Implemented a focused feature24 regression gate in `tests/test_regression_v1.py`:
  - `test_feature24_ac_coverage_and_no_services_regression_gate`
- The gate executes the full feature24 AC-mapped test set (`test222`-`test227`) in one run path, including no-services compatibility checks.
- Confirmed task149 expectations:
  - focused validator/inspect coverage is exercised together
  - manifests without `services` remain behaviorally unchanged via `test225`
- Updated task149 status to `needs-review`.

## Files changed
- tests/test_regression_v1.py
- TASKS.txt

## Linked tests (task149)
- test222: tests/test_validator.py::test_feature24_services_optional_list_is_accepted
- test223: tests/test_validator.py::test_feature24_service_required_fields_and_type_validation
- test224: tests/test_validator.py::test_feature24_health_check_method_specific_validation
- test225: tests/test_validator.py::test_feature24_no_services_regression_unchanged
- test226: tests/test_cli_inspect.py::test_feature24_inspect_displays_services
- test227: tests/test_validator.py::test_feature24_duplicate_service_names_rejected

## Test runs and results
- python3 -m pytest tests/test_regression_v1.py::test_feature24_ac_coverage_and_no_services_regression_gate -> 1 passed
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- No repeated bug/error class encountered during task149 implementation.

## Teaching notes
- A regression gate test is most useful when it composes a feature’s acceptance tests into one deterministic command path; this catches integration drift while keeping runtime low.
- For schema-heavy features, including both strict validation tests and backward-compatibility tests in the same gate prevents “correct but breaking” changes.
- This pattern mirrors production release checks: run a compact, high-signal canary suite before broader regression to get fast confidence and isolate failures quickly.
