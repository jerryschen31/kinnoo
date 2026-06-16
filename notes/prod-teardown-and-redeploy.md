# Prod Complete Teardown and Redeploy Instructions (Prod Only)

## Snapshot backup taken

I already initiated a manual backup snapshot of the prod DB:

- DB instance: `kinnoo-prod-postgres`
- Snapshot ID: `kinnoo-prod-postgres-manual-20260615-180659`
- Region: `us-west-2`

At the time these instructions were written, snapshot status was `creating`.
Before teardown, wait for it to become `available`:

```bash
aws rds wait db-snapshot-completed \
  --region us-west-2 \
  --db-snapshot-identifier kinnoo-prod-postgres-manual-20260615-180659

aws rds describe-db-snapshots \
  --region us-west-2 \
  --db-snapshot-identifier kinnoo-prod-postgres-manual-20260615-180659 \
  --query 'DBSnapshots[0].{Status:Status,SnapshotId:DBSnapshotIdentifier,DB:DBInstanceIdentifier,SnapshotCreateTime:SnapshotCreateTime}' \
  --output json
```

## Short answer

Yes, this is safe for Prod if and only if you initialize Terraform with the Prod backend file and use the Prod tfvars file.

Prod backend in this repo:

- `iac/environments/prod/backend.hcl`
  - bucket = `kinnoo-terraform-state-prod`
  - key = `prod/network/terraform.tfstate`

Because destroy operates on the currently initialized state, using this backend limits actions to Prod-managed resources in that state.

## Exact commands: Gracefully destroy Prod

Run from repo root:

```bash
cd /Users/jerry/gh/kinnoo

# 1) Force Terraform to use PROD state backend (critical safety step)
terraform -chdir=iac init -reconfigure -backend-config=environments/prod/backend.hcl

# 2) Preview exactly what will be destroyed in PROD
terraform -chdir=iac plan -destroy -var-file=environments/prod/terraform.tfvars -out=prod-destroy.plan

# 3) Review plan output before applying
terraform -chdir=iac show prod-destroy.plan

# 4) Apply the reviewed PROD destroy plan
terraform -chdir=iac apply prod-destroy.plan
```

If you want one command instead of plan+apply:

```bash
cd /Users/jerry/gh/kinnoo
terraform -chdir=iac init -reconfigure -backend-config=environments/prod/backend.hcl
terraform -chdir=iac destroy -var-file=environments/prod/terraform.tfvars
```

## Prod safety guardrails

Use all of these to avoid mistakes:

1. Always run init with exactly: `iac/environments/prod/backend.hcl`
2. Always pass exactly: `iac/environments/prod/terraform.tfvars`
3. Always run `plan -destroy` first for destructive actions.
4. Never run this sequence after initializing with dev backend in the same shell history without re-running prod init.
5. Do not pass ad-hoc `-var` overrides that change environment/domain intent.

## Is this sufficient for taking down Prod?

Yes, for Terraform-managed Prod resources tracked in Prod state.

Notes:

- This should remove cost-heavy resources (ECS/ALB/RDS, etc.) managed by this state.
- Cloudflare records managed by this Terraform stack (for prod API/cert validation) can be removed.
- Frontend apex/www record may be unaffected if `manage_frontend_record = false` remains unchanged.
- Terraform state bucket itself is backend infrastructure and is not destroyed by this stack.

## Bring Prod back up later

Run from repo root:

```bash
cd /Users/jerry/gh/kinnoo

# 1) Re-point Terraform to PROD state backend
terraform -chdir=iac init -reconfigure -backend-config=environments/prod/backend.hcl

# 2) Recreate PROD infra
terraform -chdir=iac apply -var-file=environments/prod/terraform.tfvars
```

Optional preview first:

```bash
terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars -out=prod-create.plan
terraform -chdir=iac apply prod-create.plan
```

## Post-recreate reminders

1. Re-sync DB URL secret from recreated RDS master secret:

```bash
scripts/ops/sync-database-url.sh prod --region us-west-2 --project kinnoo
```

2. Rebuild/redeploy the prod server container:

```bash
scripts/ops/rebuild_push_server_and_redeploy_ecs.sh --env prod
```

