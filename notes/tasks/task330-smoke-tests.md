# Task 330 Smoke Tests

## Goal
Validate Sub-phase 5 integration end-to-end and ensure no regression in existing auth flows.

## Preconditions
- All Sub-phase 5 backend and frontend tasks merged in branch.
- SQLite auth store configured for development.

## Manual smoke checks
1. Run complete registration flow: /signup -> /signup/verify -> /registry.
2. Log out and run forgot-password flow: /forgot-password -> /forgot-password/reset -> /login.
3. Verify reset invalidates old sessions and allows login with new password only.
4. Verify duplicate-safe behavior:
   - register-request responses do not reveal account existence.
   - reset-request responses do not reveal account existence.
5. Verify tenant slug collision handling by registering users with same email prefix.
6. Verify baseline login and registry browsing still work after Sub-phase 5 changes.

## Pass criteria
- Registration and reset flows work for end users with expected security controls.
- Existing login/registry flow remains functional without regressions.
