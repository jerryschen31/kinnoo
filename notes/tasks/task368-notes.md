# Task368 Notes

## Summary
Implemented Feature79 task368 by adding deterministic OpenClaw pack include rules for identity files and workspace content directories.

## What Was Implemented
- In `src/kinnoo/pack_command.py` added OpenClaw include constants:
  - identity files: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `USER.md`, `MEMORY.md`, `IDENTITY.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`
  - workspace directories: `memory/`, `skills/`
- Added `_collect_openclaw_workspace_files(agent_root)`:
  - includes present identity files only (optional files do not fail pack)
  - recursively includes files under `memory/` and `skills/` with deterministic sorted order
- Added `manifest_framework` detection and OpenClaw-specific include wiring in archive write flow.

## Test Coverage
- Added/validated:
  - `tests/test_pack.py::test_feature79_openclaw_pack_includes_identity_and_workspace_dirs`
- Verifies:
  - OpenClaw pack succeeds with partial optional identity files present
  - archive includes `AGENTS.md`, `SOUL.md`, `skills/...`, and `memory/...`
  - missing optional identity file (`TOOLS.md`) does not appear and does not fail pack

## Teaching Notes
- Why include lists are explicit:
  - Explicit contracts prevent accidental omission of framework-critical metadata when packaging across environments.
- Why optional files are tolerated:
  - OpenClaw workspaces can be in-progress; pack should be robust to partial identity authoring while preserving deterministic behavior.
