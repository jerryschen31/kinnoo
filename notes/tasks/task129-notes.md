# Task129 Notes - Feature21 regression gate for existing frameworks

## Scope implemented
- Added regression coverage proving that feature21 additions do not break existing framework template behavior for `gemini`, `chatgpt`, and `claude-chat`.
- Implemented linked test191 automation path.
- Added a regression_v1 gate test that selects under the required `framework or feature21` filter and executes legacy framework checks.

## Files changed
- `tests/test_init.py`
- `tests/test_regression_v1.py`
- `TASKS.txt`

## Implementation details
- Added `test_feature21_regression_existing_frameworks_unchanged` in `tests/test_init.py`:
  - scaffolds each legacy framework with `kinnoo init --framework ...`
  - asserts framework-specific dependency/model/env-var/run-example markers remain intact
  - validates generated manifest with the existing validator
- Added `test_feature21_framework_templates_do_not_regress_existing_frameworks` in `tests/test_regression_v1.py`:
  - runs legacy framework template tests + the new feature21 regression test as a focused gate
  - fails with full stdout/stderr context if any regression appears

## Tests implemented
- `tests/test_init.py::test_feature21_regression_existing_frameworks_unchanged` (test191)
- `tests/test_regression_v1.py::test_feature21_framework_templates_do_not_regress_existing_frameworks` (additional regression gate support)

## Validation and regression results
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `17 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `3 passed, 18 deselected`
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `1 passed, 2 deselected`
- `python3 -m pytest` -> `184 passed, 1 skipped`

## Bug/error notes
- No implementation bug or test failure required iterative fixing for task129.
- The 5-attempt cap was not reached for any bug class.

## Teaching notes
- Regression gates are strongest when they assert invariant outputs tied to user-facing behavior (deps, model hint, env-var guidance), not just pass/fail of broad suites.
- Keep one dedicated automation-path test for requirements traceability (`test191`) and optionally pair it with a broader regression gate in `test_regression_v1.py` for reviewer confidence.
- Feature expansion work should always include explicit backward-compatibility tests for pre-existing options, especially in template-driven CLIs where small changes can silently alter generated artifacts.
