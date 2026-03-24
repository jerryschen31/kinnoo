# Task145 - feature23 regression gate for one-shot runtime

## Summary
- Implemented the task145-linked regression gate test required by `test220`.
- Added `tests/test_regression_v1.py::test_feature23_no_regression_for_one_shot_runtime` to verify one-shot behavior remains stable after introducing mcp-server runtime mode.
- The regression gate runs a focused subset of one-shot assertions covering input propagation, streaming behavior, exit-code propagation, backward-compatible single-input path, and one-shot trace safety fields.
- Updated task145 status to `needs-review`.

## Files changed
- tests/test_regression_v1.py
- TASKS.txt

## Linked tests (task145)
- test220: tests/test_regression_v1.py::test_feature23_no_regression_for_one_shot_runtime

## Test runs and results
- python3 -m pytest tests/test_regression_v1.py::test_feature23_no_regression_for_one_shot_runtime -> 1 passed
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- No repeated bug/error class encountered during task145 implementation.

## Teaching notes
- Regression gates should test behavior contracts rather than internal implementation details; this keeps tests resilient while still protecting critical runtime semantics.
- For agent runtimes, backward-compatibility checks are strongest when they cover both user-facing outputs (stdout/stderr and exit codes) and observability artifacts (trace log schema invariants).
- Focused regression subsets can provide high confidence quickly when they are intentionally mapped to acceptance criteria and known risk surfaces.
