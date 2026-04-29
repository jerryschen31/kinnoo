# task525 implementation notes

- Added `scripts/ops/create_registry_database_url_stub_secret.sh`: idempotent bootstrap script that writes a clearly-marked placeholder JSON value (`{"REGISTRY_DATABASE_URL":"postgresql+psycopg://REGISTRY_DATABASE_URL_STUB_PLACEHOLDER:..."}`) to `/<project>/<env>/REGISTRY_DATABASE_URL` so the first `terraform apply` (which references the secret via a `data "aws_secretsmanager_secret"` block in `iac/modules/secrets/main.tf`) does not fail because the secret name is missing. After RDS exists, `scripts/ops/refresh_registry_database_url_secret.sh` replaces the placeholder with the real connection string.
- Behavior contract:
  1. Secret missing → create with placeholder JSON.
  2. Secret exists with placeholder marker → no-op.
  3. Secret exists with non-placeholder (real) value → refuse to overwrite, exit 0 (so it's safe to re-run any time).
- Supports `--environment`, `--project-name`, `--region`, and `--dry-run`. Tags the secret with `Project`/`Environment`/`ManagedBy=bootstrap-script`.
- Test coverage: `tests/iac/test_feature121_db_url_stub_secret.py` (test748). Uses a Python AWS shim to simulate Secrets Manager state across three runs (create → no-op → refuse-to-overwrite-real-value) to lock in the contract without touching real AWS.
