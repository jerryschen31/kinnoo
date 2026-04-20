# Task497 Notes

## Summary
- Added provider-portable OIDC server adapter/service (`server/auth/oidc.py`) for JWT validation, login URL generation, token exchange, and userinfo/JWKS operations.
- Added auth-provider selection in `server/app.py` with fail-fast env validation when `AUTH_PROVIDER=oidc_kinde`.
- Updated `server/routes/web_auth.py` to support redirect/callback/logout OIDC flow while preserving legacy behavior when OIDC provider is not enabled.
- Added `server/tests/test_feature118_oidc_auth.py` for OIDC token acceptance/rejection envelopes and provider fail-fast behavior.

## Teaching Notes
- Keep auth architecture stable by isolating provider-specific logic in one adapter and making middleware depend on a shared token-validation contract.
- JWT validation for OIDC should always include signature + issuer + audience + time-claim checks (`exp`, `nbf`, `iat`), not just signature.
- Fail-fast config checks reduce runtime ambiguity and make CI failures easier to diagnose.
