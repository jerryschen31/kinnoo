# Task142 - feature23 supervisor lifecycle and readiness probes

## Summary
- Added a standalone supervisor module with process lifecycle primitives:
  - `start_server(...)`
  - `stream_output(...)`
  - `wait_until_ready(...)`
  - `shutdown_server(...)`
- Implemented readiness strategy inference with fallback behavior:
  - explicit `readiness_probe.method: tcp` with port
  - explicit `readiness_probe.method: stdout` with marker
  - default fallback to TCP when `runtime.port` exists
  - otherwise immediate-ready mode
- Added task142-linked tests for probe modes and default fallback behavior.
- Updated task142 status to `needs-review` after passing scoped tests.

## Files changed
- src/kinnoo/supervisor.py
- src/kinnoo/schema.py
- tests/test_cli.py
- TASKS.txt

## Linked tests (task142)
- test216: tests/test_cli.py::test_feature23_readiness_probe_tcp_and_stdout_marker
- test221: tests/test_cli.py::test_feature23_default_readiness_fallback_behavior

## Test runs and results
- python3 -m pytest tests/test_cli.py::test_feature23_readiness_probe_tcp_and_stdout_marker -> 1 passed
- python3 -m pytest tests/test_cli.py::test_feature23_default_readiness_fallback_behavior -> 1 passed
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- No repeated bug/error class encountered during task142 implementation.

## Teaching notes
- Building a supervisor layer first (before full run-command integration) de-risks long-running runtime features by isolating lifecycle logic behind a small API.
- Readiness checks should be explicit and testable, with deterministic fallbacks to avoid fragile runtime startup behavior.
- For agentic systems, startup gating is critical: returning "ready" too early causes downstream tool/runtime flakiness that looks nondeterministic at the application layer.
