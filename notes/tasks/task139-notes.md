# Task139 - feature22 asset credential warning sweep in pack

## Summary
- Added warning-only asset credential sweep hooks into pack flow.
- Implemented filename-pattern warnings for secret-like asset files (for example `.env`, `.pem`, `id_rsa`, credential markers).
- Implemented regex-based text scanning for credential-like content in UTF-8 text assets.
- Added explicit binary-file skip behavior for text regex scanning.
- Added warning-only heuristic disclaimer output for asset credential scan findings.

## Files changed
- src/kinnoo/code_sweep.py
- src/kinnoo/pack_command.py
- tests/test_pack.py
- TASKS.txt

## Linked tests (task139)
- test212: tests/test_pack.py::test_feature22_pack_warns_on_secret_like_asset_filenames
- test213: tests/test_pack.py::test_feature22_pack_text_secret_scan_warning_only_with_binary_skip

## Test runs and results
- python3 src/validate_project_manifests.py -> Validation passed: manifests are consistent
- python3 -m pytest tests/test_pack.py -k "feature22 or assets" -> 7 passed, 9 deselected

## Bug/error notes
- No repeated bug class encountered during task139 implementation.

## Teaching notes
- Keep heuristic security sweeps non-blocking in packaging workflows, but make warnings explicit and actionable.
- Separate filename heuristics from content heuristics so each signal is explainable and testable.
- Binary-skip logic is important to avoid false decoding failures and noisy alerts when scanning mixed asset bundles.
