# Task227 - feature41 dry-run monitoring mode

## Summary
- Added dry-run prediction helper in src/kinnoo/runtime_monitor.py:
  - predict_dry_run_actions(...)
  - emits deterministic predicted process/network/filesystem intents based on entrypoint heuristics and pass-through args.
- Added CLI flag plumbing in src/kinnoo/cli.py:
  - --dry-run for kinnoo run.
- Added low-risk dry-run execution path in src/kinnoo/run_command.py:
  - prints deterministic dry-run diagnostics,
  - suppresses entrypoint execution,
  - records baseline monitor process event through existing runtime monitor lifecycle,
  - returns success when dry-run path completes.
- Added mapped test325 in tests/test_cli.py:
  - test_feature41_dry_run_monitoring_trace.
- Updated TASKS.txt status: task227 -> needs-review.

## Tests and results
- python3 -m pytest tests/test_cli.py::test_feature41_dry_run_monitoring_trace -> 1 passed

## Bug/error notes
- No implementation bug/error class required iterative repair.
- Same bug/error class fix attempts: 0 (cap: 5).

## Teaching notes
- Dry-run is most useful when it behaves like a planning/explainability mode: deterministic predicted actions plus explicit side-effect suppression guarantees.
- Keep dry-run output schema-like and stable (category/action/detail) so operators and future tooling can consume it reliably.
- Heuristic intent detection should be conservative and transparent; it is an aid to risk review, not a replacement for full runtime enforcement.