3. Expect blank data stores unless you manually restore data from snapshot.

## Optional: restore data from the manual snapshot

Terraform recreate gives you a fresh DB. If you need old data, restore from snapshot after infra is recreated.

Minimal pattern:

```bash
# Example restore into a temporary instance first (recommended)
RESTORE_ID="kinnoo-prod-postgres-restore-$(date +%Y%m%d-%H%M%S)"
DB_SG_ID="$(terraform -chdir=iac output -raw db_security_group_id)"

aws rds restore-db-instance-from-db-snapshot \
  --region us-west-2 \
  --db-instance-identifier "$RESTORE_ID" \
  --db-snapshot-identifier kinnoo-prod-postgres-manual-20260615-180659 \
  --db-instance-class db.t4g.micro \
  --db-subnet-group-name kinnoo-prod-postgres-subnet-group \
  --vpc-security-group-ids "$DB_SG_ID" \
  --no-publicly-accessible
```

Then migrate data from the restored instance into the recreated primary prod DB.

## If destroy fails (known edge cases)

Important:

- Saved plan files are immutable. If Terraform code changes after plan creation, regenerate the plan.

### 1) RDS deletion protection / final snapshot edge cases

If you see deletion protection errors for `kinnoo-prod-postgres`:

```bash
aws rds modify-db-instance \
  --region us-west-2 \
  --db-instance-identifier kinnoo-prod-postgres \
  --no-deletion-protection \
  --apply-immediately

# Retry destroy plan/apply
terraform -chdir=iac plan -destroy -var-file=environments/prod/terraform.tfvars -out=prod-destroy-remaining.plan
terraform -chdir=iac apply prod-destroy-remaining.plan
```

If final snapshot name conflicts occur, keep your manual snapshot above as source of truth and use AWS CLI deletion only as last resort, then reconcile Terraform state.

### 2) S3 bucket not empty (versioning/object lock)

Prod registry bucket may retain object versions/delete markers.

Find prod bucket:

```bash
aws s3api list-buckets --query 'Buckets[].Name' --output text | tr '\t' '\n' | grep 'kinnoo-registry-prod-'
```

Purge versions/delete markers with governance bypass (replace bucket name):

```bash
bucket="kinnoo-registry-prod-<account-id>"

aws s3api list-object-versions --bucket "$bucket" --output json \
| jq -r '.Versions[]? | [.Key, .VersionId] | @tsv' \
| while IFS=$'\t' read -r key version; do
    aws s3api delete-object --bucket "$bucket" --key "$key" --version-id "$version" --bypass-governance-retention
  done

aws s3api list-object-versions --bucket "$bucket" --output json \
| jq -r '.DeleteMarkers[]? | [.Key, .VersionId] | @tsv' \
| while IFS=$'\t' read -r key version; do
    aws s3api delete-object --bucket "$bucket" --key "$key" --version-id "$version" --bypass-governance-retention
  done
```

Then retry Terraform apply for remaining destroy plan.

## Prod demo cost mode

To reduce the AWS bill while keeping prod functional for demos, two toggles were added to `iac/environments/prod/terraform.tfvars` on 2026-06-15:

```hcl
rds_multi_az   = false   # Switch DB from Multi-AZ (~$22/mo savings) to Single-AZ
alb_enable_waf = false   # Disable WAF ACL and its ALB association (~$5/mo savings)
```

Both are controlled by root-level Terraform variables (`rds_multi_az`, `alb_enable_waf`) wired through to the `rds-postgres` and `alb` modules respectively.

To re-enable full production hardening before a high-stakes demo or production promotion, flip both to `true` and apply:

```bash
# In iac/environments/prod/terraform.tfvars:
rds_multi_az   = true
alb_enable_waf = true
```

```bash
terraform -chdir=iac init -reconfigure -backend-config=environments/prod/backend.hcl
terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars -out=prod-hardened.plan
terraform -chdir=iac apply prod-hardened.plan
```

Note: switching RDS Multi-AZ back to `true` causes a brief DB modification window (similar to a managed failover). Plan the apply outside of active demo time.
