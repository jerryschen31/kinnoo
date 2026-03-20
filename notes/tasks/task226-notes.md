# Task226 - feature41 resource control enforcement

## Summary
- Added task226 resource-control policy helpers in src/kinnoo/runtime_monitor.py:
  - RuntimeResourceControls dataclass,
  - normalize_runtime_resource_controls(...) input validation,
  - posix_resource_limits_supported() platform capability check.
- Extended run CLI plumbing in src/kinnoo/cli.py:
  - --max-seconds
  - --max-cpu-seconds
  - --max-memory-mb
- Implemented enforcement in src/kinnoo/run_command.py:
  - wall-clock timeout kill-switch in one-shot execution paths,
  - POSIX resource-limits preexec wiring for CPU/memory where supported,
  - deterministic degraded-mode warnings when resource controls are unsupported,
  - deterministic reason codes in timeout/cpu limit failure messages.
- Added mapped test324 in tests/test_cli.py:
  - test_feature41_resource_control_enforcement.
- Updated TASKS.txt status: task226 -> needs-review.

## Tests and results
- python3 -m pytest tests/test_cli.py::test_feature41_resource_control_enforcement -> 1 passed

## Bug/error notes
- No implementation bug/error class required iterative fixes for this task.
- Same bug/error class fix attempts: 0 (cap: 5).

## Teaching notes
- Resource controls are most reliable when split by control-plane type:
  - wall-clock timeout is portable and should be enforced everywhere,
  - CPU/memory hard limits depend on OS/runtime primitives and need explicit graceful fallback messaging.
- Deterministic degraded-mode diagnostics are part of the contract: when enforcement is unavailable, make the limitation explicit so operators and CI can reason about risk.
- Parsing/normalizing resource flags early keeps policy decisions centralized and reduces ambiguous runtime behavior.
