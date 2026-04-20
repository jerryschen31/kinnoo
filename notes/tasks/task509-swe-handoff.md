# Task509 SWE Handoff - Backfill, Parity, and Rollback Gates

## Objective
Build migration tooling from JSON metadata to Postgres plus deterministic parity checks and rollback gate validation.

## Deliverables
- Idempotent backfill script(s) for metadata migration.
- Deterministic parity checker (counts/key fields/hash consistency outputs).
- Rollback drill support using backend flag switch and health verification.

## Task Contracts
- Re-running backfill must not duplicate/corrupt records.
- Parity output must be stable and diff-friendly for gate checks.
- Cutover gate criteria must be explicit and automatable.

## Validation
- Run backfill twice and verify idempotency.
- Produce zero-mismatch parity report for controlled fixture set.
- Validate rollback switch to json backend with healthy service state.
