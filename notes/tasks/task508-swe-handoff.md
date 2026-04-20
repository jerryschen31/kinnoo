# Task508 SWE Handoff - Metadata Backend Integration and Health Wiring

## Objective
Integrate `PostgresMetadataManager` behind `REGISTRY_METADATA_BACKEND` while preserving existing metadata behavior and enabling DB-aware health checks.

## Deliverables
- `PostgresMetadataManager` implementing current metadata manager interface.
- Backend flag wiring in config/app bootstrapping (`json` default, `postgres` opt-in).
- DB ping path in health/readiness endpoints for postgres mode.

## Task Contracts
- No behavior regression for json backend default path.
- Postgres mode should fail fast on startup when DB unavailable.
- Runtime outage behavior must be explicit/deterministic (no hanging requests).

## Validation
- Compare metadata behavior under json vs postgres modes.
- Validate health/readiness and startup failure behavior in postgres mode.
