# Task203 - feature36 non-openclaw regression safeguards

## Summary
- Added test301 regression coverage in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature36_non_openclaw_import_regression_guard`
- Regression guard validates non-OpenClaw behavior remains stable across three representative paths:
  - Python non-OpenClaw project remains classified as `chatgpt` and not misclassified as `openclaw`.
  - Generic Node project without OpenClaw markers remains non-OpenClaw and still imports with warning-first guidance.
  - Ambiguous non-OpenClaw Python signals surface actionable warning text while avoiding OpenClaw misclassification.
- Updated [TASKS.txt](TASKS.txt):
  - `task203` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature36_non_openclaw_import_regression_guard` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Regression tests are strongest when they include both positive stability checks and anti-regression negatives (for example, asserting what must *not* happen, such as OpenClaw misclassification).
- For inference systems, include ambiguous fixtures in regression gates so warning-first behavior remains stable over time.
- Keep regression fixtures realistic but minimal; this reduces flakiness and makes failures easier to diagnose quickly.
