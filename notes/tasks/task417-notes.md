# Task 417 Notes

## Summary

Implemented the initial Terraform project skeleton for feature103:

- Created root IaC files under iac/ (versions, providers, variables, locals, outputs, main).
- Added S3 backend configuration in iac/backend.tf with use_lockfile = true.
- Added state bootstrap module files in iac/state/ for state bucket management.
- Created initial VPC module scaffolding in iac/modules/vpc/ with VPC, public subnets, route table, and security groups.
- Added test coverage scaffold in tests/test_feature_103.py (group1 + group2 entrypoints required by TESTS.txt).

## Why this implementation

- AC1 needs the full root project shape now, so these files were created first.
- AC2 requires migration away from DynamoDB locking; backend uses native S3 lockfile mode.
- AC3 and AC4 require an initial VPC and security-group baseline, implemented in the first VPC module pass.
- Group2 checks are present but are intentionally finalized in task418 (endpoint and tfvars completion).

## Teaching Notes

- Terraform backend configuration is evaluated during terraform init, before planning resources. Keep backend config in the root stack, never in reusable modules.
- S3 native lockfile mode (use_lockfile = true) creates lock artifacts in S3 without requiring a DynamoDB lock table.
- Splitting Terraform into root module + reusable child modules keeps your architecture composable: root wires env-specific values; modules hold reusable resource logic.
- For incremental delivery, write tests for the final acceptance shape early (group1/group2), then implement task-by-task until all groups pass.

## Test Plan for Task 417

- Run only task-relevant regression target now:
  - python3 -m pytest tests --testmon tests/test_feature_103.py::test_feature103_group1
- Defer group2 execution to task418 because AC5-AC8 are completed there.
