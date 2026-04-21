# Postgres Registry Operations Runbook

## Alarm Definitions
- **CPUUtilization** alarm: trigger at >75% for 2 periods (5m).
- **FreeStorageSpace** alarm: trigger below 2GiB for 2 periods (5m).
- **DatabaseConnections** alarm: trigger above 80 for 2 periods (5m).
- **ReadLatency** alarm: trigger above 200ms average for 3 periods (1m).
- Alarm notifications route to the configured `sns_topic_arn` and are owned by the registry on-call operator.

## Cutover Runbook
1. Confirm `alembic upgrade head` succeeds in target environment.
2. Execute JSON-to-Postgres backfill (`scripts/postgres_backfill.py`) and parity report (`scripts/postgres_parity.py`).
3. Verify parity mismatch count is zero.
4. Set `REGISTRY_METADATA_BACKEND=postgres` and restart service.
5. Validate `/ready` returns `db=true`.

## Rollback Runbook
1. Set `REGISTRY_METADATA_BACKEND=json`.
2. Restart service and validate `/ready` reports healthy checks.
3. Confirm publish/list/search paths remain functional.
4. Keep Postgres data unchanged for forensic analysis.

## Restore / PITR Runbook
1. Restore latest automated snapshot or perform point-in-time restore from AWS RDS.
2. Point `REGISTRY_DATABASE_URL` to restored instance.
3. Run parity checks against JSON baseline before re-enabling postgres mode.
4. Record incident timeline and owner in ops notes.

## Connection Saturation Response
1. Check `DatabaseConnections` alarm and app logs.
2. Temporarily raise ECS task count or reduce write load.
3. Tune `REGISTRY_DB_POOL_SIZE` and `REGISTRY_DB_MAX_OVERFLOW`.
4. If saturation persists, roll back to JSON backend and escalate to DB owner.

## Runtime Resilience Expectations
- In postgres mode, startup is fail-fast when DB is unreachable.
- Health/readiness endpoints include DB ping results in postgres mode.
- Runtime DB outages return deterministic error responses; requests must not hang indefinitely.
