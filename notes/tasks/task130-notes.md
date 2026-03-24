# Task130 Notes - Feature21 dependency compatibility pinning update

## Scope implemented
- Replaced broad pre-1.0 placeholder constraints with tighter tested compatibility ranges for feature21 frameworks.
- Added test coverage for AC4 policy enforcement and policy/implementation alignment.

## Files changed
- `src/kinnoo/templates.py`
- `tests/test_init.py`
- `TASKS.txt`

## Implementation details
- Updated framework requirements template constants:
  - `pydantic-ai>=0.0,<0.1`
  - `langgraph>=0.2,<0.3`
  - `openai-agents>=0.1,<0.2`
- Added policy helper tests in `tests/test_init.py`:
  - `_feature21_tested_compatibility_targets()`
  - `_satisfies_feature21_dependency_policy()`
- Added task130-linked tests:
  - `test_feature21_requirements_tested_compatibility_ranges` (test192)
  - `test_feature21_dependency_policy_alignment` (test193)

## Tests implemented
- `tests/test_init.py::test_feature21_requirements_tested_compatibility_ranges` (test192)
- `tests/test_init.py::test_feature21_dependency_policy_alignment` (test193)

## Validation and regression results
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `19 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `3 passed, 19 deselected`
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `1 passed, 2 deselected`
- `python3 -m pytest` -> skipped in this run (tool path was explicitly skipped)

## Bug/error notes
- No implementation bug required fix iterations.
- 5-attempt cap was not approached.

## Teaching notes
- Version policies should be encoded as tests, not comments only; helper policy validators reduce silent drift over time.
- For pre-1.0 dependencies, narrowing to tested bounded ranges (or exact pins) is safer than broad `<1.0` constraints because minor bumps can include breaking changes.
- Keep requirement policy checks close to template-generation tests so policy changes fail fast during scaffold-related refactors.
