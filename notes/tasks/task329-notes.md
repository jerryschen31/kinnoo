# Task329 Notes

## Scope completed
- Added transparent rehash-on-login behavior for legacy password hashes in web auth login flow.
- Added password manager rehash policy detection helper.
- Kept rate limiting and password-policy hardening active on auth entrypoints and validated those paths with task-linked regressions.

## Tests added and coverage
- `tests/test_registry.py::test_feature60_rehash_on_login_for_legacy_hash`
  - Seeds a legacy scrypt hash, performs successful login, and verifies password hash upgrade behavior.

## Targeted regression command and result
Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 -m pytest tests --testmon -k "test_feature58_register_confirm_rejects_expired_or_used_token or test_feature59_password_reset_request_rate_limit or test_feature59_password_policy_rejects_compromised_or_similar or test_feature60_rehash_on_login_for_legacy_hash"
```

Result:
```text
4 passed
445 deselected
```

## Teaching notes
- Rehash-on-login is an incremental migration strategy: users upgrade cryptographic strength naturally during normal authentication without forced password reset campaigns.
- A practical policy boundary is: verify with legacy hash formats, then rewrite to preferred format only after successful credential verification.
- Keep hardening tests mixed across old/new endpoints to catch regressions where newly added security controls might accidentally diverge by flow.
