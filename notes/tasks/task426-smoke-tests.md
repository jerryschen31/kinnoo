# Task 426 Smoke Tests

## Scope

- Validate feature106 AC4-AC6 checks for ACM validation records and Cloudflare auth conventions.

## Commands

```bash
python3 -m pytest tests/test_feature_106.py::test_feature106_group2 --testmon
terraform -chdir=iac init -backend=false -input=false
terraform -chdir=iac validate
```

## Expected

- The test passes and confirms ACM validation record logic exists and provider token is env sourced.
- Terraform validation succeeds.
