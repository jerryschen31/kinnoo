# Task497 SWE Handoff - Server OIDC Auth Adapter and Route Cutover

## Objective
Cut server auth over to provider-portable OIDC validation and redirect/callback/logout auth flow behavior.

## Contract
- Validate JWTs via discovery + JWKS with issuer/audience/expiry/scope checks.
- Keep provider-specific behavior inside a server adapter boundary.
- Preserve stable error envelope semantics on auth failures.

## Primary Files
- `server/auth/`
- `server/routes/auth.py`
- `server/routes/web_auth.py`
- `server/auth/middleware.py`
- `server/app.py`

## Required Tests
- `test707`
- `test708`

## Execution Guidance
1. Implement adapter boundary first, then wire routes/middleware.
2. Remove direct dependency on legacy username/password token paths.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest server/tests -q -k "auth or oidc"`
