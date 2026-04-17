# Task136 - feature22 pack asset path inclusion and safety

## Summary
- Implemented manifest-driven asset bundling in pack flow via assets.paths when bundling is enabled.
- Added recursive directory expansion with deterministic ordering for bundled asset files.
- Added bundle opt-out behavior for assets.bundle: false with explicit informational output.
- Added traversal/escape-path rejection and non-fatal warnings for missing declared asset paths.

## Files changed
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Linked tests (task136)
- test204: tests/test_pack.py::test_feature22_pack_includes_assets_recursively_when_enabled
- test205: tests/test_pack.py::test_feature22_pack_skips_assets_when_bundle_false
- test206: tests/test_pack.py::test_feature22_pack_rejects_asset_path_traversal
- test207: tests/test_pack.py::test_feature22_pack_warns_on_missing_asset_path

## Test runs and results
- python3 scripts/validate_project_manifests.py -> Validation passed: manifests are consistent
- python3 -m pytest tests/test_pack.py -k "feature22 or assets" -> 4 passed, 9 deselected

## Teaching notes
- Recursive bundling should always emit archive paths relative to the agent root; this prevents non-deterministic archive layouts.
- Path traversal defense is best modeled as a root containment check after normalization/resolution; allow only paths where candidate.relative_to(root) succeeds.
- Warning-vs-error boundaries matter for UX: missing optional assets can be warning-only, while escape attempts should fail closed.
- Deduplicating archive entries avoids subtle zip behavior issues when the same file is included by multiple mechanisms.
