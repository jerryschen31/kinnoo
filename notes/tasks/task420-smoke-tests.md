# Task 420 Smoke Tests

## Scope

- Validate feature104 AC5-AC7 checks for IAM roles and OIDC trust wiring.

## Command

```bash
python3 -m pytest tests/test_feature_104.py::test_feature104_group2 --testmon
```

## Expected

- The test passes and confirms:
  - ECS task role exists.
  - ECS execution role exists.
  - GitHub OIDC provider exists.
