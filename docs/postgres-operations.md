# Postgres Registry Operations Runbook

## Day-0 Dev DB Bring-Up (Terraform + Cutover)
1. Pre-create runtime secret names in AWS Secrets Manager (this Terraform stack references them as existing secrets):
   - `${project_name}/${environment}/REGISTRY_DATABASE_URL`
   - and any required auth secrets for your environment.
2. Confirm non-secret runtime defaults in Terraform env tfvars (dev recommended):
   - `registry_metadata_backend = "json"` (safe before cutover)
   - `registry_db_pool_size = 10`
   - `registry_db_max_overflow = 20`
   - `registry_db_pool_recycle_seconds = 1800`
3. Provision infra first:
   - `terraform init`
   - `terraform plan -var-file=environments/dev/terraform.tfvars`
   - `terraform apply -var-file=environments/dev/terraform.tfvars`
4. After apply, get:
   - DB endpoint from Terraform outputs.
   - DB username from RDS config (`kinnoo_admin` by default in this stack).
   - DB password from the RDS-managed master-user secret (RDS is configured with `manage_master_user_password = true`).
   Then build `REGISTRY_DATABASE_URL` for DB name `kinnoo_registry`.
5. Put/update the final `REGISTRY_DATABASE_URL` value in AWS Secrets Manager.
6. Ensure runtime access before app cutover:
   - ECS task role can read `REGISTRY_DATABASE_URL` secret.
   - Network path allows ECS -> RDS on `5432` (security groups/NACLs).
7. Initialize schema and migrate data:
   - Run `db migrate` / `alembic upgrade head`.
   - If moving from JSON metadata: run `scripts/postgres_backfill.py` then `scripts/postgres_parity.py`.
8. Cut over:
   - Set `REGISTRY_METADATA_BACKEND=postgres` (in Terraform env config).
   - Deploy/restart ECS service so new env + secret are loaded.
9. Validate dev DB is live:
   - `/ready` is healthy with DB checks passing.
   - Registry metadata create/read/update flows succeed.
   - RDS alarms/connections/latency are within expected thresholds.

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
