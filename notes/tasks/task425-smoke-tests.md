# Task 425 Smoke Tests

## Scope

- Validate feature106 AC1-AC3 checks for base Cloudflare DNS records.

## Command

```bash
python3 -m pytest tests/test_feature_106.py::test_feature106_group1 --testmon
```

## Expected

- The test passes and confirms:
  - dev.kinnoo.ai CNAME record exists and targets Pages.
  - dev-api.kinnoo.ai CNAME record exists and targets ALB DNS.
  - API record is proxied.
