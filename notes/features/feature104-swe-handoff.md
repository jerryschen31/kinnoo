# Feature 104 — SWE Handoff: Terraform Storage & Security

## Context
Create Terraform modules for S3 registry bucket, IAM roles, and Secrets Manager.

## Files to Create
```
iac/modules/
├── s3-registry/
│   ├── main.tf          # S3 bucket, encryption, Object Lock, versioning, lifecycle
│   ├── variables.tf     # bucket_name, environment
│   └── outputs.tf       # bucket_arn, bucket_name
├── iam/
│   ├── main.tf          # ECS task role, ECS execution role, GitHub OIDC role
│   ├── variables.tf     # s3_bucket_arn, ecr_arn, secrets_arns, github_repo
│   ├── outputs.tf       # role ARNs
│   └── policies.tf      # IAM policy documents
└── secrets/
    ├── main.tf          # Secrets Manager secrets
    ├── variables.tf     # secret names and values
    └── outputs.tf       # secret ARNs
```

## S3 Registry Bucket
- Naming: `kinnoo-registry-dev-386775099533`
- Encryption: AES-256 (SSE-S3) — set as default encryption
- Object Lock: GOVERNANCE mode (allows admin delete with additional permissions)
- Versioning: enabled
- Public access: fully blocked (all four settings)
- Lifecycle: consider 90-day transition to IA for old versions

## IAM Roles
1. **ECS Task Role** — Attached to running container:
   - S3 read/write to registry bucket (s3:GetObject, s3:PutObject, s3:ListBucket, s3:DeleteObject)
   - SNS publish (for password reset alerts)
2. **ECS Execution Role** — Used by ECS to start tasks:
   - ECR pull (ecr:GetDownloadUrlForLayer, ecr:BatchGetImage, ecr:GetAuthorizationToken)
   - CloudWatch Logs (logs:CreateLogStream, logs:PutLogEvents)
   - Secrets Manager read (secretsmanager:GetSecretValue) for JWT/session secrets
3. **GitHub Actions OIDC Role** — For CI/CD:
   - OIDC provider for `token.actions.githubusercontent.com`
   - Trust policy: repo = `kinnoo/kinnoo`, branch = `main`
   - Permissions: ECR push, ECS update-service, S3 for Terraform state, Terraform plan/apply

## Secrets Manager
- `kinnoo/dev/jwt-secret` — JWT signing key
- `kinnoo/dev/session-secret` — Session signing key
- `kinnoo/dev/admin-password` — Bootstrap admin password
- Values set via AWS Console or CLI (not in Terraform)

## Implementation Notes
- Use `aws_s3_bucket_object_lock_configuration` (separate resource from bucket)
- OIDC provider: `aws_iam_openid_connect_provider` for GitHub Actions
- Secrets: create the secret resource in Terraform, set value manually (don't store in tfvars)
- Object Lock GOVERNANCE mode allows deletion with `s3:BypassGovernanceRetention`
- IAM policies should use least-privilege principle

## Dependencies
- feature103 (VPC module for reference, terraform structure)

## Acceptance Criteria Summary
1. S3 bucket with AES-256, Object Lock GOVERNANCE, versioning, public access blocked
2. IAM roles for ECS task, ECS execution, GitHub OIDC
3. Secrets Manager secrets created (values set manually)
4. `terraform validate` passes
