# Task138 - feature22 archive size threshold behavior for assets

## Summary
- Implemented asset-aware archive warning threshold resolution in pack flow.
- `assets.max_bundle_size_mb` now overrides default/env threshold behavior when present and valid.
- Preserved existing warning wording and archive-size reporting output shape.
- Added linked test209 to verify default threshold behavior and assets override behavior.

## Files changed
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Linked tests (task138)
- test209: tests/test_pack.py::test_feature22_pack_size_warning_uses_assets_threshold

## Test runs and results
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent
- python3 -m pytest tests/test_pack.py -k "feature22 or assets" -> 5 passed, 9 deselected

## Bug/error notes
- No repeated implementation bug class encountered for task138.

## Teaching notes
- Introduce config-precedence explicitly: task-specific manifest values should override generic defaults and environment knobs when the feature contract demands it.
- Keep threshold parsing defensive (`bool` exclusion, positive-number checks) even when validator already enforces schema; this improves runtime resilience.
- Reuse stable warning text while changing threshold source to avoid accidental downstream regression in user guidance and tests.
