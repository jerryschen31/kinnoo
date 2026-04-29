# Task372 Notes

## Summary
Implemented Feature81 task372 by wiring OpenClaw run delegation to `openclaw agent --agent <name> --message <prompt>`, adding `--thinking` passthrough, and propagating delegated non-zero exit codes with deterministic diagnostics.

## What Was Implemented
- Updated run CLI usage/help and parser:
  - added `--thinking {low,medium,high}` on `kinnoo run`
- Updated run dispatch in `src/kinnoo/cli.py`:
  - passes `openclaw_thinking` into `run_agent(...)`
- Updated `src/kinnoo/run_command.py` OpenClaw run path:
  - resolves agent name from manifest `name`
  - delegates to `openclaw agent --agent <name> --message <prompt>`
  - appends optional `--thinking <level>`
  - preserves stream passthrough and returns delegated exit code
  - emits deterministic non-zero diagnostic category: `openclaw_agent_runtime_nonzero_exit`

## Test Coverage
- Added/validated:
  - `tests/test_cli.py::test_feature81_run_mapping_thinking_and_exit_propagation`
- Verifies:
  - delegated command shape matches feature contract
  - `--thinking high` is passed through correctly
  - delegated runtime failure returns non-zero exit and stable diagnostic category

## Smoke Tests
- `notes/tasks/task372-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why delegation uses manifest `name` instead of directory name:
  - `name` is the canonical identity used across manifest, install, and registry paths; this avoids path-dependent behavior.
- Why deterministic error categories matter:
  - They create stable operational contracts for automation and make failure triage easier in CI and logs.
