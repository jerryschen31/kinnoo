# Feature63 SWE Handoff

## Scope
- Feature: feature63
- Tasks: task336, task337
- Tests: test495, test496
- Dependencies: feature62

## Goal
Introduce ClawHub mirror storage and visibility model under tenant slug `clawhub` with explicit source attribution.

## Task Guidance

### task336
Key outcomes:
- Add mirror metadata model and upsert behavior.
- Persist mirrored records under tenant slug `clawhub`.
- Implement admin-controlled/public ownership model for `clawhub` tenant.
- Ensure this tenant is not a username/password login account.

### task337
Key outcomes:
- Surface source attribution and sync timestamps in search/inspect.
- Add idempotency guarantees for repeated mirror ingestion.
- Add regression tests for mirror query and labeling behavior.

## AC to Test Mapping
- AC1 -> test495
- AC2 -> test495
- AC3 -> test496
- AC4 -> test496

## Constraints
- Provenance must be unambiguous in all user-facing registry surfaces.
- Preserve deterministic upsert semantics across repeated sync runs.
