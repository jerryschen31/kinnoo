# Task364 Notes

## Summary
Implemented Feature77 task364 by changing OpenClaw init to delegate agent registration to OpenClaw CLI with mandatory preflight and existing-workspace protection.

## What Was Implemented
- In src/kinnoo/init_command.py for `framework=openclaw`:
  - resolve workspace path as `~/.openclaw/workspace-<name>`
  - fail if workspace already exists
  - run shared preflight via `run_openclaw_preflight_for_command("init")`
  - delegate registration to `openclaw agents add <name> --workspace <path>`
  - return deterministic error if delegated command fails

## Test Coverage
- Added:
  - tests/test_init.py::test_feature77_init_delegation_and_existing_workspace_guard
- Verifies:
  - preflight executes before subprocess delegation
  - delegated command path is reached
  - existing workspace triggers deterministic guard failure

## Teaching Notes
- Why delegate instead of scaffolding internals:
  - Wrappers should leverage source-of-truth lifecycle commands from upstream systems.
  - This reduces drift and maintenance burden when OpenClaw evolves quickly.
- Why preflight-first sequencing matters:
  - Failing before subprocess/file mutations prevents partial setup and improves operator trust.
