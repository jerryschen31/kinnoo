# task359 notes

## Summary
- Added metadata cleanup coverage for uninstall in `tests/test_install.py::test_feature74_uninstall_metadata_and_errors`.
- Verified uninstall removes corresponding lockfile agent entry while preserving other entries.
- Verified uninstall writes structured uninstall trace events under install-root metadata.
- Verified deterministic missing-target diagnostics for repeated uninstall attempts.
- Updated README with uninstall metadata lifecycle and failure-path guidance.

## Teaching Notes
- Metadata cleanup should be validated independently from destructive path execution to prevent silent drift.
- Uninstall error diagnostics should include both what failed and where resolution should happen.
- Regression tests that cover both success and immediate retry-failure paths are effective for idempotency boundaries.

## Validation
- `python3 -m pytest tests --testmon -k test_feature74_uninstall_metadata_and_errors`
