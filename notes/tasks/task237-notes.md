# Task237 - feature43 JWT access token issuance and validation

## Summary
- Added token issuance and validation module in server/auth/token.py:
  - HMAC-SHA256 JWT-compatible signing with configurable signing key and kid header.
  - Claims contract implemented: iss, sub, tenant_slug, scopes, token_id, exp, iat.
  - Short-lived token support via configurable ttl_minutes (default 60).
  - Credential-to-token flow via issue_token_for_credentials(...) using UserStore.
  - Role-based scope assignment:
    - admin -> registry:read, registry:publish, registry:admin
    - user -> registry:read
  - Token denylist support via revoke_token_id(...) for emergency revocation.
  - Key-rotation validation support with current key plus previous key fallback behavior.
- Added auth middleware helper in server/auth/middleware.py:
  - authenticate_request(...) parses Bearer token, validates token, and enforces required scope.
  - Unauthorized paths return 401-style PermissionError messages.
  - Missing scope returns 403-style PermissionError messages.
- Added mapped test335 in server/tests/test_jwt_auth.py:
  - test_jwt_lifecycle verifies issuance, invalid credentials (401), protected validation success,
    expiration rejection (401), missing scope rejection (403), denylist revocation, and key-rotation fallback.

## Tests and results
- python3 -m pytest server/tests/test_jwt_auth.py::test_jwt_lifecycle -> 1 passed

## Bug/error notes
- No bug/error class required iterative fixes for task237.
- Same bug/error class fix attempts: 0 (cap: 5).

## Teaching notes
- JWT implementation is easier to audit when token concerns are split into three layers: encoding/signing, claim validation, and request-level scope enforcement.
- kid-based key rotation should not rely only on exact-kid lookup; controlled fallback to previous trusted key helps avoid accidental auth outages during rollout windows.
- Denylist checks should happen after signature validation but before scope evaluation so revoked tokens never reach authorization logic.
- Deterministic error semantics (401 for invalid/expired/revoked, 403 for missing scope) keep middleware behavior stable for future API integration tests.
