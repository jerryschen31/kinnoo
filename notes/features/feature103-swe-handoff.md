# Feature 103 — SWE Handoff: Terraform Project Setup + VPC Networking

## Context
Create the complete `iac/` directory structure for Terraform. Bootstrap state storage. Create VPC with public subnets, security groups, and VPC endpoints for S3.

## Files to Create
```
iac/
├── versions.tf              # terraform { required_version, required_providers { aws, cloudflare } }
├── providers.tf             # provider "aws" { region = var.aws_region } + S3 backend config
├── variables.tf             # Root variables: aws_region, environment, project_name, etc.
├── outputs.tf               # Root outputs: vpc_id, subnet_ids, sg_ids, etc.
├── locals.tf                # Common locals: tags = { Project = "kinnoo", Environment = var.environment }
├── main.tf                  # Module instantiation (VPC, S3, IAM, etc.)
├── state/
│   ├── main.tf              # S3 bucket + DynamoDB table for state locking
│   └── variables.tf
├── modules/
│   └── vpc/
│       ├── main.tf          # VPC, subnets, route tables, internet gateway, VPC endpoints
│       ├── variables.tf     # vpc_cidr, subnet_cidrs, cloudflare_ips
│       ├── outputs.tf       # vpc_id, public_subnet_ids, security_group_ids
│       └── security_groups.tf  # ALB SG, ECS SG, VPC endpoint SG
└── environments/
    └── dev/
        └── terraform.tfvars
```

## VPC Design
- CIDR: 10.0.0.0/16
- Public subnet A: 10.0.1.0/24 (us-west-2a)
- Public subnet B: 10.0.2.0/24 (us-west-2b)
- Internet gateway for outbound access (public subnets)
- **No NAT Gateway**

## Security Groups
- **ALB SG**: Inbound 443 from Cloudflare IP ranges only. Outbound to ECS SG on 8000.
- **ECS SG**: Inbound 8000 from ALB SG only. Outbound all (for S3 via VPC endpoint, ECR, etc.)
- **VPC Endpoint SG**: Inbound 443 from VPC CIDR.

## VPC Endpoints
- S3 gateway endpoint (no cost)
- ECR API + ECR DKR interface endpoints (for ECS → ECR pulls without NAT)
- CloudWatch Logs interface endpoint

## State Bootstrap
- S3 bucket: `kinnoo-terraform-state-386775099533`
- DynamoDB table: `kinnoo-terraform-locks`
- Applied manually BEFORE other modules: `cd iac/state && terraform init && terraform apply`

## terraform.tfvars (dev)
```hcl
aws_region   = "us-west-2"
environment  = "dev"
project_name = "kinnoo"
vpc_cidr     = "10.0.0.0/16"
```

## Implementation Notes
- Use `data "aws_ip_ranges"` or hardcode Cloudflare IP ranges (they publish at https://www.cloudflare.com/ips/)
- Use `data "aws_caller_identity"` for account ID in naming
- All resources tagged with: `Project = "kinnoo"`, `Environment = var.environment`
- `terraform validate` must pass for all modules

## Testing
- `terraform validate` passes
- `terraform plan` shows expected resources
- (Manual): state bootstrap creates S3 bucket and DynamoDB table

## Dependencies
- None — this is the first IaC feature

## Acceptance Criteria Summary
1. iac/ directory structure created
2. State bootstrap module works
3. VPC with 2 public subnets
4. Security groups restricted properly
5. VPC endpoints for S3, ECR, CloudWatch
6. No NAT Gateway
