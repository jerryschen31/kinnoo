# Task 389 Notes

## Summary
Implemented task389 for feature89 by enforcing production startup secrets and finalizing production runtime defaults:
- Added production startup guard in server/app.py:
  - create_app now raises ValueError in KINNOO_ENV=production when required secrets are missing:
    - REGISTRY_TOKEN_SIGNING_SECRET
    - REGISTRY_SESSION_SIGNING_SECRET
    - REGISTRY_REGISTER_TOKEN_SECRET
    - REGISTRY_PASSWORD_RESET_TOKEN_SECRET
- Ensured production uvicorn runtime config semantics in app state:
  - workers defaults to at least 2 in production
  - timeout_seconds remains 30
  - graceful_shutdown flag remains true
- Updated tests/test_feature_89.py::test_feature89_group2 to verify:
  - startup fails when required production secrets are missing
  - startup succeeds when secrets are present
  - uvicorn config reflects production defaults

## Tests Run
- python3 -m pytest --testmon tests/test_feature_89.py::test_feature89_group2
- Result: 1 passed

## Smoke Tests
- notes/tasks/task389-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Startup guards prevent insecure defaults from leaking into production:
  - Validating secrets at app boot is cheaper and safer than failing later under load.
- Keep production defaults explicit and testable:
  - Representing uvicorn settings as app state allows deterministic assertions in tests and easier runtime introspection.
- Write negative-path tests first for hardening work:
  - Verifying “fails when missing” prevents false confidence from only testing successful startup.
