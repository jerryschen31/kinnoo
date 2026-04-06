# Task 422 Notes

## Summary

Implemented feature105 AC1-AC4 by adding Terraform modules for compute entry resources:

- Added ECR module:
  - Repository with scan-on-push enabled.
  - AES-256 encryption configuration.
  - Lifecycle policy for retaining recent tagged images and expiring stale untagged images.
- Added ALB module:
  - Internet-facing ALB in public subnets.
  - HTTPS listener on 443 with ACM certificate for DNS validation.
  - HTTP listener redirect on port 80 to HTTPS.
  - ECS target group with `/health` endpoint checks.
  - Output of ACM DNS validation records for Cloudflare integration.
- Added feature105 regression tests in tests/test_feature_105.py (group1 for AC1-AC4).

## Teaching Notes

- ACM DNS validation is best modeled by outputting certificate validation records from the ALB module and publishing them in your DNS provider module. This keeps certificate issuance decoupled from DNS implementation details.
- ALB + target group health checks should validate application readiness (`/health`) rather than just TCP reachability, which catches app-level failures earlier.
- ECR lifecycle policy is a practical cost and hygiene control. Keeping recent tagged images while expiring old untagged layers prevents storage bloat in long-running CI pipelines.

## Task-specific Regression

- Command: python3 -m pytest tests --testmon -k test_feature105_group1
