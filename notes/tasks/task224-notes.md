# Task224 - feature41 runtime event monitoring baseline

## Summary
- Added baseline runtime monitor module in src/kinnoo/runtime_monitor.py.
- Wired monitor lifecycle into run flow in src/kinnoo/run_command.py so monitored runs capture:
  - process spawn events,
  - network access attempt events (Python runtime baseline via sitecustomize hook),
  - filesystem write events (snapshot-based created/modified detection).
- Added mapped test322 in tests/test_run_preflight.py:
  - test_feature41_runtime_event_monitoring_baseline.
- Updated TASKS.txt status for task224 to needs-review.

## Tests and results
- python3 -m pytest tests/test_run_preflight.py::test_feature41_runtime_event_monitoring_baseline -> 1 passed

## Bug/error notes
- Encountered one implementation bug: IndentationError in run_command.py during first test run.
- Resolution: corrected runtime monitor wiring indentation in run_agent and re-ran mapped test.
- Same bug/error class fix attempts: 1 (cap: 5).

## Teaching notes
- For runtime telemetry baselines, start with deterministic, low-risk signals (process launch + controlled hooks + filesystem deltas) before adding deep OS-level probes.
- Python runtime observability can be bootstrapped safely with a temporary sitecustomize hook injected through PYTHONPATH; this avoids changing user entrypoint code.
- Keep telemetry schema stable and machine-readable (schema_version, category, event_type, sequence, timestamp, details) so future policy enforcement can build on a reliable contract.
- Always ensure telemetry output paths and payloads are secret-safe by design and redaction-aware.
