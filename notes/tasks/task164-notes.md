# Task164 - feature19 in-place manifest write, collision safety, and rollback

## Summary
- Implemented task164 import write flow in [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
  - Added deterministic in-place manifest generation and write (`kinnoo.yaml`) in target project root only
  - Added collision protection: import aborts when `kinnoo.yaml` already exists (non-override path)
  - Added rollback safety: if a failure occurs after write begins, partial `kinnoo.yaml` is removed before returning error
- Added focused task164 tests in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature19_import_writes_manifest_in_place` (test254)
  - `test_feature19_import_failure_rolls_back_partial_output` (test255)
  - `test_feature19_import_collision_requires_explicit_override` (test256)
- Updated `task164` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature19_import_writes_manifest_in_place tests/test_cli_import.py::test_feature19_import_failure_rolls_back_partial_output tests/test_cli_import.py::test_feature19_import_collision_requires_explicit_override` -> `3 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Rollback logic should be co-located with the write boundary (`try/except` around file creation) so cleanup is guaranteed when post-write steps fail.
- In-place import safety improves when collision checks are explicit and default to non-destructive behavior; override flows can be layered later without weakening default guarantees.
- A deterministic baseline manifest is useful in staged feature delivery: it enables reliable contract tests now while keeping room for analyzer-driven enrichment in subsequent tasks.
