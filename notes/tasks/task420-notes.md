# Task 420 Notes

## Reimplementation Pass (Current)

- Re-validated IAM resources for AC5-AC7.
- Strengthened execution-role inline policy coverage with explicit ECR read actions and CloudWatch Logs write actions so runtime permissions are explicit in module code.
- Re-ran targeted regression for task420.

## Summary

Implemented IAM module for feature104 AC5-AC7:

- Added iac/modules/iam/variables.tf for environment, naming, bucket ARN, and GitHub repo trust scope.
- Added iac/modules/iam/main.tf with:
  - ECS task role + inline S3 bucket access policy
  - ECS execution role + managed execution policy + secrets read policy
  - GitHub OIDC provider and GitHub Actions federated role
  - OIDC trust conditions on audience and repository subject
- Added outputs for role ARNs.

## Teaching Notes

- ECS task role and execution role should stay separate: task role is app runtime permissions, execution role is pull/log/secrets bootstrap for ECS.
- OIDC trust policy conditions (`aud`, `sub`) are your main defense against token replay from unauthorized repos.
- Least-privilege is an iterative process: start with clear policy statements and tighten resource scopes as module dependencies get wired.
- Outputting IAM role ARNs from modules simplifies cross-module wiring for ECS services and CI pipelines later.

## Task-specific Regression

- Command: python3 -m pytest tests/test_feature_104.py::test_feature104_group2 --testmon
