# Task181 - feature32 daemon attach interactive control

## Summary
- Added attach command wiring in src/kinnoo/cli.py:
  - new subcommand `kinnoo attach <agent-dir>`
  - usage validation and dispatch to runtime attach logic.
- Implemented daemon attach flow in src/kinnoo/run_command.py:
  - new `attach_agent(agent_dir_arg)` function.
  - resolves persisted daemon state metadata from `.kinnoo/daemon-state.json`.
  - validates attach preconditions with deterministic diagnostics:
    - runtime type must be `daemon`,
    - runtime language must be supported for attach (`python` or `nodejs`),
    - daemon PID must still be running,
    - interactive TTY is required.
  - bridges daemon session output by streaming daemon log file content and ending cleanly when daemon exits.
- Extended supervisor utilities in src/kinnoo/supervisor.py:
  - added `daemon_pid_is_running(pid)` public helper for attach/stop lifecycle checks.
- Added task-linked regression test in tests/test_cli.py:
  - `test_feature32_attach_daemon_session_controls` (test279)
  - verifies supported attach path plus deterministic guarded failures for non-running daemon, unsupported runtime type, and non-TTY usage.
- Updated task tracking:
  - task181 status set to `needs-review` in TASKS.txt.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature32_attach_daemon_session_controls` -> `1 passed`
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- No implementation or test bugs encountered during task181.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Attach control surfaces should gate on explicit preconditions before opening a stream loop. This avoids ambiguous operator experiences and gives deterministic failure modes.
- For daemon lifecycle tooling, persisted metadata plus process-table checks forms a robust control plane even when the runtime process itself cannot expose a native interactive socket/pty API.
- Reusing a small supervisor helper (`daemon_pid_is_running`) keeps lifecycle checks consistent across stop/attach/logs flows and reduces divergence in process-state semantics.
