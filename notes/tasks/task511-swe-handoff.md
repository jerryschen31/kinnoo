# Task511 SWE Handoff - Postgres Test Harness (Local + CI)

## Objective
Enable reliable Postgres-backed testing in local dev and CI with isolation and concurrency sanity coverage.

## Deliverables
- Local Docker Compose Postgres workflow.
- CI Postgres service-container wiring.
- Transaction rollback fixtures for isolation.
- Concurrency sanity tests for publish/search and pool behavior.

## Task Contracts
- Tests must not leak DB state between cases.
- CI must run Postgres-backed tests reproducibly.
- Concurrency sanity checks should catch lost-write/duplicate-version regressions.

## Validation
- Run targeted Postgres integration suite locally.
- Verify CI workflow config includes Postgres services and required env.
