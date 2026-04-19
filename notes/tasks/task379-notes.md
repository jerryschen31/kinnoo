# Task379 Notes

> **⚠️ DEPRECATED (2026-04-18):** The OpenClaw skill search preflight described below reflects an earlier paradigm where kinnoo treated individual OpenClaw skills from ClawHub as the fundamental unit. kinnoo now supports OpenClaw workspace-based agents instead. This note is retained for historical context only.

## Summary
Implemented Feature84 task379 by enforcing OpenClaw preflight before skill search and adding deterministic guidance for empty results and upstream failures while preserving stable `--json` behavior.

## What Was Implemented
- Updated `src/kinnoo/search_command.py`:
  - added preflight gate: `run_openclaw_preflight_for_command("openclaw-skill-search")`
  - emits deterministic preflight failure diagnostics with categories
  - for success with empty results:
    - human mode: prints actionable "No OpenClaw skill results found..." guidance
    - json mode: preserves machine-readable empty response (`[]`)
  - for non-zero upstream search exits:
    - emits deterministic category `openclaw_skill_search_nonzero_exit`

## Test Coverage
- Added/validated:
  - `tests/test_cli_registry.py::test_feature84_skill_search_preflight_empty_and_error_guidance`
- Verifies:
  - missing CLI preflight failure category is stable
  - empty result guidance is deterministic in human mode
  - json mode preserves empty machine-readable output contract
  - upstream non-zero failures emit deterministic diagnostics

## Smoke Tests
- `notes/tasks/task379-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why empty-result handling differs by output mode:
  - Human mode benefits from actionable guidance, while JSON mode should avoid narrative noise and keep machine contracts clean.
- Why preflight and runtime failure categories are separate:
  - Distinct categories isolate environment readiness problems from search backend failures, improving reliability and observability.
