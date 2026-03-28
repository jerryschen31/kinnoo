# Task325 Notes

## Scope completed
- Added `POST /api/auth/password-reset-confirm` endpoint.
- Endpoint validates signed reset token integrity/expiry, enforces single-use token consumption, applies server-side password policy checks, updates stored password hash, and invalidates all active sessions for the target user.
- Extended registration-confirm flow to also enforce common-password and email-similarity policy checks.
- Added SQLite consumed-token persistence for password-reset token replay prevention.

## Tests added and coverage
- `tests/test_registry.py::test_feature59_password_reset_confirm_success_invalidates_sessions`
  - Verifies successful reset updates password and invalidates active sessions.
- `tests/test_registry.py::test_feature59_password_reset_confirm_invalid_token`
  - Verifies expired/malformed/consumed token rejection behavior.
- `tests/test_registry.py::test_feature59_password_policy_rejects_compromised_or_similar`
  - Verifies compromised/common password rejection in register-confirm and similar-password rejection in reset-confirm.
- `tests/test_registry.py::test_feature59_password_reset_invalidates_all_relational_sessions`
  - Verifies all session records for the user are invalidated after successful reset.

## Targeted regression commands and results
Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 -m pytest tests --testmon -k "test_feature59_password_reset_confirm_success_invalidates_sessions or test_feature59_password_reset_confirm_invalid_token or test_feature59_password_policy_rejects_compromised_or_similar or test_feature59_password_reset_invalidates_all_relational_sessions"
```
Result:
```text
4 passed
440 deselected
```

Smoke-related command:
```bash
cd /Users/jerry/gh/kinnoo/web && npm run test -- __tests__/forgot-password-reset-page.test.tsx
```
Result:
```text
1 file passed
2 tests passed
```

## Teaching notes
- Single-use reset tokens should be backed by persisted consumed-state, not only in-memory checks, to remain safe across process restarts and horizontal scaling.
- Password-reset security should pair credential rotation with session revocation. Rotating a password without invalidating sessions leaves active compromised sessions usable.
- Keep password policy checks centralized and reusable (`register-confirm` and `reset-confirm`) to prevent policy drift across auth entrypoints.
