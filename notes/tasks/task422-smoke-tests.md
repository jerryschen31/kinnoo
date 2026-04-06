# Task 422 Smoke Tests

## Scope

- Validate feature105 AC1-AC4 implementation and module shape.

## Commands

```bash
python3 -m pytest tests --testmon -k test_feature105_group1
```

## Expected

- ECR repository, image scanning, and lifecycle policy resources exist.
- ALB HTTPS listener and ACM DNS-validation certificate resources exist.
- Target group health check path is `/health`.
