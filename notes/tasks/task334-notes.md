# Task334 Notes

## Summary
Implemented the Feature62 schema/validator contract for `openclaw-skill` and `provenance`, removed deferred metadata fields from schema usage, and updated manifest docs with canonical examples plus migration guidance.

## What Changed
- `src/kinnoo/schema.py`
  - Added `SUPPORTED_MANIFEST_TYPES = ["agent", "openclaw-skill"]`.
  - Added optional top-level `type` and `provenance` object fields.
  - Added nested provenance keys (`source_registry`, `source_slug`, `source_url`, `source_version`) to optional field typing.
  - Removed `channels`, `skills`, and `state_dirs` from optional schema fields.

- `src/kinnoo/validator.py`
  - Added disallowed-metadata checks that reject `channels`, `skills`, and `state_dirs` with deterministic guidance.
  - Added `openclaw-skill` type checks:
    - supports only allowed manifest `type` values
    - enforces `framework=openclaw`, `runtime.language=nodejs`, `runtime.type=daemon` for `type=openclaw-skill`
  - Added `provenance` validation rules:
    - requires `source_registry` and `source_version` when provenance is present
    - requires at least one of `source_slug` or `source_url`
  - Removed framework requirement for `channels` and no longer validates state_dirs contract here.

- `src/kinnoo/import_command.py`
  - For inferred OpenClaw projects, now emits `type: openclaw-skill`.
  - Stops emitting `skills` and `state_dirs` in generated manifests.

- `docs/manifest-schema-reference.md`
  - Added Feature62 contract section with canonical examples:
    - mirrored ClawHub skill
    - GitHub-origin agent (not skill)
    - locally authored OpenClaw project
  - Added migration guidance from flat source fields to `provenance` object.
  - Documented deferred metadata fields (`channels`, `skills`, `state_dirs`) as unsupported in this schema version.

- `tests/test_validator.py`
  - Added task regression test:
    - `test_feature62_openclaw_skill_schema_validation`

## Teaching Notes
- A robust schema migration pattern is:
  1. Introduce new canonical object shape (`provenance`).
  2. Add explicit deterministic validation rules for required and conditional fields.
  3. Reject deferred/legacy fields with clear migration guidance to avoid silent schema drift.
- Validation should encode business intent, not only type checks. Here, compatibility rules (`openclaw-skill` requires `framework=openclaw` + Node daemon runtime) are contract-level invariants.
- Documentation should ship canonical examples from day one; examples reduce ambiguity and improve implementation/test fixture quality.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k test_feature62_openclaw_skill_schema_validation`
- Result:
  - `1 passed, 453 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task334-smoke-tests.md`.
