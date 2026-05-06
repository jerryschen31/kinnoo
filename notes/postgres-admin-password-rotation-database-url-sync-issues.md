# Postgres Admin Password Rotation and Database URL Sync Issues

## Original Problem
postgres admin password was being rotated but registry database URL, which contains the admin password in its string, was not updated, causing database access denied errors

## Response Explaining the Fix
Implemented. Rotation is now explicitly controlled by Terraform with per-environment tfvars toggles, and I added guardrails to keep the DB URL secret aligned during apply/deploy workflows.

What I changed

1. Added root Terraform variables for rotation control:
- iac/variables.tf
- New vars:
  - rds_master_secret_rotation_enabled
  - rds_master_secret_rotation_automatically_after_days
  - rds_sync_registry_database_url_on_rotation_apply

2. Wired those vars into the RDS module:
- iac/main.tf
- Passes aws_region + the three new rotation/sync vars into module.rds_postgres.

3. Added module-level enforcement with drift correction trigger:
- iac/modules/rds-postgres/variables.tf
- iac/modules/rds-postgres/main.tf
- Uses aws_secretsmanager_secret_rotation data source to observe current state.
- Uses terraform_data + local-exec to enforce desired state via script when desired/observed differ.

4. Added new enforcement script:
- scripts/ops/enforce-rds-master-secret-rotation.sh
- Idempotently:
  - enables/updates rotation schedule with rotate-secret when desired=true
  - disables rotation with cancel-rotate-secret when desired=false
- Optionally refreshes /kinnoo/<env>/REGISTRY_DATABASE_URL from current RDS master secret.

5. Added dev/prod tfvars toggles:
- iac/environments/dev/terraform.tfvars
- iac/environments/prod/terraform.tfvars
- Current defaults set to:
  - rds_master_secret_rotation_enabled = false
  - rds_master_secret_rotation_automatically_after_days = 7
  - rds_sync_registry_database_url_on_rotation_apply = true

6. Strengthened sync tooling:
- scripts/ops/sync-database-url.sh
- Now resolves the RDS master secret dynamically from DB instance identifier instead of hardcoded rds!db- IDs.
- Added:
  - --db-instance override
  - --fail-on-mismatch (exits non-zero on credential drift)

7. Added deploy-time sync guardrail:
- scripts/ops/rebuild_push_server_and_redeploy_ecs.sh
- Before image push/redeploy, it now:
  - checks REGISTRY_DATABASE_URL creds vs current RDS master secret
  - auto-refreshes if mismatched
  - fails if still mismatched after refresh attempt

Validation run

1. Shell syntax checks passed for:
- scripts/ops/enforce-rds-master-secret-rotation.sh
- scripts/ops/sync-database-url.sh
- scripts/ops/rebuild_push_server_and_redeploy_ecs.sh

2. Terraform validation passed:
- terraform -chdir=iac validate

How to use the new toggle

1. In each env tfvars file, set:
- rds_master_secret_rotation_enabled = true or false
- rds_master_secret_rotation_automatically_after_days = N
- rds_sync_registry_database_url_on_rotation_apply = true

2. Apply per environment:
- terraform -chdir=iac init -reconfigure -backend-config=iac/environments/dev/backend.hcl
- terraform -chdir=iac apply -var-file=iac/environments/dev/terraform.tfvars

- terraform -chdir=iac init -reconfigure -backend-config=iac/environments/prod/backend.hcl
- terraform -chdir=iac apply -var-file=iac/environments/prod/terraform.tfvars

About always keeping RDS master secret and REGISTRY_DATABASE_URL in sync

Current state after this change:
1. Sync is enforced on Terraform apply when enabled.
2. Sync is enforced before ECS redeploy via deploy script.
3. This is strong operationally, but not mathematically continuous between applies/deploys.

For true continuous sync when rotation is enabled, the best next step is event-driven automation:
1. EventBridge rule on Secrets Manager rotation events for the RDS master secret.
2. Lambda target that runs the same refresh logic (update /kinnoo/<env>/REGISTRY_DATABASE_URL immediately after each rotation).
3. Keep the deploy-time check as a final safety net.

If you want, I can implement that EventBridge + Lambda path in Terraform next.
