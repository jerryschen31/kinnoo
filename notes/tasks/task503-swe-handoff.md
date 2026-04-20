# Task503 SWE Handoff - Auth Portability and Integration Test Expansion

## Objective
Expand automated auth coverage across server/web/CLI flows and provider-portability adapter contracts.

## Contract
- Server token and callback/logout error-path contracts are covered.
- CLI login/logout/refresh behavior is covered.
- Web redirect/callback/protected-layout behavior is covered.
- Adapter portability tests run with mocked discovery/JWKS.

## Primary Files
- `server/tests/`
- `tests/client_cli_registry/`
- `tests/e2e_workflows/`
- `web/__tests__/`

## Required Tests
- `test715`

## Execution Guidance
1. Keep test assertions contract-focused and deterministic.
2. Ensure markers and automation paths are aligned with TESTS manifest entries.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest server/tests tests/client_cli_registry tests/e2e_workflows -q -k "feature118 or auth"`
