# Task183 - feature32 supervisor health state diagnostics and regression gate

## Summary
- Added daemon lifecycle state classification to src/kinnoo/health_check.py:
  - `DaemonLifecycleResult` dataclass
  - `classify_daemon_lifecycle_state(...)` helper that deterministically classifies daemon status as:
    - `not-running`
    - `unhealthy`
    - `healthy`
  - each state includes actionable operator guidance text.
- Integrated daemon lifecycle diagnostics into src/kinnoo/run_command.py preflight flow:
  - for `runtime.type: daemon`, preflight now evaluates persisted daemon metadata + process liveness + service check outcomes.
  - emits deterministic preflight line and guidance for daemon lifecycle state.
  - includes daemon state in preflight readiness gating for daemon runtime.
  - preserves existing one-shot and mcp-server preflight behavior without daemon-state evaluation.
- Added task-linked regression gate in tests/test_regression_v1.py:
  - `test_feature32_daemon_health_state_regression_gate` (test281)
  - verifies `healthy`, `unhealthy`, and `not-running` daemon states with actionable diagnostics.
  - verifies compatibility: one-shot and mcp-server preflight flows remain green and do not emit daemon lifecycle state output.
- Updated task tracking:
  - task183 status set to `needs-review` in TASKS.txt.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature32_daemon_health_state_regression_gate` -> `1 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- One implementation issue encountered during test authoring:
  - initial test281 draft included incomplete capture handling.
  - fixed by replacing with complete capsys-based regression assertions.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Lifecycle diagnostics are easier to maintain when state classification is centralized in a small pure helper (`classify_daemon_lifecycle_state`) instead of duplicating ad-hoc logic in CLI/runtime code.
- Treating daemon state as a combination of three signals improves operational clarity:
  - control-plane metadata exists,
  - process is alive,
  - dependent service checks are healthy.
- Regression gates for lifecycle features should explicitly include non-daemon compatibility assertions to prevent accidental behavior bleed into legacy runtime paths.
