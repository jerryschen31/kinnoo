# Task213 - feature38 sweep output contract and no-secret regression safeguards

## Summary
- Added task-linked regression coverage in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature38_output_format_and_secret_safety_regression_guard` (test311).
- Regression guard validates mixed-language sweep output contract remains stable across inspect and pack flows:
  - inspect warnings keep deterministic `path:line: description` structure,
  - sweep categories (env exposure, risky JS primitive, credential pattern, OpenClaw config danger) remain visible,
  - pack flow still emits warning-first memory snapshot findings and archive creation output.
- Regression guard validates no-secret-value invariant:
  - secret-like JS/JSON/snapshot values are not echoed in inspect/pack output.
- Updated [TASKS.txt](TASKS.txt):
  - `task213` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature38_output_format_and_secret_safety_regression_guard` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Output-contract regression tests should assert both structural invariants (format, categories) and safety invariants (no secret echoing).
- Mixed-path validation (inspect + pack) catches drift that single-surface tests can miss.
- Keep regression fixtures explicit and deterministic so failures point directly to contract changes rather than environmental variance.
