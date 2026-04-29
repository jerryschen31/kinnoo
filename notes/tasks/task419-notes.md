# Task 419 Notes

## Reimplementation Pass (Current)

- Re-validated module structure and acceptance criteria coverage for AC1-AC4.
- Added an S3 lifecycle rule to expire noncurrent versions after 30 days to align with feature-level storage hygiene requirements.
- Re-ran targeted regression for task419.

## Summary

Implemented S3 registry Terraform module for feature104 AC1-AC4:

- Added iac/modules/s3-registry/variables.tf with bucket and environment inputs.
- Added iac/modules/s3-registry/main.tf with:
  - S3 bucket resource with object_lock_enabled
  - AES-256 SSE default encryption
  - GOVERNANCE Object Lock default retention
  - Versioning enabled
  - Public access block settings
- Added feature104 tests scaffold in tests/test_feature_104.py and validated group1.

## Teaching Notes

- For Object Lock in AWS, bucket-level object_lock_enabled must be set at bucket creation.
- GOVERNANCE mode gives protective retention while still allowing privileged administrative bypass when needed.
- Explicit public-access-block resources are a defense-in-depth requirement even when bucket policies look private.
- Breaking acceptance tests into group1/group2/group3 allows incremental delivery by task while keeping final feature coverage coherent.

## Task-specific Regression

- Command: python3 -m pytest tests/test_feature_104.py::test_feature104_group1 --testmon
