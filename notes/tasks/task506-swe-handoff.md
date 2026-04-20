# Task506 SWE Handoff - Terraform Postgres Foundation

## Objective
Implement Phase 13.1 IaC foundation for Postgres with secure private deployment and ECS runtime wiring.

## Deliverables
- Create `iac/modules/rds-postgres/{main.tf,variables.tf,outputs.tf}`.
- Wire module through `iac/main.tf`, `iac/variables.tf`, `iac/outputs.tf`.
- Update `iac/modules/vpc/*` to add the private subnets required for RDS placement, including any required private route tables and associations, and expose the resulting private subnet outputs.
- Update `iac/modules/secrets/*` and `iac/modules/ecs-fargate/*` for DB secret/env wiring.
- Update dev/prod tfvars contracts.

## Task Contracts
- RDS must be private-only, placed in VPC private subnets via a DB subnet group, and SG-scoped to ECS on 5432.
- Enforce encryption/TLS posture and prod protections (multi-AZ + deletion protection).
- ECS runtime must expose `REGISTRY_DATABASE_URL`, `REGISTRY_METADATA_BACKEND`, and DB pool env keys.

## Validation
- `terraform -chdir=iac fmt -check -recursive`
- `terraform -chdir=iac validate`
- `terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars`
- `terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars`
