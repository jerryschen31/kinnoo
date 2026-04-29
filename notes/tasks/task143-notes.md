# Task143 - feature23 run_command integration for mcp-server mode

## Summary
- Integrated `runtime.type: mcp-server` into `run_agent(...)` by routing process lifecycle through supervisor APIs.
- Preserved one-shot runtime behavior by retaining the existing direct `subprocess.Popen(...).communicate()` path when runtime type is not `mcp-server`.
- Added task143-linked integration tests to confirm:
  - long-running server execution mode is active for `mcp-server` (`test215`)
  - stdout/stderr passthrough occurs while process is still running (`test218`)
- Updated task143 status to `needs-review`.

## Files changed
- src/kinnoo/run_command.py
- tests/test_cli.py
- TASKS.txt

## Linked tests (task143)
- test215: tests/test_cli.py::test_feature23_run_mcp_server_long_running_mode
- test218: tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr

## Test runs and results
- python3 -m pytest tests/test_cli.py::test_feature23_run_mcp_server_long_running_mode -> 1 passed
- python3 -m pytest tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr -> 1 passed
- python3 scripts/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- Initial test218 assertion was too strict (first stdout line can be readiness marker); updated the test to assert streamed markers across multiple lines while process remains running.
- Same bug/error class fix attempts: 1 (within requested cap of 5).

## Teaching notes
- Runtime branching is a common extensibility point: keep the orchestrator small and delegate process control to a specialized module (`supervisor`) so each runtime mode can evolve independently.
- For long-running agent systems, "ready" and "running" are distinct states. Readiness probes gate startup correctness, while stream-forwarding ensures observability during steady state.
- Integration tests for streaming should assert behavior while the process is still alive; that catches hidden buffering regressions that output-only-after-exit checks can miss.
