# Feature 105 — SWE Handoff: Terraform Compute Stack

## Context
Create Terraform modules for ECR, ALB, ACM, ECS/Fargate, and EFS.

## Files to Create
```
iac/modules/
├── ecr/
│   ├── main.tf          # ECR repository, lifecycle policy, scanning
│   ├── variables.tf
│   └── outputs.tf       # repository_url
├── alb/
│   ├── main.tf          # ALB, HTTPS listener, target group, ACM cert
│   ├── variables.tf     # vpc_id, subnet_ids, security_group_id, domain, zone_id
│   └── outputs.tf       # alb_dns_name, alb_arn, target_group_arn, acm_arn
└── ecs-fargate/
    ├── main.tf          # ECS cluster, task def, service, EFS mount
    ├── variables.tf     # image_url, cpu, memory, secrets_arns, efs_id, etc.
    └── outputs.tf       # cluster_arn, service_name
```

## ECR
- Repository: `kinnoo-server`
- Image scanning: enabled on push
- Lifecycle policy: keep last 10 images, expire untagged after 7 days
- Encryption: AES-256

## ALB
- Internal: false (internet-facing)
- Subnets: both public subnets
- Security group: ALB SG from feature103
- HTTPS listener (443): forward to target group
- HTTP listener (80): redirect to HTTPS
- Target group: port 8000, protocol HTTP, health check on /health
- ACM certificate: `dev-api.kinnoo.ai` with DNS validation
- ACM validation records: output for Cloudflare module (feature106)

## ECS/Fargate
- Cluster: `kinnoo-dev`
- Task definition:
  - CPU: 512 (0.5 vCPU)
  - Memory: 1024 (1 GB)
  - Container: kinnoo-server from ECR
  - Port: 8000
  - EFS mount: `/data` for persistent auth store
  - Secrets from Secrets Manager: JWT_SECRET, SESSION_SECRET, ADMIN_PASSWORD
  - Environment variables: KINNOO_ENV=production, S3_BUCKET, AWS_REGION, SNS_TOPIC_ARN
  - Log configuration: awslogs driver → CloudWatch log group
- Service:
  - Desired count: 1
  - Subnets: public subnets (with public IP for outbound internet)
  - Security group: ECS SG
  - Load balancer: ALB target group

## EFS
- File system in the VPC
- Mount targets in both subnets
- Encryption at rest
- Access point for the `/data` directory
- Security group: allow NFS (2049) from ECS SG

## Implementation Notes
- ACM certificate validation requires DNS records in Cloudflare — output the validation CNAME for feature106
- ECS tasks in public subnets need `assign_public_ip = true` (since no NAT Gateway)
- EFS mount in task def uses `efs_volume_configuration`
- Secrets injected as environment variables via `secrets` block in container definition
- Container definition uses `aws_ecs_task_definition` with `container_definitions` JSON

## Dependencies
- feature103 (VPC, subnets, security groups)
- feature104 (IAM roles, S3 bucket, Secrets Manager)

## Acceptance Criteria Summary
1. ECR repository with scanning and lifecycle
2. ALB with HTTPS, ACM cert, health check
3. ECS Fargate cluster + service (0.5 vCPU, 1GB, 1 task)
4. EFS with mount targets
5. `terraform validate` passes
