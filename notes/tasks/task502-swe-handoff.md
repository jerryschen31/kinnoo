# Task502 SWE Handoff - Legacy Auth Runtime Retirement and Compatibility Gating

## Objective
Retire or default-disable local password/session/reset runtime flows after OIDC cutover.

## Contract
- Legacy paths are removed or compatibility-gated with default OFF.
- Protected auth paths do not fallback to legacy auth by default.
- Compatibility behavior is explicit and controlled.

## Primary Files
- `server/auth/session.py`
- `server/auth/token.py`
- `server/storage/sqlite_auth_store.py`
- `server/routes/auth.py`

## Required Tests
- `test714`

## Execution Guidance
1. Remove implicit fallback paths first.
2. Add explicit compatibility controls only where operationally necessary.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest server/tests -q -k "legacy and auth and feature118"`
