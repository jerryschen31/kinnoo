# Phase 14 - Fix token not getting email tenant slug

Date: 2026-04-21
Scope: Hosted OIDC auth parity across CLI login, server publish ownership, and web UI tenant identity.

## Problem
After OIDC rollout, users could see:
- `kinnoo login` showing an email-derived tenant slug (for example `jerryschen`).
- Remote publish/listed registry ownership still appearing as `org_...`.

This created cross-surface identity drift (CLI/login vs publish/registry records).

## Root Cause
Two related causes were identified:

1. Token claim shape variability
- Access tokens in the affected environment often contained `org_code` but not `email` and not `tenant_slug`.
- Existing claim-based tenant fallback naturally resolved to `org_...`.

2. Resolution path mismatch between surfaces
- CLI hosted login was updated to derive tenant slug from OIDC userinfo email (web-parity behavior).
- Server publish authorization relied on token claims and therefore could still resolve to `org_code` when `email` was absent.

## Fixes Implemented
### 1) CLI/web parity improvements
- Hosted CLI tenant resolution now prefers userinfo email before token claim fallbacks.
- Login CLI surface was simplified to hosted flow only (legacy `--email/--password` removed).

### 2) Auth env loader hardening
- Updated auth environment loader to also fetch/export userinfo endpoint under both names:
  - `AUTH_USERINFO_ENDPOINT`
  - `USERINFO_ENDPOINT`
- This prevents shells from silently missing the endpoint required for email-based tenant derivation.

### 3) Server-side publish tenant consistency fix
- Updated OIDC token validation path so that when token `email` is missing, server attempts userinfo lookup and augments payload with email before resolving tenant slug.
- Tenant resolution now prioritizes email-derived slug semantics for identity parity, then falls back to org-based claims when email is unavailable.

## Files Changed (phase scope)
- `src/kinnoo/auth_command.py`
- `src/kinnoo/cli.py`
- `scripts/load_kinnoo_auth_env.sh`
- `server/auth/oidc.py`
- `tests/client_cli_registry/test_feature118_cli_auth.py`
- `tests/client_cli_registry/test_cli_registry.py`
- `tests/client_cli_pack/test_pack.py`
- `tests/client_cli_publish/test_publish_command.py`
- `server/tests/test_feature118_oidc_auth.py`
- `docs/cli-reference.md`
- `docs/registry-guide.md`

## Validation Performed
- Verified `kinnoo login -h` no longer exposes deprecated password flags.
- Verified JS/TS pack and publish --pack do not require `requirements.txt`.
- Verified token payload inspection in local shell demonstrated real env condition (`org_code` present, email absent), confirming why server-side userinfo fallback was required.
- Performed syntax validation on patched OIDC server files.

## Operational Outcome
After rebuilding and redeploying server image/tasks with updated code and env wiring:
- Tenant identity now resolves consistently across login + publish + registry display.
- Previously observed `org_...` tenant drift issue is resolved in the working environment.

## Follow-ups
- Keep `AUTH_USERINFO_ENDPOINT` and alias wiring in all deployment environments.
- Keep server/userinfo fallback tests as a regression guard for providers/tokens that omit email claims.
- Continue monitoring OIDC claim shape differences between environments during future auth changes.
