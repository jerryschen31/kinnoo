# Dev Complete Teardown and Redeploy Instructions (Dev Only)

## Short answer
Yes, this can be safe for Prod, but only if you always initialize Terraform with the Dev backend config and use the Dev tfvars file.

In this repo, Dev and Prod are isolated by separate backend state locations:
- Dev backend: iac/environments/dev/backend.hcl
  - bucket = kinnoo-terraform-state-dev
  - key = dev/network/terraform.tfstate
- Prod backend: iac/environments/prod/backend.hcl
  - bucket = kinnoo-terraform-state-prod
  - key = prod/network/terraform.tfstate

Because destroy operates on the currently initialized state, using the Dev backend means destroy only targets Dev-managed resources.

## Exact commands: Destroy Dev only
Run these from repo root:

```bash
cd /Users/jerry/gh/kinnoo

# 1) Force Terraform to use DEV state backend (critical safety step)
terraform -chdir=iac init -reconfigure -backend-config=environments/dev/backend.hcl

# 2) Optional but strongly recommended: preview exactly what will be destroyed in DEV
terraform -chdir=iac plan -destroy -var-file=environments/dev/terraform.tfvars -out=dev-destroy.plan

# 3) Apply the reviewed DEV destroy plan
terraform -chdir=iac apply dev-destroy.plan
```

If you want one command instead of plan+apply:

```bash
cd /Users/jerry/gh/kinnoo
terraform -chdir=iac init -reconfigure -backend-config=environments/dev/backend.hcl
terraform -chdir=iac destroy -var-file=environments/dev/terraform.tfvars
```

## Prod safety guardrails
Use all of these to avoid touching Prod:

1. Always run init with exactly this file before destroy/apply:
   - iac/environments/dev/backend.hcl
2. Always pass exactly this var file:
   - iac/environments/dev/terraform.tfvars
3. Always run plan first for destructive actions and review resource names contain -dev-.
4. Never run init with iac/environments/prod/backend.hcl in the same sequence.
5. Do not use ad-hoc var overrides that set environment=prod.

## Is this sufficient for taking down Dev?
Yes, for Terraform-managed Dev infrastructure, this is sufficient. It will remove resources tracked in Dev Terraform state.

Notes:
- This should remove cost-heavy infra (ECS/ALB/RDS, etc.) that is managed by Dev state.
- Cloudflare Worker is likely unaffected if it is not managed by this Terraform stack.
- Some DNS records managed by this stack (for dev labels) may be deleted and recreated later.
- Terraform state bucket itself is the backend and is not destroyed by these commands.

## Bring Dev back up later (blank DB/S3 is fine)
Run from repo root:

```bash
cd /Users/jerry/gh/kinnoo

# 1) Re-point Terraform to DEV state backend
terraform -chdir=iac init -reconfigure -backend-config=environments/dev/backend.hcl

# 2) Recreate DEV infra
terraform -chdir=iac apply -var-file=environments/dev/terraform.tfvars
```

Optional preview first:

```bash
terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars -out=dev-create.plan
terraform -chdir=iac apply dev-create.plan
```

## Post-recreate reminders
1. Re-sync DB URL secret from the recreated RDS master secret before deploying app workloads:

```bash
scripts/ops/sync-database-url.sh dev --region us-west-2 --project kinnoo
```

2. Rebuild/redeploy the dev server container if needed:

```bash
scripts/ops/rebuild_push_server_and_redeploy_ecs.sh --env dev
```

3. Expect blank data stores if infra was fully destroyed and recreated.

## If destroy fails (known edge cases)

Important:
- A saved plan file is immutable. If Terraform code changes after a plan is created, you must generate a new plan file. Do not keep applying an older `*.plan`.

### 1) RDS error: cannot create snapshot because DB is not in available state

If you see:
- `InvalidDBInstanceState: Cannot create a snapshot ... not currently in the available state`

Then refresh/apply with the current Terraform config (dev now skips final snapshot):

```bash
cd /Users/jerry/gh/kinnoo
terraform -chdir=iac init -reconfigure -backend-config=environments/dev/backend.hcl
terraform -chdir=iac plan -destroy -var-file=environments/dev/terraform.tfvars -out=dev-destroy-remaining.plan
terraform -chdir=iac apply dev-destroy-remaining.plan
```

If the DB is still stuck and you need immediate cost stop, use AWS CLI (dev DB only), then reconcile Terraform:

```bash
aws rds delete-db-instance \
  --db-instance-identifier kinnoo-dev-postgres \
  --skip-final-snapshot \
  --delete-automated-backups \
  --region us-west-2

# Wait until it is fully deleted
aws rds wait db-instance-deleted \
  --db-instance-identifier kinnoo-dev-postgres \
  --region us-west-2

# Remove from terraform state if it still exists there
terraform -chdir=iac state rm 'module.rds_postgres[0].aws_db_instance.this'

# Continue destroy for remaining resources
terraform -chdir=iac plan -destroy -var-file=environments/dev/terraform.tfvars -out=dev-destroy-remaining.plan
terraform -chdir=iac apply dev-destroy-remaining.plan
```

### 2) S3 error: bucket not empty even though current objects look empty

This bucket uses versioning + Object Lock (governance). Old versions/delete markers can remain.

First verify there are residual versions/delete markers:

```bash
aws s3api list-object-versions --bucket kinnoo-registry-dev-386775099533 --output json
```

If entries exist, purge versions and delete markers (with governance bypass), then retry Terraform apply:

```bash
bucket="kinnoo-registry-dev-386775099533"

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

terraform -chdir=iac apply dev-destroy-remaining.plan
```
