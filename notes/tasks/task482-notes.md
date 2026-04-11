# Task482 notes - containerized Lambda security checks via Terraform (2026-04-10)

## What changed
- Added async Lambda dispatch path from publish flow:
  - `invoke_security_check_lambda_async(...)`
  - dispatches when `KINNOO_SECURITY_CHECK_EXECUTION_MODE=lambda`
  - uses `InvocationType=Event` for async invoke
  - safe local fallback when lambda mode is disabled/unavailable
- Added integration test that mocks boto3 Lambda invocation and verifies async dispatch path.
- Added explicit retry/fallback behavior for lambda async invoke path:
  - default retries: `KINNOO_SECURITY_CHECK_LAMBDA_RETRIES=2` (3 total attempts)
  - on repeated failure, invocation result reports fallback marker while inline publish checks remain authoritative

## Terraform changes
- Added new module: `iac/modules/lambda-security-check`
  - creates Lambda function (container image) with 60s timeout
  - creates CloudWatch log group
- Updated IAM module:
  - new lambda execution role and policy
  - ECS task role permission to invoke Lambda
  - output for lambda role ARN
- Wired root stack:
  - new `module.lambda_security_check`
  - ECS env var injection for lambda mode and function name
  - new outputs for lambda name/arn
- Added root variable and dev tfvars value:
  - `lambda_security_check_image_uri`

## Validation and plan evidence
- `terraform -chdir=iac init -backend=false -input=false` (success)
- `terraform -chdir=iac validate` (success)
- `terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars -var 'zone_id=dummy-zone' -refresh=false` (success)
  - Plan summary: `7 to add, 0 to change, 2 to destroy`
  - New planned resources include:
    - `module.lambda_security_check.aws_lambda_function.security_check`
    - `module.lambda_security_check.aws_cloudwatch_log_group.security_check`
    - IAM role/policies for lambda execution and ECS invoke permissions

## Apply note
- Terraform apply was intentionally not executed in this SWE run because it would perform real cloud changes requiring environment-specific operator authorization.

## Operator diagnosis note
- If you do not see the Lambda function in AWS console after publish, the most likely cause is that Terraform changes were only planned/validated and not applied yet.
- Even after Terraform apply, Lambda async dispatch will not run from publish until the server ECS task is redeployed with updated environment variables and image containing task482+ code.
- Security icons in the UI are driven by publish-time inline checks persisted in metadata; if icons are absent, verify you are hitting the updated server deployment and publishing through that deployment (not an older stack).

## Test run
- `python3 -m pytest server/tests/test_security_check.py --testmon -k "containerized_security_check or publish_triggers_security_update or post_publish_security_checks"`
  - Result: passed
