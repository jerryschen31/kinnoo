# Task211 - feature38 OpenClaw config danger rule set

## Summary
- Updated [src/kinnoo/code_sweep.py](src/kinnoo/code_sweep.py):
  - Added targeted OpenClaw JSON danger signatures for risky settings such as `allow_shell=true`, `disable_sandbox=true`, `allow_unsafe_eval=true`, `auto_approve=true`, `network_access=unrestricted`, and `tool_policy=allow_all`.
  - Added candidate filtering for relevant OpenClaw JSON artifacts to reduce unrelated noise.
  - Preserved warning-first file/line output format with actionable descriptions.
- Added task-linked integration test in [tests/test_trust_baseline.py](tests/test_trust_baseline.py):
  - `test_feature38_openclaw_config_dangerous_settings_warning` (test309),
  - validates dangerous fixture emits targeted warnings,
  - validates safe fixture avoids dangerous-config warnings.
- Updated [TASKS.txt](TASKS.txt):
  - `task211` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_trust_baseline.py::test_feature38_openclaw_config_dangerous_settings_warning` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Config-focused security checks should use explicit key/value danger states rather than broad keyword matching to reduce false positives.
- Candidate pre-filtering (file naming and content markers) improves sweep precision without sacrificing detection of intended targets.
- Preserve deterministic warning strings so findings remain stable for automation and regression tests.
