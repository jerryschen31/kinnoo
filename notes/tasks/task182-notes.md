# Task182 - feature32 daemon logs command and contextual output

## Summary
- Added logs command wiring in src/kinnoo/cli.py:
  - new subcommand `kinnoo logs <agent-dir>`
  - `--tail` option for recent-line output window
  - `--follow` option for live streaming mode.
- Implemented daemon logs flow in src/kinnoo/run_command.py:
  - new `logs_agent(agent_dir_arg, follow=False, tail_lines=20)` function.
  - resolves daemon state metadata and log path from persisted control-plane files.
  - validates runtime and metadata preconditions with deterministic diagnostics.
  - renders each output line with source and UTC timestamp context.
  - supports tail mode and follow mode, ending follow deterministically when daemon exits.
  - handles missing log file and non-running daemon follow requests with actionable errors.
- Added task-linked integration test in tests/test_cli.py:
  - `test_feature32_logs_daemon_tail_and_follow` (test280)
  - verifies tail output context, follow streaming output, and deterministic diagnostics for missing/non-running cases.
- Updated task tracking:
  - task182 status set to `needs-review` in TASKS.txt.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature32_logs_daemon_tail_and_follow` -> `1 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- No implementation or test bugs encountered during task182.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Logs control surfaces should separate two operator intents clearly:
  - tail: bounded historical context for quick diagnosis,
  - follow: live stream mode tied to daemon liveness.
- Adding source and timestamp context at rendering time gives consistent observability even when daemon-emitted lines are unstructured.
- Deterministic guardrails (missing state, missing log path, non-running follow mode) reduce ambiguity and make CLI behavior easier to automate in regression tests.
