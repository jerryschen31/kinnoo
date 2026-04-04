# Task337 Notes

## Summary
Implemented Feature63 attribution UX and idempotency behavior by surfacing mirrored ClawHub provenance in search/inspect outputs and adding regression coverage for repeated upsert sync cycles.

## What Changed
- `src/kinnoo/search_command.py`
  - Added mirror result path for remote searches using `RegistryService.list_clawhub_mirror_records()`.
  - Added mirrored output fields in search results:
    - `source: clawhub (mirrored)`
    - `slug: <source_slug>`
    - `synced_at: <timestamp>`
  - Added deterministic mirror query matching across name/slug/version/url and `clawhub` namespace keyword.
  - Added compatibility helpers so mirror rendering works for both dataclass and dict payload shapes.

- `src/kinnoo/inspect_command.py`
  - Added inspect target mode for mirrored slugs:
    - `kinnoo inspect clawhub:<owner>/<slug>`
    - `kinnoo inspect clawhub/<owner>/<slug>`
  - Added attribution-focused inspect output with source and sync metadata.
  - Added raw-mode representation for mirrored records.

- `tests/test_cli_registry.py`
  - Added `test_feature63_mirror_attribution_and_idempotency` (test496).
  - Covers repeated upsert behavior, search attribution labels, namespace query behavior, and inspect mirror metadata output.

## Teaching Notes
- For mirror systems, idempotency is easiest to guarantee when an upsert key is deterministic (`source_slug + source_version`), and tests assert stable record counts after repeated writes.
- Attribution should be first-class user output, not buried in metadata; that makes provenance auditable in routine workflows (`search`, `inspect`).
- When integrating heterogeneous backend payloads (dict vs dataclass), centralizing field access avoids brittle output bugs.

## Test Run (Task-only)
- Command:
  - `python3 -m pytest tests --testmon -k "test_feature63_mirror_attribution_and_idempotency"`
- Result:
  - `1 passed, 458 deselected`

## Smoke Tests
- No task-specific smoke test file found at `notes/tasks/task337-smoke-tests.md`.
