# Task140 - feature22 documentation and regression gate

## Summary
- Added explicit Feature22 asset compatibility guidance in README, including no-assets backward compatibility, recursive folder inclusion, `bundle: false`, and threshold override behavior.
- Updated manifest schema reference docs to explicitly state that manifests without `assets` remain compatible with pre-feature22 pack/install behavior.
- Added the linked regression gate test `test_feature22_no_assets_regression_unchanged` to prove no-assets workflows remain unchanged across pack/install.
- Marked task140 as `needs-review` after validation and targeted regression pass.

## Files changed
- README.md
- docs/manifest-schema-reference.md
- tests/test_regression_v1.py
- TASKS.txt

## Linked tests (task140)
- test211: tests/test_regression_v1.py::test_feature22_no_assets_regression_unchanged

## Test runs and results
- python3 scripts/validate_project_manifests.py -> Validation passed: manifests are consistent
- python3 -m pytest tests/test_regression_v1.py::test_feature22_no_assets_regression_unchanged -> 1 passed

## Bug/error notes
- No repeated bug/error class encountered during task140 implementation.

## Teaching notes
- Regression gates are strongest when they execute stable pre-existing contract tests instead of re-testing new feature internals.
- For backward compatibility work, document defaults and opt-in behavior explicitly so users understand that unchanged manifests keep unchanged behavior.
- Pair docs updates with an automated regression gate to keep behavior and documentation aligned over time.
