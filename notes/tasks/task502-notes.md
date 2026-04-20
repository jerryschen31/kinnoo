# Task502 Notes

## Summary
- Added legacy auth compatibility gating in `server/app.py` and `server/routes/auth.py`.
- Defaulted legacy password/register/reset API paths to disabled when OIDC provider mode is active.
- Added explicit compatibility override via `AUTH_ENABLE_LEGACY_PATHS=true` for controlled rollback scenarios.
- Added regression coverage in `server/tests/test_auth_route.py::test_feature118_legacy_auth_paths_disabled`.

## Teaching Notes
- Cutover safety works best when legacy behavior is explicit opt-in instead of implicit fallback.
- Compatibility gates should be narrow (only legacy endpoints) and observable through clear error messages.
- Keeping a rollback switch while defaulting it off balances migration safety with security hardening.
