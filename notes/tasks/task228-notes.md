# Task228 - feature41 feature39 integration and graceful degradation

## Summary
- Added feature39/feature41 monitor policy integration in src/kinnoo/runtime_monitor.py:
  - RuntimeMonitorPolicySummary dataclass,
  - resolve_monitor_policy_summary(...) that binds monitor policy view to manifest permissions declarations.
- Integrated runtime monitor policy diagnostics in src/kinnoo/run_command.py:
  - emits deterministic monitor policy summary for network/filesystem/shell/browser,
  - emits deterministic graceful degradation diagnostics with reason code when telemetry is limited.
- Added mapped regression test326 in tests/test_regression_v1.py:
  - test_feature41_feature39_integration_and_graceful_degradation,
  - validates policy summary alignment with feature39 permissions for Python and Node fixtures,
  - validates deterministic degradation guidance when telemetry-limited mode is simulated.
- Updated TASKS.txt status: task228 -> needs-review.

## Tests and results
- python3 -m pytest tests/test_regression_v1.py::test_feature41_feature39_integration_and_graceful_degradation -> 1 passed

## Bug/error notes
- No implementation bug/error class required iterative repair.
- Same bug/error class fix attempts: 0 (cap: 5).

## Teaching notes
- Integration layers are most maintainable when they expose a normalized policy summary object rather than scattering permission checks across multiple runtime branches.
- Graceful degradation should be explicit and machine-readable (reason codes + limited capabilities), so operators and CI can distinguish “policy denied” from “telemetry unavailable”.
- Cross-runtime parity does not always mean identical instrumentation depth; it means stable policy semantics and predictable fallback behavior where primitives differ.
