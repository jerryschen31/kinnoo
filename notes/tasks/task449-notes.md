# Task 449 Notes

## Summary
Implemented CLI auth hardening for feature61: login now uses server-resolved tenant context, `list/search --remote` are fail-closed with explicit guidance, and logout behavior remains auth-clearing and blocks remote operations until re-login.

## What changed
- Updated `src/kinnoo/auth_command.py`:
  - `login` now requests token without client-side tenant guessing.
  - tenant slug is persisted only when discovered from token claims.
  - login fails with clear diagnostics if tenant context is missing from auth response.
- Updated `server/api/endpoints.py` and `server/auth/token.py`:
  - `tenant_slug` became optional in `/api/auth/token` payload.
  - non-admin token issuance derives tenant from identity server-side.
  - admin token issuance preserves explicit tenant override (default `global`) to keep publish bypass behavior.
- Updated `src/kinnoo/list_command.py` and `src/kinnoo/search_command.py`:
  - removed remote fallback to local mock storage when registry URL is missing.
  - added actionable remediation messages for missing registry URL and missing auth state.
- Updated docs in `README.md`:
  - documented fail-closed remote mode and auth/tenant persistence behavior.
- Updated `scripts/add-dev-user.sh`:
  - added deterministic password set options via `--password` or `--password-env` after user creation.
  - supports local and ECS mode password reset/unlock flows without printing secrets.

## Test coverage updates
- Updated `tests/test_cli_registry.py`:
  - login test now validates tenant discovery from token claims (not email-derived fallback).
  - added `test_feature61_hardened_login_logout_remote_auth_gating` (test609 automation path).
  - adjusted mirror attribution test to use explicit remote config stubbing instead of removed remote fallback.
- Updated `tests/test_cli_registry_modes.py` and `tests/test_pack_size_reporting.py`:
  - switched remote-mode fixtures to explicit authenticated HTTP stubs.
  - kept local/default assertions in local-only envs to avoid auto-remote mode from configured URL.

## Targeted validation runs
- `python3 -m pytest tests/test_cli_registry.py --testmon -k "feature61"` -> passed (3 selected)
- `python3 -m pytest tests/test_cli_registry_modes.py --testmon -k "list_default_local_and_remote_modes or search_default_local_and_remote_modes or source_mode_argument_validation_errors"` -> passed (3 selected)
- `python3 -m pytest tests/test_pack_size_reporting.py --testmon -k "list_includes_archive_size"` -> passed (1 selected)
- `python3 scripts/validate_project_manifests.py` -> passed

## Teaching notes
- Auth should be fail-closed at trust boundaries. In CLI registry flows, explicit remote intent (`--remote`) should never silently degrade into local behavior.
- Tenant resolution belongs in the server trust domain, not in the client heuristics domain. Client-side derivation works for prototypes but becomes brittle once identity/tenant mapping evolves.
- Preserve privileged automation escape hatches (`publish_to_authenticated_registry`) deliberately and test them explicitly when tightening default auth behavior.
