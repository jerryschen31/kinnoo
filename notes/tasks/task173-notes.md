# Task173 - feature31 python runtime regression gate

## Summary
- Implemented test269 regression gate in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - Added `test_feature31_python_runtime_regression_gate`.
  - Gate performs an end-to-end Python workflow using script-path CLI invocation:
    - `pack` a Python agent fixture
    - `install` the generated `.kno` into a target directory
    - `run` the installed Python agent and assert expected output/exit semantics
- Regression gate intentionally uses a Python runtime fixture with empty requirements to keep execution deterministic and independent from Node-specific flows introduced in feature31.
- Updated `task173` status to `needs-review` in [TASKS.txt](TASKS.txt).

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature31_python_runtime_regression_gate` -> `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For parity gates, end-to-end behavior checks are stronger than isolated unit assertions because they verify cross-command contracts (`pack -> install -> run`) as users actually experience them.
- When validating regression safety against a new runtime feature, prefer fixtures that isolate the old runtime path (here: Python) so failures clearly indicate parity breaks rather than mixed-runtime complexity.
- Keep regression tests deterministic by minimizing external dependencies (empty requirements, controlled temp directories, explicit archive root), which improves reliability in CI and local dev environments.
