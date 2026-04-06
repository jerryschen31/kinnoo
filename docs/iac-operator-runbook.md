# IaC Operator Runbook

## Phase 12 Backend Standard (S3 Native Locking)

Use Terraform S3 backend with native state lockfiles (`use_lockfile = true`).
Do not use a DynamoDB lock table.

### Backend key naming convention

Use one key per root stack:

- format: `<env>/<stack>/terraform.tfstate`
- examples:
  - `dev/network/terraform.tfstate`
  - `dev/storage/terraform.tfstate`
  - `dev/compute/terraform.tfstate`
  - `dev/monitoring/terraform.tfstate`

This keeps state isolated per root stack and avoids collisions.

## WHERE to create `backend.tf`

Create `backend.tf` inside each Terraform root stack directory (the directory where you run `terraform init/plan/apply`).

- Create `backend.tf` in root stack directories, not in reusable child modules under `modules/`.
- Child modules should never define a backend.

If your root stacks are laid out as `iac/environments/dev/<stack>/`, then put each backend file at:

- `iac/environments/dev/network/backend.tf`
- `iac/environments/dev/storage/backend.tf`
- `iac/environments/dev/compute/backend.tf`
- `iac/environments/dev/monitoring/backend.tf`

## WHEN to create `backend.tf`

Create `backend.tf` before the first `terraform init` for each root stack.

Recommended order:

1. Ensure state bucket exists (`kinnoo-terraform-state-dev`) and has versioning/encryption.
2. Create `backend.tf` in the target root stack.
3. Run `terraform init` in that root stack.
4. Run `terraform plan` and `terraform apply`.

Bootstrap exception:

- If a stack is responsible for creating the state bucket itself, run that stack
  first with local state (no backend block) or run `terraform init -backend=false`.
- After the bucket exists, add `backend.tf` and run `terraform init -migrate-state`.

## Standard `backend.tf` template

```hcl
terraform {
  backend "s3" {
    bucket       = "kinnoo-terraform-state-dev"
    key          = "dev/<stack>/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }
}
```

Replace `<stack>` with the stack name, for example `storage`.

## Operator credentials (Jerry)

Use your AWS profile before running Terraform:

```bash
export AWS_PROFILE=jerry
export AWS_REGION=us-west-2
export AWS_SDK_LOAD_CONFIG=1
```

Optional check:

```bash
aws sts get-caller-identity
```

## SWE agent deployment handoff

To let SWE agent run IaC deployment steps in this workspace:

1. Open terminal in repo root.
2. Export `AWS_PROFILE=jerry` and region vars shown above.
3. `cd` into a root stack directory.
4. Confirm `backend.tf` exists in that directory with a unique key.
5. Run:

```bash
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Notes

- If a root stack was previously initialized with a different backend key, run:

```bash
terraform init -reconfigure
```

- If migrating existing state to a new key/back end, use:

```bash
terraform init -migrate-state
```
