# Task 424 Notes

## Summary

Implemented feature105 AC7-AC9 completion work for EFS and deployment validation:

- Completed EFS resources in ECS module:
  - Encrypted EFS file system.
  - Mount targets across all provided subnets (both dev public subnets).
  - EFS access point for `/data` mount path.
  - Dedicated EFS security group permitting NFS from ECS task security group.
- Finalized ECS service desired count behavior using `var.desired_count` with default `1`.
- Updated feature105 group3 regression checks to enforce desired-count default and EFS resources.
- Planned Terraform validation command as part of task acceptance.

## Teaching Notes

- Using `desired_count` as a variable with a safe default (`1`) balances beta simplicity with future scale-out flexibility, without requiring refactors.
- EFS mount targets must exist in each subnet where tasks run; otherwise, ECS tasks can fail to mount volumes in specific AZs.
- Infrastructure acceptance criteria should include both static structure checks (resource presence) and executable validation (`terraform validate`) to catch provider/schema drift early.

## Task-specific Regression

- Command: python3 -m pytest tests --testmon -k test_feature105_group3
- Command: terraform -chdir=iac init -backend=false -input=false && terraform -chdir=iac validate
