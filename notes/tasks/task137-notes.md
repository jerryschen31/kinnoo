# Task137 - feature22 install extraction and inspect visibility

## Summary
- Kept install extraction behavior path-preserving for bundled assets and validated it with a dedicated feature22 install test.
- Extended inspect output to display declared asset paths and computed asset size metadata.
- Added asset file expansion for inspect in both directory and archive modes so visibility works consistently across both targets.

## Files changed
- src/kinnoo/inspect_command.py
- tests/test_cli_install_extract.py
- tests/test_cli_inspect.py
- TASKS.txt

## Linked tests (task137)
- test208: tests/test_cli_install_extract.py::test_feature22_install_extracts_assets_with_relative_paths
- test210: tests/test_cli_inspect.py::test_feature22_inspect_displays_asset_paths_and_sizes

## Test runs and results
- python3 scripts/validate_project_manifests.py -> Validation passed: manifests are consistent
- python3 -m pytest tests/test_cli_install_extract.py -k "feature22 or assets" -> 1 passed, 1 deselected
- python3 -m pytest tests/test_cli_inspect.py -k "feature22 or assets" -> 1 passed, 6 deselected

## Bug/error notes
- Encountered one test-collection error: IndentationError in tests/test_cli_inspect.py for the new task137 test function.
- Fixed by correcting function indentation to top-level alignment.
- Fix attempts for this bug class: 1 (resolved; below 5-attempt cap).

## Teaching notes
- For archive-vs-directory parity, compute asset metadata from the target’s native source: filesystem walks for directories and zip member metadata for archives.
- Showing both declared asset paths and resolved file-level sizes helps users verify manifest intent versus packaged reality.
- Keep traversal guards and size calculations in inspect read-only; inspect should explain state, not mutate it.
