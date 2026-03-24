# Task197 - feature35 selective snapshot exclusions for state_dirs

## Summary
- Implemented `state_dirs[].exclude` filtering during pack snapshot capture in [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py):
  - added manifest normalization helper for structured state dir entries with per-root exclude patterns,
  - added deterministic path-matching helpers for exclusion checks,
  - applied exclusion filtering before adding files under `state_snapshots/<state-dir>/...`.
- Added task-linked integration regression test295 in [tests/test_pack.py](tests/test_pack.py):
  - `test_feature35_state_dirs_exclude_patterns` validates both archive and restored-install outcomes,
  - verifies excluded files are omitted while core state files are preserved.
- Updated [TASKS.txt](TASKS.txt):
  - `task197` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_pack.py::test_feature35_state_dirs_exclude_patterns` -> `1 passed`

## Bug/error notes
- One bug class encountered:
  - test initially invoked `src/kinnoo/cli.py` from `tmp_path`, causing file-not-found for the CLI script.
  - fixed by reusing project test harness command (`python3 -m src.kinnoo.cli`) with `_pack_env(...)`.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Exclusion policy is safest when applied as early as possible in the snapshot pipeline (during file enumeration), because this guarantees omitted files never enter the archive.
- Deterministic exclusion behavior depends on normalizing both candidate paths and patterns (for example slash normalization and optional `./` prefix stripping) before matching.
- For contract tests that span multiple CLI stages, keep one focused regression that validates both archive shape and final restored filesystem state; this catches drift between pack and install semantics.
