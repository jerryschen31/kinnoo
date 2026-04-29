# Task487 notes - init/run help hotfix + task482 diagnostics (2026-04-11)

## What changed
- Removed legacy `kinnoo init --framework` option from CLI parser/help.
- Kept positional `kinnoo init [framework] [agent_name]` as the only framework selection path.
- Updated init help to present framework catalog under positional argument details.
- Removed `--thinking {low,medium,high}` from `kinnoo run` help/CLI parsing.
- Added orange icon prefix (`🍊`) to subcommand help descriptions.
- Added retry/fallback policy in lambda async invocation helper used by publish flow.

## Task482 diagnosis summary
- Task482 Terraform changes were validated/planned previously but intentionally not applied in the SWE run.
- Without `terraform apply`, lambda resources are not created in AWS and no lambda execution is visible in console.
- After apply, ECS service must be redeployed with updated image/env vars for publish route to invoke lambda.
- Existing security icons are sourced from inline publish-time checks; absent icons typically indicate publishing against an older deployment path.

## Files updated
- src/kinnoo/cli.py
- tests/test_cli.py
- server/services/security_check.py
- server/tests/test_security_check.py
- TASKS.txt
- TESTS.txt
- FEATURES.txt
- notes/features/feature115-swe-handoff.md
- notes/tasks/task482-notes.md

## Test run
- `python3 -m pytest tests/test_cli.py --testmon -k "init_help_deprecates_framework_flag_and_uses_language_metavar or run_help_removes_thinking_option_and_has_orange_title or framework_flag_rejected_for_init or feature81_run_mapping_and_exit_propagation"`
- `python3 -m pytest server/tests/test_security_check.py --testmon -k "containerized_security_check_lambda_retry_fallback"`
- `python3 scripts/validate_project_manifests.py`

## Teaching notes
- Deprecation completion is strongest when parser support is removed, help output is updated, and explicit rejection tests lock behavior.
- For distributed systems, async-offload paths (Lambda) should expose retry semantics and explicit fallback metadata so operators can distinguish deployment/config issues from business-logic failures.

## Additional fixes completed after initial task487
- Verified `Dockerfile.lambda` and `lambda_handler.py` and used them to bootstrap a deployable Lambda image.
- Added dedicated Terraform-managed ECR repository and lifecycle policy for Lambda security-check images.
- Added Terraform outputs exposing Lambda ECR repository URL/name/ARN.
- Hardened Terraform variable contract for `lambda_security_check_image_uri`:
	- removed unsafe default pointing at a public base image
	- added validation to require private account ECR URI + tag
- Added automation script `scripts/ops/build_and_push_lambda_security_check_image.sh` to build and push Lambda image with Lambda-compatible build settings.
- Created/pushed image tags (`v1`, then `v2`) and updated `iac/environments/dev/terraform.tfvars` to use `v2`.
- Diagnosed and fixed ECR lifecycle policy validation error (`tagStatus=tagged` requires a tag filter).
- Validated Lambda creation with targeted Terraform apply after pushing Lambda-compatible image.

## Additional Lambda pipeline completion (S3 trigger + result writeback)
- Added Terraform event wiring so S3 uploads of tenant-scoped `.kno` objects now invoke Lambda automatically.
- Added Lambda invoke permission allowing the registry bucket to call the function.
- Replaced stub Lambda handler with real checks that:
	- parse tenant/agent/version metadata from the S3 object path,
	- load the archive and checksum sidecar,
	- run signature/archive/per-file/checksum checks,
	- write a structured security report object back to S3,
	- update the existing per-version metadata document used by server/UI (`security_status`, `security_report`).
- Added focused tests for Lambda handler behavior covering archive processing and non-archive skip behavior.

### Files changed for this follow-up
- `iac/main.tf`
- `iac/modules/lambda-security-check/main.tf`
- `iac/modules/lambda-security-check/variables.tf`
- `Dockerfile.lambda`
- `lambda_handler.py`
- `tests/test_lambda_handler.py`
- `TASKS.txt`
- `TESTS.txt`

## Verbatim response (requested)
Completed. I checked your files, created the Terraform-managed Lambda ECR repo, enforced safer Terraform validation, wrote the build/push automation script, and successfully created the Lambda with a valid image.

What I verified
1. Your [Dockerfile.lambda](Dockerfile.lambda) is valid for a minimal Lambda container bootstrap.
2. Your [lambda_handler.py](lambda_handler.py) is valid Python and works for smoke testing.

Answer to your ECR question
1. Yes, you should use a separate ECR repo for the Lambda image.
2. That is now implemented and created as:
[lambda_security_check_ecr_repository_url output](iac/outputs.tf)

Terraform hardening done
1. Added dedicated Lambda ECR repo resources and lifecycle policy in:
[iac/modules/ecr/main.tf](iac/modules/ecr/main.tf)
2. Added module outputs for Lambda repo name/url/arn in:
[iac/modules/ecr/outputs.tf](iac/modules/ecr/outputs.tf)
3. Exposed root output for Lambda ECR URL in:
[iac/outputs.tf](iac/outputs.tf)
4. Removed unsafe default and enforced explicit private ECR image URI with validation in:
[iac/variables.tf](iac/variables.tf)
5. Set dev environment variable to the pushed image URI in:
[iac/environments/dev/terraform.tfvars](iac/environments/dev/terraform.tfvars)

Script automation done
1. Added executable script:
[scripts/ops/build_and_push_lambda_security_check_image.sh](scripts/ops/build_and_push_lambda_security_check_image.sh)
2. Script behavior:
- Reads Lambda ECR repo URL from Terraform outputs
- Logs into ECR
- Builds Lambda-compatible image with buildx for linux/amd64
- Disables provenance/sbom attestation to avoid Lambda media-type rejection
- Pushes image and prints the tfvars line to use

What I ran for you
1. Terraform targeted apply created Lambda ECR repo and lifecycle policy successfully.
2. Script built and pushed image tag v2:
386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:v2
3. Updated dev tfvars to use v2.
4. Terraform targeted apply for Lambda module succeeded; Lambda function creation is now successful:
kinnoo-dev-security-check

Important note from the run
1. The first pushed image tag v1 failed Lambda CreateFunction due to unsupported manifest media type.
2. Switching to buildx with linux/amd64 and provenance/sbom disabled fixed it (v2).

Natural next steps
1. Run a full Terraform plan/apply (without target) to reconcile full stack:
terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars -var "zone_id=YOUR_ZONE_ID"
terraform -chdir=iac apply -var-file=environments/dev/terraform.tfvars -var "zone_id=YOUR_ZONE_ID"
2. Redeploy ECS server so publish flow uses the latest server code path.
3. Publish a test agent and check CloudWatch logs for kinnoo-dev-security-check invocation.
