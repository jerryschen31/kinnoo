# Feature43 Notes

## Intent
Feature43 is the auth and identity prerequisite for remote registry server/web UI. It codifies bootstrap admin, user/tenant management, JWT, and session security.

## Scope Implemented in Planning
- Added feature43 in `FEATURES.txt`
- Added tasks `task234`-`task238`
- Added tests `test332`-`test336`

## Policy Decisions Captured
- Bootstrap creates first admin once, then bootstrap disabled.
- Admin-only creation of users and tenants in V1.
- Tenant slug is user-chosen and globally unique.
- No self-signup in V1.
- Short-lived JWT tokens for API auth.

## Task-by-Task Implementation Guidance

### task234
- Implement user model and password hashing (argon2 preferred).
- Keep persistent storage through shared storage abstraction.
- Add secure password verification utilities.

### task235
- Provide one-time bootstrap command for first admin.
- Output temporary credential once and force password change.
- Refuse bootstrap after admin exists.

### task236
- Implement tenant model and slug validator.
- Enforce uniqueness and admin-only tenant creation.
- Include visibility field for future policy controls.

### task237
- Implement token issuance endpoint and JWT validation middleware.
- Enforce route scopes (`registry:read`, `registry:publish`, `registry:admin`).
- Add denylist and signing-key rotation support.

### task238
- Implement web session auth and secure cookie handling.
- Add CSRF generation/validation and server-side invalidation.
- Enforce session TTL and logout/reset invalidation.

## Test Strategy
- `test332`: secure hashing and verification
- `test333`: bootstrap one-time behavior
- `test334`: tenant slug validation + admin-only controls
- `test335`: JWT lifecycle, scopes, denylist, rotation
- `test336`: session security and CSRF/invalidation

## SWE Risks
- Bootstrapping logic accidentally re-runnable
- Weak scope enforcement allowing privilege escalation
- Session/token invalidation race cases

## SWE Done Checklist
- Bootstrap path closes after first admin
- Admin-only user/tenant creation enforced in API layer
- JWT and session flows both fully covered by tests
- No secret values emitted in logs or errors

## Tech Lead Review 1

### Verdict
- Status: changes requested (not approved for merge gate)
- Reason: one acceptance criterion is not fully implemented yet, and one is only partially evidenced at service/store level.

### Findings (ordered by severity)
- High: AC4 requires POST /api/auth/token endpoint behavior, but no API route implementation was found in server code.
	- Evidence: token issuance currently exists as service logic only in server/auth/token.py and is exercised directly by unit tests in server/tests/test_jwt_auth.py.
	- Impact: feature-level contract is incomplete for API consumers.
	- Required fix: add the auth endpoint and wire validation/error semantics (200 on valid creds, 401 on invalid creds, default TTL behavior).
- Medium: AC5 states admin-only creation via admin API endpoints, but enforcement is currently verified through storage/service paths and tests, not endpoint handlers.
	- Evidence: enforcement logic in tenant/user creation paths is present; no admin endpoint implementation was found in this feature scope.
	- Impact: policy is not yet validated at API boundary where authorization bypass risk is highest.
	- Required fix: implement admin create-user/create-tenant endpoints and add endpoint-level authorization tests.

### Security/Secret-Leak Check (server/)
- Broad keyword scan completed across server code.
- High-signal credential signature scan completed (AWS/GitHub/Slack/Google/private-key signatures).
- Result: no leaked real credentials or private keys found.
- Notes: test fixtures include synthetic secrets/password strings, which is acceptable for tests; no production secret literals were identified.

### Test Gate
- Required command executed: python3 -m pytest --testmon
- Result: 5 passed in 0.40s
- Executed tests:
	- server/tests/test_bootstrap.py
	- server/tests/test_jwt_auth.py
	- server/tests/test_session_auth.py
	- server/tests/test_tenant_model.py
	- server/tests/test_user_model.py

### AC Coverage Assessment
- AC1: pass (user model + hashed password behavior validated)
- AC2: pass (bootstrap one-time flow validated)
- AC3: pass (tenant slug validation + uniqueness + admin-only creation logic validated)
- AC4: fail (endpoint contract not implemented yet)
- AC5: partial (authorization present in lower layers; endpoint boundary coverage pending)
- AC6: pass (session + CSRF + invalidation behavior validated)
- AC7: pass (denylist + key rotation validated)
- AC8: pass (tests run without external services)

### Release Decision
- Feature43 is not approved in this review iteration.
- Minor version bump and changelog update are deferred until AC4/AC5 endpoint-level completion and re-review.

## SWE agent - AC4 AC5 remediation

### What was added
- Added explicit API endpoint handlers in [server/api/endpoints.py](server/api/endpoints.py):
	- POST /api/auth/token via post_auth_token(...)
	- POST /api/admin/users via post_admin_create_user(...)
	- POST /api/admin/tenants via post_admin_create_tenant(...)
- Added API package marker in [server/api/__init__.py](server/api/__init__.py).

### AC4 coverage update
- Implemented POST /api/auth/token behavior in endpoint handler:
	- accepts username+password payload
	- returns 200 with signed JWT and ttl-derived expires_in on valid credentials
	- returns 401 on invalid credentials
- Added endpoint assertions to mapped test335 in [server/tests/test_jwt_auth.py](server/tests/test_jwt_auth.py).

### AC5 coverage update
- Implemented admin API endpoint authorization boundary checks:
	- create user endpoint requires registry:admin scope
	- create tenant endpoint requires registry:admin scope
	- non-admin token attempts are rejected with 403
- Added endpoint assertions to mapped test334 in [server/tests/test_tenant_model.py](server/tests/test_tenant_model.py).

### Re-test results
- python3 -m pytest server/tests/test_jwt_auth.py::test_jwt_lifecycle server/tests/test_tenant_model.py::test_tenant_slug_management
- Result: 2 passed

### Recommendation for TechLead re-review
- AC4 should now be marked implemented at endpoint boundary.
- AC5 should now be marked implemented at endpoint boundary.
- Conditional deferral is no longer required for these two AC items.

## AC4 and AC5 Implementation Notes

### AC4: POST /api/auth/token
- Implemented endpoint handler in [server/api/endpoints.py](server/api/endpoints.py) as `post_auth_token(...)`.
- Request contract:
	- accepts `username`, `password`, optional `tenant_slug` (defaults to `global`).
- Response contract:
	- `200` with `access_token`, `token_type=Bearer`, and `expires_in` derived from token TTL.
	- `401` for invalid credentials.
	- `400` for malformed payloads.
- Validation evidence:
	- endpoint-path assertions added to mapped test335 in [server/tests/test_jwt_auth.py](server/tests/test_jwt_auth.py).

### AC5: Admin-only user and tenant creation endpoints
- Implemented endpoint handlers in [server/api/endpoints.py](server/api/endpoints.py):
	- `post_admin_create_user(...)` for POST `/api/admin/users`
	- `post_admin_create_tenant(...)` for POST `/api/admin/tenants`
- Authorization behavior:
	- requires `registry:admin` scope via auth middleware token validation.
	- non-admin caller receives `403`.
	- malformed payloads return `400`.
	- duplicate/invalid domain operations return `409` where applicable.
- Validation evidence:
	- endpoint-path assertions added to mapped test334 in [server/tests/test_tenant_model.py](server/tests/test_tenant_model.py).

### Focused Re-test
- `python3 -m pytest server/tests/test_jwt_auth.py::test_jwt_lifecycle server/tests/test_tenant_model.py::test_tenant_slug_management`
- Result: `2 passed`
