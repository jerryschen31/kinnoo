# Task 410 Notes

## Summary
Implemented task410 for feature100 by adding account-lockout behavior after repeated failed logins.

### Code changes
- server/models/user.py:
  - Added persistent fields for lockout tracking:
    - failed_login_attempts
    - locked_until
    - password_changed_at
- server/storage/user_store.py:
  - Added helpers:
    - increment_failed_login(...)
    - reset_login_failures(...)
- server/auth/token.py:
  - Updated credential issuance flow:
    - checks active lockout and rejects with 423 + retry_after
    - increments failed attempts on bad password
    - locks user after 5 failures for 15 minutes
    - clears expired lockout and resets counters after successful auth
- server/api/endpoints.py + server/routes/auth.py:
  - Plumbed 423 account_locked response semantics through API handler
  - Added retry_after details in error response payload
- tests/test_feature_100.py:
  - Added group1 test covering lockout trigger, 423 response, retry_after, lockout expiry clear

## Tests Run
- python3 -m pytest --testmon tests/test_feature_100.py::test_feature100_group1
- Result: 1 passed

## Smoke Tests
- notes/tasks/task410-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Lockout should be persisted with user records:
  - in-memory counters can be bypassed on process restart; persisted lockout state is safer.
- Keep auth error mapping explicit:
  - API handlers should map domain auth outcomes (401 vs 423) deterministically.
- Isolate interacting controls in tests:
  - rate limiting and lockout can interfere with each other, so tests should control request-source identity to test one behavior at a time.
