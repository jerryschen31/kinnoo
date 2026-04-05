# Task 391 Notes

## Summary
Implemented task391 for feature90 by adding server-side integrity manifest enforcement in the upload pipeline:
- Added META-INF/integrity.json verification in server/routes/publish.py.
- Integrity checks now validate, when manifest is present:
  - integrity.json is valid JSON with a files mapping
  - each manifest-listed file exists in archive
  - each file size matches manifest size
  - each SHA-256 hash matches manifest sha256
  - archive has no extra non-META-INF files beyond manifest entries
- Integrity failures now reject upload with HTTP 400 and descriptive error detail.

Also expanded tests/test_feature_90.py::test_feature90_group2 to cover:
- successful publish for valid archive
- tampered integrity manifest hash mismatch returns 400 with JSON error payload

## Tests Run
- python3 -m pytest --testmon tests/test_feature_90.py::test_feature90_group2
- Result: 1 passed

## Smoke Tests
- notes/tasks/task391-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Integrity validation should happen before storage writes:
  - rejecting tampered archives early prevents poisoned artifacts in registry storage.
- Validate both completeness and exactness:
  - checking missing files alone is not enough; extra files can also indicate tampering.
- Keep validation deterministic:
  - explicit, first-failure error messages make support and incident triage faster.
