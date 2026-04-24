# task524 implementation notes

- Filled in `iac/environments/prod/terraform.tfvars` so all required (no-default or `nullable=false`) variables in `iac/variables.tf` are present:
  - `zone_id`: placeholder string `REPLACE_WITH_KINNOO_AI_ZONE_ID` with an inline comment requiring the operator to paste the real Cloudflare zone id before first apply.
  - `lambda_security_check_image_uri`: placeholder URI `000000000000.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:bootstrap` chosen so it satisfies the strict regex declared in `iac/variables.tf` (12 zeros for the account id) but is obviously not a real account so any apply that tries to pull from ECR fails loudly.
  - `auth_provider="oidc_kinde"`, `registry_metadata_backend="postgres"` — explicit so prod does not silently inherit defaults that diverge from the deployment intent.
  - `base_domain="kinnoo.ai"`, `frontend_subdomain="www"`, `api_subdomain="api"`, `manage_frontend_record=false` — the env-isolated DNS contract introduced by task518.
- Inline comments in the prod tfvars walk operators through the bootstrap order (targeted ECR apply → image push → paste real URI → full apply) and the no-cross-contamination intent for the subdomain labels.
- Added `tests/iac/test_feature121_prod_tfvars_contract.py` (test747): parses `iac/variables.tf` for required variables (no `default = ...` or `nullable = false`), parses `iac/environments/prod/terraform.tfvars`, and asserts every required key is present, non-empty, and that `lambda_security_check_image_uri` matches the regex declared in variables.tf. Will fail any future drift where someone adds a required variable without filling in the prod tfvars.
