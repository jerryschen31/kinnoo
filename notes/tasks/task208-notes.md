# Task208 - feature37 non-node install regression safeguards

## Summary
- Added task-linked regression guard in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature37_python_install_noop_regression_guard` (test306).
- Regression coverage validates Python install baseline remains unchanged even when feature37 Node flags are passed:
  - install succeeds with `--allow-vulnerable` and `--ignore-scripts`,
  - Node audit/lifecycle outputs are absent,
  - Node tooling probe scripts are never invoked,
  - Node install trace artifact is not created for Python runtime install,
  - installed Python agent still runs successfully.
- Updated [TASKS.txt](TASKS.txt):
  - `task208` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature37_python_install_noop_regression_guard` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Runtime-scoped security controls should be regression-guarded with explicit negative assertions ("this path must not execute") to prevent cross-runtime drift.
- Adding probe executables in test PATH is a practical way to detect accidental command-path invocation without changing production code.
- Preserve baseline behavior under new flags by proving they are parsed safely but ignored where semantically irrelevant.
