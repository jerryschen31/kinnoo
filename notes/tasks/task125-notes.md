# Task125 Notes - Feature20 merge-fix for required-input enforcement and run usage guidance

## Scope implemented
- Fixed feature20 contract mismatch where required input could be bypassed by pass-through args.
- Updated run usage/error guidance to reflect all supported feature20 invocation modes.
- Added focused regression tests for both issues and linked them in manifests.

## Files changed
- `src/kinnoo/run_command.py`
- `src/kinnoo/cli.py`
- `tests/test_cli.py`
- `TASKS.txt`
- `TESTS.txt`
- `FEATURES.txt`

## Implementation details
- Enforced strict required-input contract in runtime:
  - In `run_command.py`, run now rejects when `inputs.required` is true and positional input is missing, regardless of pass-through args.
- Updated run usage text in CLI:
  - Added shared run usage text that includes legacy single-input mode, no-input mode, and pass-through mode.
  - Replaced legacy-only usage output in missing-args paths with the expanded guidance.

## Tests implemented
- `tests/test_cli.py::test_run_required_input_cannot_be_bypassed_by_pass_through` (test178)
- `tests/test_cli.py::test_run_usage_includes_feature20_modes` (test179)

## Validation and regression results
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_validator.py -k "inputs_required" -q` -> `2 passed`
- `python3 -m pytest tests/test_cli.py -k "run" -q` -> `17 passed, 1 deselected`
- `python3 -m pytest tests/test_input_guard_integration.py -q` -> `6 passed`
- `python3 -m pytest tests/test_install.py tests/test_regression_v1.py::test_feature20_does_not_regress_v2_behavior -q` -> `2 passed`
- `python3 -m pytest -q` -> `171 passed, 1 skipped`

## Bug encountered and fix
- Encountered one YAML parsing issue in `TESTS.txt` due to an unquoted colon in a preconditions string.
- Fixed by quoting the preconditions value for test178.
- Fix attempts for this bug class: 1 (resolved, below the 5-attempt threshold).

## Teaching notes
- Contract enforcement belongs at runtime boundaries, not just parser boundaries. Here, enforcing `inputs.required` in `run_command` prevents mode-specific bypasses.
- For CLI UX, usage text should evolve alongside feature capability; otherwise, users get valid behavior but invalid guidance.
- Regression tests should target contract breakpoints directly:
  - one negative-path test for bypass attempts,
  - one guidance test for user-facing invocation patterns.
- In agent platforms, pairing behavior fixes with user-guidance fixes reduces both security risk and operator confusion.