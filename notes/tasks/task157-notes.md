# Task157 - feature26 AC coverage and regression gate

## Summary
- Added `tests/test_regression_v1.py::test_feature26_framework_template_regression_gate` (test242).
- The regression gate executes a focused feature26 stability set to ensure adding `mcp-client` did not regress existing init framework template behavior.
- The gate also includes `tests/test_validator.py::test_feature26_permissions_schema_validation` to keep MCP permissions schema behavior in the focused regression path.
- Confirmed AC mapping for feature26 tests remains aligned in `TESTS.txt` (`test236` through `test242`).
- Updated `task157` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py -k feature26` -> `1 passed`
- `python3 -m pytest tests/test_pack.py -k feature26` -> `2 passed`
- `python3 -m pytest tests/test_init.py -k feature26` -> `2 passed`
- `python3 -m pytest tests/test_regression_v1.py -k feature26` -> `1 passed`

## Bug/error notes
- No task157 implementation or test failures were encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Regression gates should target contract boundaries, not implementation details. Here that means template generation behavior, manifest validity, and runtime I/O contract behavior.
- A focused gate can still be comprehensive when it composes existing acceptance tests (`test236`-`test241`) with one high-signal orchestrator (`test242`).
- In agentic systems, permission-policy regressions are security regressions; including schema validation in the gate reduces the chance of silently widening capability.
