# Task370 Notes

## Summary
Implemented Feature80 task370 by routing OpenClaw install extraction into `~/.openclaw/workspace-<name>`, running OpenClaw preflight before extraction, and delegating workspace registration with `openclaw agents add`.

## What Was Implemented
- `src/kinnoo/install_command.py`:
  - Added import of `run_openclaw_preflight_for_command`.
  - For `type: openclaw-skill` manifests:
    - run preflight (`install` mode) before archive extraction
    - select deterministic target directory: `Path.home() / ".openclaw" / f"workspace-{agent_name}"`
  - Updated delegated OpenClaw command from dependency install path to registration path:
    - `openclaw agents add <agent_name> --workspace <target_dir>`
  - Kept deterministic delegated trace writing behavior.

## Test Coverage
- Added/validated:
  - `tests/test_install.py::test_feature80_openclaw_install_extracts_to_workspace_and_registers`
- Verifies:
  - OpenClaw installs extract to workspace convention under `~/.openclaw`
  - registration command invocation shape matches `openclaw agents add ... --workspace ...`
  - install succeeds in non-interactive mode with unverified-publisher override.

## Teaching Notes
- Why preflight before extraction matters:
  - It avoids partial filesystem writes when OpenClaw runtime prerequisites are missing.
- Why canonical install target matters:
  - A single workspace convention reduces ambiguity and keeps install/import/init behaviors aligned across wrapper flows.
