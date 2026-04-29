# Task500 SWE Handoff - Internal Identity Mapping and Publish Ownership

## Objective
Preserve kinnoo-owned UUID identity while mapping external provider subject and tenant context for publish ownership.

## Contract
- Internal user PK remains UUID-based.
- External subject (`sub`) remains mapped attribute, not internal PK.
- Publish ownership persists mapped internal identity and tenant linkage.

## Primary Files
- `server/routes/publish.py`
- `server/storage/`
- `server/services/`

## Required Tests
- `test712`

## Execution Guidance
1. Add deterministic upsert/linking behavior for first-authenticated requests.
2. Validate multi-user and multi-tenant ownership scenarios.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest server/tests -q -k "publish and feature118"`
