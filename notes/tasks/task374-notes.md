# Task374 Notes

## Summary
Implemented Feature82 task374 by adding `kinnoo logs --daemon openclaw` as a thin OpenClaw logs wrapper with deterministic passthrough for `--follow` and `--json` flags.

## What Was Implemented
- Added new module `src/kinnoo/logs_command.py`:
  - `logs_openclaw(follow=False, json_output=False)` delegates to `openclaw logs`
  - forwards `--follow` and `--json` when requested
  - preserves stdout/stderr passthrough and returns delegated exit code
- Updated `src/kinnoo/cli.py` logs parser/dispatch:
  - added `--daemon openclaw` selector
  - added logs `--json` passthrough flag
  - routes OpenClaw daemon logs to `logs_openclaw(...)`
  - keeps existing agent-dir daemon log behavior unchanged

## Test Coverage
- Added/validated:
  - `tests/test_cli.py::test_feature82_logs_passthrough_follow_and_json`
- Verifies:
  - `kinnoo logs --daemon openclaw` delegates successfully
  - `--follow` and `--json` are passed through deterministically
  - wrapper preserves delegated output behavior

## Smoke Tests
- `notes/tasks/task374-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why this wrapper is intentionally thin:
  - Thin adapters reduce divergence from upstream CLI semantics and make upgrades lower-risk.
- Why explicit flag passthrough matters:
  - Stable flag mapping keeps user expectations consistent between native OpenClaw and Kinnoo wrapper commands.
