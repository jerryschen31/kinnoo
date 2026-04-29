# Task 423 Smoke Tests

## Scope

- Validate feature105 AC5-AC6 implementation for ECS/Fargate cluster, task definition, and service.

## Commands

```bash
python3 -m pytest tests --testmon -k test_feature105_group2
```

## Expected

- ECS cluster/task definition/service resources exist.
- Task definition is configured for 512 CPU and 1024 memory.
- Task definition includes EFS mount configuration and secrets injection.
