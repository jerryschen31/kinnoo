# Task 423 Notes

## Summary

Implemented feature105 AC5-AC6 by creating the ECS/Fargate runtime module and wiring compute dependencies at the root stack:

- Added ECS/Fargate module in iac/modules/ecs-fargate/ with:
  - ECS cluster resource.
  - ECS task definition configured for 0.5 vCPU (512) and 1 GB memory (1024).
  - Container definition with Secrets Manager secret injection for JWT_SECRET, SESSION_SECRET, and ADMIN_PASSWORD.
  - EFS volume mount wiring to `/data` in the task definition.
  - ECS service resource fronted by ALB target group.
- Updated iac/main.tf to instantiate and connect:
  - s3-registry, iam, secrets, ecr, alb, ecs-fargate, cloudflare modules.
- Updated root variables/outputs to support compute-stack module composition.
- Added/updated feature105 regression assertions for task423 slice (group2).

## Teaching Notes

- ECS task definition IAM split matters operationally: execution role handles image pull/log bootstrap, while task role scopes app runtime access.
- Wiring secret ARNs as a map then building deterministic container secret entries keeps Terraform concise and makes changes diff-friendly.
- Root module composition should expose actionable outputs (ALB DNS, target group, cluster/service IDs) so downstream modules and operators can integrate without hardcoded lookups.

## Task-specific Regression

- Command: python3 -m pytest tests --testmon -k test_feature105_group2
