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
