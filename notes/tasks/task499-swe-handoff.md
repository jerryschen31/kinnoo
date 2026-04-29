# Task499 SWE Handoff - CLI Login/Logout/Refresh Migration

## Objective
Move CLI auth from direct credential flow to hosted auth with robust refresh/logout behavior.

## Contract
- `kinnoo login` stores access token, refresh token, expiry metadata, and tenant context.
- Refresh executes before expiry-sensitive registry calls.
- `kinnoo logout` clears local auth state and keeps graceful no-state behavior.

## Primary Files
- `src/kinnoo/auth_command.py`
- `src/kinnoo/config.py`
- `src/kinnoo/registry.py`

## Required Tests
- `test710`
- `test711`

## Execution Guidance
1. Keep command UX deterministic and actionable on failures.
2. Encapsulate provider interactions in one CLI auth service boundary.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest tests/client_cli_registry -q -k "login or logout or refresh or feature118"`
