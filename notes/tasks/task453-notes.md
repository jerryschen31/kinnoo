# task453 Notes

## Summary
- Updated top-level help banner to show CLI branding with icon, version, and short commit hash:
  - `🍊 Kinnoo CLI v<version> (<short-hash>)`
- Added resilient hash resolution helper that uses `git rev-parse --short HEAD` and falls back to `unknown` when git metadata is unavailable.
- Added regression test `tests/test_cli.py::test_help_shows_version_hash_icon` validating the first help-line format.

## Files changed
- `src/kinnoo/cli.py`
- `tests/test_cli.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests --testmon -k test_help_shows_version_hash_icon` (blocked by unrelated syntax error in `tests/test_feature_96.py` during collection)
  - `python3 -m pytest tests/test_cli.py --testmon -k test_help_shows_version_hash_icon`
- Result:
  - `1 passed, 91 deselected`

## Teaching notes
- A user-facing CLI banner should avoid hard failures when VCS metadata is missing; using a safe fallback (`unknown`) keeps help output deterministic in source tarballs and CI artifacts.
- Restrict regex assertions to the specific contract line to avoid brittle tests against broader help text layout.
