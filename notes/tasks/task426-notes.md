# Task 426 Notes

## Reimplementation Pass (Current)

- Re-validated ACM DNS validation record handling and provider auth assumptions for AC4-AC6.
- Updated feature106 group2 test assertions to match Cloudflare provider v4 record resources.
- Re-ran targeted regression for task426.

## Summary

Implemented feature106 AC4-AC6 code paths:

- Added ACM validation DNS record resource in iac/modules/cloudflare/main.tf using for_each over acm_validation_records input.
- Updated provider guidance in iac/providers.tf so Cloudflare auth comes from CLOUDFLARE_API_TOKEN environment variable.
- Updated task426 status to needs-review.

## Teaching Notes

- Dynamic for_each over validation records is the cleanest way to handle ACM outputs because certificate validation can produce one or more CNAME records.
- For provider credentials, environment variables keep secrets out of Terraform files and source control.
- Proxied should remain false for ACM validation records; certificate validation needs direct DNS resolution.
- Keep module inputs strongly typed (list(object(...))) to catch wiring errors early.

## Task-specific Regression

- Command: python3 -m pytest tests/test_feature_106.py::test_feature106_group2 --testmon
