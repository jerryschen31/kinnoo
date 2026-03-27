# Task 321 Notes

## Summary
Implemented `POST /api/auth/register-confirm` with token validation, single-use enforcement, user provisioning, local identity mapping, deterministic tenant slug collision handling, and authenticated session cookie issuance.

## What was implemented
- Added SQLite-backed auth helper store:
  - server/storage/sqlite_auth_store.py
  - consumed registration tokens
  - tenant slug reservation (`base`, `base-1`, `base-2`...)
  - local identity upsert (`provider=local`)
- Extended registration token service:
  - server/auth/tokens.py
  - token verification + expiry checks
  - stable token hashing for single-use consumption checks
- Added server-side registration password baseline validation:
  - server/auth/password_policy.py
  - 10-128 length requirements
- Wired auth store into app state and auth router:
  - server/app.py
- Implemented `/api/auth/register-confirm` endpoint:
  - server/routes/auth.py
  - validates JSON, password policy, token signature/expiry
  - marks token consumed (replay-safe)
  - creates user (hashed password via existing user model)
  - creates local identity and tenant slug with suffix collision policy
  - creates session and sets `kinnoo_session` + `kinnoo_csrf` cookies

## Tests implemented and run
Task-linked tests:
- test472: register-confirm success creates user+tenant+session cookies
- test473: expired/consumed token rejection
- test486: deterministic tenant slug suffix allocator

Command run:
- python3 -m pytest tests --testmon -k "test_feature58_register_confirm_success_creates_user_tenant_session or test_feature58_register_confirm_rejects_expired_or_used_token or test_feature58_tenant_slug_collision_suffix_allocator"

Result:
- 3 passed
- 0 failed

## Smoke-test note
- `notes/tasks/task321-smoke-tests.md` exists and its key end-user checks (signup/verify completion, cookie/session issuance, slug collision behavior) are covered by the automated task tests above.

## Teaching notes
- Single-use token enforcement should happen before expensive account-creation side effects to prevent replay races.
- Deterministic slug allocation becomes reliable only when uniqueness is enforced at the persistence layer (not only in app logic).
- Setting both session and CSRF cookies at account-creation time keeps initial post-registration UX consistent with existing authenticated flows.
- Keeping token verify/consume logic separate from route code improves testability and reduces security regressions in future auth changes.
