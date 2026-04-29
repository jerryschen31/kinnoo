# Task180 - feature32 daemon stop command and graceful termination

## Summary
- Added daemon lifecycle stop helpers in src/kinnoo/supervisor.py:
  - `DaemonStopReport` for deterministic stop-path reporting.
  - `stop_daemon_pid(...)` implementing SIGTERM-first shutdown with bounded wait and SIGKILL fallback.
  - `clear_daemon_state(...)` for control-plane metadata cleanup after terminal stop outcomes.
- Added stop control flow in src/kinnoo/run_command.py:
  - `stop_agent(agent_dir_arg)` resolves daemon state metadata, validates PID, performs stop flow via supervisor helper, prints deterministic diagnostics, and clears stale/terminal state metadata.
- Added CLI command wiring in src/kinnoo/cli.py:
  - new `kinnoo stop <agent-dir>` subcommand with usage/error handling and dispatch to `stop_agent`.
- Added task-linked integration test in tests/test_cli.py:
  - `test_feature32_stop_daemon_graceful_and_fallback` (test278)
  - covers responsive SIGTERM stop and fallback SIGKILL path, including metadata cleanup assertions.
- Updated TASKS.txt:
  - `task180` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature32_stop_daemon_graceful_and_fallback` -> `1 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- No implementation bugs encountered while developing task180.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Daemon stop semantics are best implemented as an explicit two-stage control algorithm: first a graceful `SIGTERM` with bounded wait, then a deterministic hard-stop fallback (`SIGKILL`) if the process is unresponsive.
- A dedicated report object (`DaemonStopReport`) helps separate runtime behavior from CLI/operator messaging, which makes both testing and future health integrations easier.
- Persisted daemon state should be treated as control-plane truth but must be cleaned on terminal outcomes; this prevents stale PID drift and makes later commands (`attach`, `logs`, health checks) more predictable.
