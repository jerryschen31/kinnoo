# Task378 Notes

## Summary
Implemented Feature84 task378 by adding `kinnoo search --openclaw-skill <query>` as a thin wrapper around `openclaw skills search`, including optional `--json` passthrough.

## What Was Implemented
- Updated `src/kinnoo/search_command.py`:
  - added `search_openclaw_skills(query, json_output=False)`
  - delegates to `openclaw skills search <query> [--json]`
  - preserves stdout/stderr passthrough and delegated exit code
- Updated `src/kinnoo/cli.py` search parser/dispatch:
  - added `--openclaw-skill` mode selector
  - added search `--json` passthrough flag for OpenClaw mode
  - routes OpenClaw mode to `search_openclaw_skills(...)`
  - preserves existing local/remote registry search mode behavior

## Test Coverage
- Added/validated:
  - `tests/test_cli_registry.py::test_feature84_skill_search_delegation_and_json_passthrough`
- Verifies:
  - OpenClaw search delegation command shape is correct
  - `--json` passthrough is preserved
  - successful search output passthrough remains stable

## Smoke Tests
- `notes/tasks/task378-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why mode flags are explicit (`--openclaw-skill`):
  - Explicit mode selection prevents accidental behavior overlap with existing local/remote registry search semantics.
- Why passthrough output is useful:
  - It allows Kinnoo to stay a stable control-plane wrapper while preserving native OpenClaw output contracts for humans and automation.
