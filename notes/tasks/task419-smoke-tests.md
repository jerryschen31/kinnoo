# Task 419 Smoke Tests

## Scope

- Validate feature104 AC1-AC4 checks for the S3 registry module.

## Command

```bash
python3 -m pytest tests/test_feature_104.py::test_feature104_group1 --testmon
```

## Expected

- The test passes and confirms:
  - AES-256 SSE is configured.
  - GOVERNANCE Object Lock is enabled.
  - Versioning is enabled.
  - Public access block is present.
