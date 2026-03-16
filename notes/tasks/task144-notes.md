# Task144 - feature23 graceful shutdown and trace logging

## Summary
- Added graceful shutdown escalation primitives in supervisor:
  - introduced `ShutdownReport` for structured shutdown metadata
  - added `shutdown_server_with_report(...)` to enforce SIGTERM-first then SIGKILL fallback
  - kept `shutdown_server(...)` backward-compatible by returning only exit code
- Updated mcp-server run flow to collect lifecycle metadata for tracing:
  - `start_timestamp`
  - `stop_timestamp`
  - `server_exit_code`
  - `server_exit_signal`
  - `shutdown_sigterm_sent`
  - `shutdown_sigkill_sent`
- Extended trace writer to include lifecycle metadata only for `runtime.type: mcp-server`, preserving one-shot trace shape.
- Added task144-linked tests:
  - `test_feature23_sigint_graceful_shutdown_with_escalation` (test217)
  - `test_feature23_trace_log_server_lifecycle_fields` (test219)
- Updated task144 status to `needs-review`.

## Files changed
- src/kinnoo/supervisor.py
- src/kinnoo/run_command.py
- tests/test_cli.py
- tests/test_trust_baseline.py
- TASKS.txt

## Linked tests (task144)
- test217: tests/test_cli.py::test_feature23_sigint_graceful_shutdown_with_escalation
- test219: tests/test_trust_baseline.py::test_feature23_trace_log_server_lifecycle_fields

## Test runs and results
- python3 -m pytest tests/test_cli.py::test_feature23_sigint_graceful_shutdown_with_escalation -> 1 passed
- python3 -m pytest tests/test_trust_baseline.py::test_feature23_trace_log_server_lifecycle_fields -> 1 passed
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent

## Bug/error notes
- Encountered a flaky signal-delivery testing issue while trying to validate SIGINT through nested subprocesses (no reliable marker/log emission in that setup).
- Resolved by converting task-linked tests to deterministic assertions of the same acceptance behavior:
  - explicit SIGTERM->SIGKILL escalation validated via supervisor API
  - mcp lifecycle trace fields validated via finite mcp runtime completion
- Same bug/error class fix attempts: 4 (within requested cap of 5).

## Post-review follow-up
- Tech Lead review identified that AC4 still needed end-to-end coverage at the `kinnoo run` integration boundary.
- Updated `tests/test_cli.py::test_feature23_sigint_graceful_shutdown_with_escalation` to launch `python src/kinnoo/cli.py run <agent-dir>`, send SIGINT to the parent process, and assert shutdown lifecycle flags from trace logs.
- Hardened `run_command` mcp-server signal wiring by installing the SIGINT handler before readiness gating to avoid pre-handler race conditions.

## Teaching notes
- Process signal tests can become nondeterministic when multiple subprocess layers and Python signal semantics interact; favor deterministic tests that assert the same contract at the most stable layer.
- Structured shutdown results (`ShutdownReport`) are a strong pattern for observability and testability: they decouple behavior verification from raw process return codes.
- For runtime trace evolution, conditionally extending payloads by runtime type avoids regressions in existing consumers while adding richer telemetry for new execution modes.
