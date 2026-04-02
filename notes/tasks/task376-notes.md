# Task376 Notes

## Summary
Implemented Feature83 task376 by adding `kinnoo install <agent> --openclaw-skill <slug-or-url>` mode that resolves existing OpenClaw agent workspaces and delegates skill installation through OpenClaw.

## What Was Implemented
- Updated `src/kinnoo/cli.py` install parser/dispatch:
  - added `--openclaw-skill <skill-id>`
  - added mode usage validation for missing agent target
  - forwards `openclaw_skill_identifier` into install command
- Updated `src/kinnoo/install_command.py`:
  - added `openclaw_skill_identifier` parameter to `install_agent(...)`
  - added `_resolve_openclaw_agent_workspace(agent_name)` via `openclaw agents list`
  - added `_install_openclaw_skill_for_existing_agent(...)` delegation path
  - delegates `openclaw skills install <skill> --workspace <workspace>` for resolved agent
  - preserves stdout/stderr passthrough and delegated exit code semantics

## Test Coverage
- Added/validated:
  - `tests/test_cli_install.py::test_feature83_skill_install_existing_agent_slug_and_url`
- Verifies:
  - existing agent is resolved through `openclaw agents list`
  - slug and URL skill identifiers are both accepted
  - delegated command shape targets resolved workspace deterministically

## Smoke Tests
- `notes/tasks/task376-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why agent resolution precedes skill installation:
  - It avoids ambiguous installs and ensures skills are applied to a known workspace context.
- Why delegation keeps raw skill identifier in task376:
  - This preserves pass-through behavior first; normalization and richer diagnostics are added in the next task to keep changes testable and incremental.
