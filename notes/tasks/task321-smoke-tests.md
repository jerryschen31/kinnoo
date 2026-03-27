# Task 321 Smoke Tests

## Goal
Validate end-to-end registration confirmation with relational persistence and deterministic tenant slug allocation.

## Preconditions
- Server running with SQLite auth store enabled for development.
- FRONTEND_URL and auth token secrets are configured.
- A valid verification token is available from register-request flow.

## Manual smoke checks
1. Complete /signup and submit a valid email.
2. Use verification token to open /signup/verify and submit a valid password (10+ chars).
3. Confirm redirect lands on /registry and session cookie is set.
4. Inspect auth DB records:
   - user row exists for email
   - identity row exists for local provider mapping
   - tenant row exists with derived slug
5. Repeat registration for a second email with same prefix and confirm slug suffix is allocated (e.g., base-1).

## Pass criteria
- Registration confirmation creates user, identity, tenant, and session records.
- Slug collisions are resolved deterministically without uniqueness errors.
