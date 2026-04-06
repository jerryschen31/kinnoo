# Task 424 Smoke Tests

## Scope

- Validate feature105 AC7-AC9 implementation for EFS mount targets, desired ECS service count, and Terraform validation.

## Commands

```bash
python3 -m pytest tests --testmon -k test_feature105_group3
terraform -chdir=iac init -backend=false -input=false
terraform -chdir=iac validate
```

## Expected

- EFS file system and mount targets are defined for ECS usage.
- ECS service desired count defaults to 1.
- Terraform validation succeeds.
