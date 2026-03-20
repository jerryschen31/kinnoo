# Task186 - feature33 framework openclaw targeted validation rules

## Summary
- Added framework-targeted OpenClaw validation branch in [src/kinnoo/validator.py](src/kinnoo/validator.py):
  - Rules execute only when `framework: openclaw`.
  - Enforces OpenClaw-specific runtime guidance:
    - `runtime.language` must be `nodejs`
    - `runtime.type` must be `daemon`
    - `runtime.package_manager` is required and constrained to `npm` or `pnpm`
    - `channels` must include `stdio`
  - Emits deterministic, framework-targeted diagnostics that explicitly reference OpenClaw expectations.
- Added task-linked automated coverage in [tests/test_validator.py](tests/test_validator.py):
  - `test_feature33_openclaw_framework_specific_validation` (test284)
  - Covers valid OpenClaw fixture, invalid OpenClaw fixture (framework-targeted failures), and non-OpenClaw control fixture to verify gating.
- Updated task status in [TASKS.txt](TASKS.txt):
  - `task186` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature33_openclaw_framework_specific_validation` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Framework-specific validation should be additive and gated: generic schema rules remain reusable, while framework constraints run only in the relevant context.
- A strong targeted test includes three fixtures:
  1. valid targeted-framework fixture,
  2. invalid targeted-framework fixture asserting framework-specific diagnostics,
  3. non-targeted control fixture proving no cross-framework leakage.
- Diagnostic quality matters as much as pass/fail outcomes: include concrete expected values in errors so operators can fix manifests quickly.
