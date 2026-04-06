# Task 425 Notes

## Reimplementation Pass (Current)

- Re-validated Cloudflare DNS resources for AC1-AC3.
- Updated feature106 group1 test assertions to match Cloudflare provider v4 resource schema (`cloudflare_record` + `value`).
- Re-ran targeted regression for task425.

## Summary

Implemented feature106 AC1-AC3 baseline in the Cloudflare module:

- Added iac/modules/cloudflare/variables.tf with zone/domain/pages/alb inputs.
- Added iac/modules/cloudflare/main.tf with DNS records for:
  - dev.kinnoo.ai -> Cloudflare Pages target
  - dev-api.kinnoo.ai -> ALB DNS name (proxied)
- Added tests/test_feature_106.py and validated group1 coverage for AC1-AC3.

## Teaching Notes

- DNS modules should expose clear input contracts (`zone_id`, `alb_dns_name`) rather than burying account-specific values in code.
- Using separate resources for frontend and API records keeps rollout and troubleshooting simple.
- Proxied CNAME on API hostname is key for Cloudflare edge protections before traffic reaches ALB.
- Keeping test groups aligned with task slices helps ship infrastructure changes incrementally while preserving acceptance-criteria traceability.

## Task-specific Regression

- Command: python3 -m pytest tests/test_feature_106.py::test_feature106_group1 --testmon
