# Task195 - feature35 pack snapshot capture for mutable state directories

## Summary
- Implemented pack-time state snapshot capture in [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py):
  - added deterministic state snapshot prefix `state_snapshots/` separate from immutable assets,
  - added `_iter_declared_state_dir_paths(...)` supporting both legacy string `state_dirs` entries and structured `{path, exclude}` entries,
  - added `_collect_state_snapshot_files(...)` for deterministic file enumeration and archive mapping,
  - enforced safety checks preventing state directory escape from agent root,
  - added runtime checks for missing/non-directory state roots with actionable warnings/errors.
- Added task-linked integration test293 in [tests/test_pack.py](tests/test_pack.py):
  - `test_feature35_pack_state_snapshot_layout` verifies:
    - state directory files are included under stable `state_snapshots/...` paths,
    - asset files remain in their immutable asset paths,
    - state files are not flattened into top-level runtime paths.
- During test insertion, restored boundaries for existing [tests/test_pack.py](tests/test_pack.py) `test_feature22_pack_warns_on_missing_asset_path` block to prevent accidental cross-test code spillover.
- Updated [TASKS.txt](TASKS.txt):
  - `task195` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_pack.py::test_feature35_pack_state_snapshot_layout` -> `1 passed`

## Bug/error notes
- Bug class encountered: test function boundary corruption in `tests/test_pack.py` after insertion (new test body accidentally captured statements from existing test).
- Resolution: restored missing existing-test body, isolated new test293 body, fixed indentation consistency.
- Same bug/error class fix attempts: `2`.

## Teaching notes
- For snapshot/archive features, define an explicit namespace boundary (`state_snapshots/` vs asset paths) early; it avoids semantic mixing and simplifies later install-restore logic.
- Deterministic archive assertions should validate both inclusion and isolation: assert what must exist and also assert forbidden path shapes that would indicate flattening.
- When adding tests into long files, re-open surrounding context to verify function boundaries/indentation; this catches a common regression class where one test accidentally absorbs another test's setup/assertions.
