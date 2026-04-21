# task506 implementation notes

- Added `iac/modules/rds-postgres` with private-only RDS configuration and alarm resources.
- Added VPC private subnets, DB security group, and ECS/Secrets DB environment wiring.
- Updated dev/prod tfvars with private subnets and DB pool/backend runtime contracts.
