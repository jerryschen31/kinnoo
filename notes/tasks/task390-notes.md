# Task 390 Notes

## Summary
Implemented task390 for feature90 by adding fail-fast server-side upload validation in server/routes/publish.py:
- Oversized payloads now return HTTP 413 (was 400).
- Invalid zip payloads now return explicit 400 validation error.
- Archives missing kinnoo.yaml now return explicit 400 validation error.
- kinnoo.yaml now enforces required non-empty fields: name, version, framework.
- Validation logic is now centralized in _validate_archive_and_manifest().

Also added feature test scaffold in tests/test_feature_90.py and implemented group1 checks for:
- oversized upload rejection
- invalid zip rejection
- missing kinnoo.yaml rejection
- missing framework rejection

## Tests Run
- python3 -m pytest --testmon tests/test_feature_90.py::test_feature90_group1
- Result: 1 passed

## Smoke Tests
- notes/tasks/task390-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Validation order matters:
  - Cheap checks (size, format) should run before expensive checks (manifest parsing, integrity verification).
- Use specific error messages for faster operator debugging:
  - Distinguishing “not zip” vs “missing kinnoo.yaml” cuts triage time significantly.
- Keep parsing and policy separate:
  - A helper that returns structured validation results makes future additions (integrity checks, signature checks) easier.
