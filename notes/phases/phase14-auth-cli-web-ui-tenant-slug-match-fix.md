# Phase 14 Auth CLI/Web UI Tenant Slug Match Fix

Date: 2026-04-20
Authoring context: Follow-up hardening after hosted OIDC CLI auth rollout and scope/audience stabilization.

## Problem Statement
Two user-facing issues remained after the earlier auth fixes:

1. Tenant slug mismatch between web UI and CLI login for the same user.
- Observed behavior: `kinnoo login` printed `Tenant: org_...` while web UI session behavior was email-derived.
- Expected behavior: tenant slug identity must be consistent across web and CLI for the same user email.

2. CLI help text still exposed deprecated username/password login flags.
- Observed behavior: `kinnoo login -h` showed `--email` and `--password`.
- Expected behavior: hosted login only, no password flag surface.

## Root Cause
### Tenant slug mismatch
- Web UI OIDC login path derives canonical username from OIDC `userinfo.email`, then maps to tenant slug using `username_to_tenant_slug`.
- CLI login was deriving tenant from token claims with fallback preference that could return `org_code` when token lacked email.
- Therefore the same user could resolve to different tenant slugs across surfaces.

### Stale CLI help surface
- Parser still declared legacy `--email` and `--password` options in `kinnoo login`, even though hosted login was now primary path.

## Implementation Summary
## 1) Canonical tenant slug alignment
File updated: `src/kinnoo/auth_command.py`

Changes:
- Added hosted login resolver that prefers OIDC userinfo identity for tenant derivation:
  - `_resolve_hosted_tenant_slug(...)`
  - `_tenant_slug_from_userinfo(...)`
- Hosted login flow now resolves tenant slug in this order:
  1. userinfo email -> email-based slug
  2. token email -> email-based slug
  3. token tenant_slug
  4. token org_code
  5. fallback `global`
- Removed env-flagged divergence for tenant slug source in token-only resolver, making default behavior deterministic and web-aligned.

Result:
- CLI and web both converge to email-derived tenant slug for the same user whenever OIDC userinfo email is available.

## 2) Hosted-only login help
File updated: `src/kinnoo/cli.py`

Changes:
- Removed parser args:
  - `--email`
  - `--password`
- Updated dispatch to call hosted login path without legacy arg dependency.

Result:
- `kinnoo login -h` now shows hosted-only usage:
  - `usage: kinnoo login [-h]`

## 3) Tests and docs updates
Files updated:
- `tests/client_cli_registry/test_feature118_cli_auth.py`
- `tests/client_cli_registry/test_cli_registry.py`
- `docs/cli-reference.md`
- `docs/registry-guide.md`

Test updates:
- Added userinfo-backed regression case to ensure token `org_code` does not override email-derived slug when userinfo email exists.
- Updated hosted login expectation where tenant resolves from userinfo email in test fixture.
- Removed legacy `--email/--password` invocation in touched CLI registry tests, switching to interactive input where applicable.

Doc updates:
- Removed non-interactive password-based login examples.
- Updated login usage text to hosted flow only.

## Validation Notes
- Focused CLI hosted auth suite passed after updates.
- Targeted login-flow tests passed/skipped as expected in local run set.
- Runtime help output verified:
  - `kinnoo login -h` no longer shows `--email` or `--password`.

## User Impact
- Consistent tenant identity context between web UI and CLI for the same email identity.
- Reduced auth confusion and fewer cross-surface permission mismatches caused by tenant slug drift.
- Cleaner and safer CLI UX by removing obsolete password options.

## Follow-up Recommendations
1. Add a small integration test that compares web callback-derived tenant slug and CLI hosted-login-derived tenant slug for the same mocked OIDC profile payload.
2. Ensure release notes call out hosted-only login surface change for users migrating from legacy password flow.
3. Keep an explicit compatibility note for operators if any automation still tries `kinnoo login --email/--password`.
