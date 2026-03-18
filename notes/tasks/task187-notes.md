# Task187 - feature33 non-openclaw compatibility and non-breaking guard

## Summary
- Added regression gate coverage for feature33 non-openclaw compatibility in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature33_non_openclaw_optional_nonbreaking_regression_gate` (test285)
  - verifies baseline Python and Node manifests remain valid when feature33 fields are omitted,
  - verifies non-openclaw manifests with valid feature33 extension fields (`runtime.package_manager`, `channels`, `skills`, `state_dirs`) remain valid,
  - verifies framework-targeted OpenClaw diagnostics do not leak into non-openclaw fixtures.
- Updated task workflow status in [TASKS.txt](TASKS.txt):
  - `task187` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature33_non_openclaw_optional_nonbreaking_regression_gate` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- A non-breaking schema extension should be validated with regression fixtures that represent both legacy and extension-enabled paths.
- Framework-specific policy should be tested with negative leakage assertions (for example: OpenClaw-only diagnostics must not appear for non-openclaw manifests).
- Regression gates are most useful when they model user-realistic manifest variants (Python baseline, Node baseline, and extension-enabled non-targeted framework cases).
