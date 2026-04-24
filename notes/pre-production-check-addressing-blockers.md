# Pre-Production Check: Addressing Blockers (Tasks 518-525)

This document provides implementation-ready guidance for SWE agents to resolve each blocker and make deployment production-ready.

## Global Implementation Rules

- Use Terraform variables and environment-specific tfvars files; do not hardcode `dev`/`prod` hostnames in shared modules.
- Prefer IaC changes over manual console changes.
- For every script that mutates cloud resources, support dry-run or explicit confirmation and fail fast on missing inputs.
- For every blocker fix, include at least one automated check (script output, terraform plan assertion, or pytest where applicable).

---

## task518: `iac/main.tf` and Cloudflare module hardcode dev domains

### Problem

- `module.alb.api_domain` is hardcoded to `"dev-api.kinnoo.ai"` in `iac/main.tf`.
- `iac/modules/cloudflare/main.tf` hardcodes `dev` and `dev-api` record names and output URLs.

### Implementation Plan

1. Add explicit domain variables in root Terraform.
- Update `iac/variables.tf` with:
  - `variable "base_domain"` (default `"kinnoo.ai"`)
  - `variable "frontend_subdomain"` (default `"dev"`)
  - `variable "api_subdomain"` (default `"dev-api"`)

2. Compute fully-qualified domains in root locals.
- Update `iac/locals.tf` with:
  - `frontend_fqdn = "${var.frontend_subdomain}.${var.base_domain}"`
  - `api_fqdn = "${var.api_subdomain}.${var.base_domain}"`

3. Pass dynamic domain to ALB module.
- Update `iac/main.tf`:
  - Replace `api_domain = "dev-api.kinnoo.ai"` with `api_domain = local.api_fqdn`

4. Refactor Cloudflare module to be environment-agnostic.
- Update `iac/modules/cloudflare/variables.tf`:
  - Replace dev-specific vars with neutral names:
    - `frontend_record_type`
    - `frontend_record_content`
    - `manage_frontend_record`
    - `frontend_subdomain`
    - `api_subdomain`
- Update `iac/modules/cloudflare/main.tf`:
  - Remove `locals { dev_host/dev_api_host }`
  - Use `var.frontend_subdomain` and `var.api_subdomain` for record names
  - Rename resources/outputs from `dev_*` to neutral equivalents

5. Update root module invocation.
- In `iac/main.tf`, map old values to new vars.
- Keep backwards compatibility briefly by wiring existing `dev_record_*` to new frontend names if needed in a transition commit, then remove old vars.

### Validation

- `terraform -chdir=iac validate`
- `terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars`
- `terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars`
- Verify plan shows prod domains for prod and dev domains for dev.

### Done Criteria

- No hardcoded `dev-api.kinnoo.ai` in `iac/main.tf`.
- Cloudflare module has no dev-specific host literals.

---

## task519: Ops scripts hardcoded to `kinnoo-dev-*`

### Problem

- `scripts/ops/rebuild_push_server_and_redeploy_ecs.sh` hardcodes ECS service/cluster names.
- `scripts/ops/check_cloudflare_dns_setup.sh` hardcodes `dev.kinnoo.ai` and `dev-api.kinnoo.ai`.

### Implementation Plan

1. Parameterize `rebuild_push_server_and_redeploy_ecs.sh`.
- Add optional args/env vars:
  - `ENVIRONMENT` (`dev` default)
  - `ECS_CLUSTER` override
  - `ECS_SERVICE` override
- Resolve cluster/service from Terraform outputs when not explicitly supplied:
  - `terraform output -raw ecs_cluster_arn` -> strip name
  - `terraform output -raw ecs_service_name`
- Remove hardcoded `kinnoo-dev-service` and `kinnoo-dev-cluster`.

2. Parameterize `check_cloudflare_dns_setup.sh`.
- Add required env vars:
  - `BASE_DOMAIN` (default `kinnoo.ai`)
  - `FRONTEND_SUBDOMAIN` (default `dev`)
  - `API_SUBDOMAIN` (default `dev-api`)
- Build expected FQDNs in script and validate those.
- Keep ACM CNAME check generic using API subdomain suffix.

3. Add usage/help blocks to both scripts.
- Print required env vars and examples for dev/prod usage.

### Validation

- Run script help/examples locally for dev and prod values.
- For DNS script, run against dev zone and prod zone with corresponding subdomains.

### Done Criteria

- No `kinnoo-dev-` hardcoded service/cluster names in script logic.
- DNS check script can verify any `<frontend_subdomain>.<base_domain>` and `<api_subdomain>.<base_domain>`.

---

## task520: production fallback CORS uses dev origins

### Problem

- In `server/config.py`, production fallback CORS defaults to dev domains.

### Implementation Plan

1. Remove dev-domain fallback from production defaults.
- In `ServerConfig.from_env` (`server/config.py`):
  - For `KINNOO_ENV=production`, require explicit `CORS_ORIGINS`.
  - If missing/empty, raise `ValueError("CORS_ORIGINS must be set in production")`.

2. Keep permissive fallback only for dev.
- Keep `("*",)` behavior only for `KINNOO_ENV=dev`.

3. Update docs and env templates.
- Document production requirement in deployment docs and sample env files.

### Validation

- Add/adjust tests in `server/tests/test_config.py`:
  - production + missing `CORS_ORIGINS` -> raises error
  - production + explicit origins -> accepted
  - dev + missing origins -> `*`

### Done Criteria

- Production mode cannot boot without explicit CORS origins.

---

## task521: hardcoded AWS profile `jerry`

### Problem

- `iac/providers.tf` and `iac/state/main.tf` hardcode AWS profile `jerry`.

### Implementation Plan

1. Remove hardcoded profile from providers.
- In both files:
  - replace `profile = "jerry"` with profile controlled by variable or env.

2. Preferred pattern:
- Add optional variable `aws_profile` (default empty string).
- In provider block, set `profile = var.aws_profile` only when non-empty.
  - If conditional assignment is awkward in current Terraform style, simplest safe approach is to omit `profile` entirely and rely on standard AWS credential chain (`AWS_PROFILE`, role creds, OIDC, etc.).

3. Update state bootstrap readme/runbook.
- Explicitly show:
  - local: `AWS_PROFILE=<name>`
  - CI: role/OIDC path with no profile.

### Validation

- `terraform -chdir=iac/state init`
- `terraform -chdir=iac/state plan`
- Confirm it works under a non-`jerry` profile and under role-based creds.

### Done Criteria

- No hardcoded profile names remain in Terraform provider files.

---

## task522: `web/wrangler.jsonc` hardcoded dev domains

### Problem

- `web/wrangler.jsonc` pins `BACKEND_URL` and route to dev endpoints.

### Implementation Plan

1. Split wrangler config by environment.
- Keep `web/wrangler.jsonc` as base shared config without hardcoded prod/dev route.
- Add env overlays using Wrangler environments:
  - `env.dev` with `routes` and `vars.BACKEND_URL` for dev
  - `env.prod` with prod values

2. Make deployment commands environment-specific.
- Example:
  - `wrangler deploy --env dev`
  - `wrangler deploy --env prod`

3. Update docs/scripts.
- Any deployment scripts should pass `--env` and not assume dev values.

### Validation

- `wrangler deploy --dry-run --env dev`
- `wrangler deploy --dry-run --env prod`

### Done Criteria

- No global hardcoded dev route/backend URL in base wrangler config.
- Dev/prod can deploy from same code with environment flag.

---

## task523: no documented/scripted bootstrap for first prod Lambda image

### Problem

- First production apply is blocked unless `lambda_security_check_image_uri` already exists.

### Implementation Plan

1. Extend existing script for env awareness.
- Update `scripts/ops/build_and_push_lambda_security_check_image.sh`:
  - Add `ENVIRONMENT` input (default `dev`)
  - Resolve ECR repo output for target env using `-var-file=environments/${ENVIRONMENT}/terraform.tfvars`
  - Emit exact tfvars line for that env.

2. Add explicit two-phase bootstrap runbook.
- Create doc section (or new doc) with exact sequence:
  1. Apply infra phase that creates ECR repo and IAM/Lambda role prerequisites.
  2. Build/push initial image with script.
  3. Set `lambda_security_check_image_uri` in env tfvars.
  4. Re-apply full stack.

3. Optional: add script flag to update tfvars automatically.
- `--write-tfvars <path>` that updates/inserts `lambda_security_check_image_uri` safely.

### Validation

- Run bootstrap sequence once in dev and once in prod dry-run flow.
- Confirm script prints valid image URI and apply picks it up.

### Done Criteria

- A new operator can bootstrap first Lambda image with only documented/scripted steps.

---

## task524: prod tfvars missing required values

### Problem

- `iac/environments/prod/terraform.tfvars` lacks required runtime values for complete apply.

### Implementation Plan

1. Add required keys explicitly in prod tfvars.
- `lambda_security_check_image_uri = "<prod ecr uri:tag>"`
- `auth_provider = "oidc_kinde"` (or chosen provider)
- Domain/DNS overrides for prod subdomains if introduced by task518:
  - `base_domain`
  - `frontend_subdomain`
  - `api_subdomain`
  - frontend record settings (`manage_frontend_record`, `frontend_record_type`, `frontend_record_content`)

2. Add prod tfvars.example template.
- Include placeholders and comments for required secrets/values.

3. Add preflight validation script/check.
- Script to assert required keys exist before `terraform apply`.

### Validation

- `terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars`
- Must not fail for missing required vars.

### Done Criteria

- Prod plan is unblocked by missing required tfvars values.

---

## task525: no safe script to pre-create `REGISTRY_DATABASE_URL` stub secret

### Problem

- First apply needs a secret ARN reference for DB URL wiring, but no safe bootstrap script exists.

### Implementation Plan

1. Add a dedicated bootstrap script.
- New script: `scripts/ops/bootstrap_registry_database_url_secret.sh`
- Inputs:
  - `AWS_REGION`
  - `ENVIRONMENT`
  - optional `PROJECT_NAME` (default `kinnoo`)
- Behavior:
  - Compute secret name: `${PROJECT_NAME}-${ENVIRONMENT}-REGISTRY_DATABASE_URL`
  - If secret missing: create with placeholder non-sensitive value, tag it, print ARN
  - If exists: no-op and print ARN

2. Ensure placeholder is clearly invalid but non-sensitive.
- Example: `postgresql+psycopg://replace:replace@replace/replace`

3. Integrate in runbook before first apply.
- Call this script in pre-apply checklist for environments using postgres metadata backend.

4. Add guardrail in ECS runtime docs.
- Replace placeholder with real connection string before enabling prod traffic.

### Validation

- Run script twice (idempotency check).
- Confirm Terraform uses secret ARN without apply-time failure.

### Done Criteria

- Secret bootstrap is scripted, idempotent, and documented.

---

## Suggested Execution Order

1. task521 (provider/profile hardcoding)
2. task518 (domain parameterization in IaC)
3. task524 (prod tfvars required values)
4. task523 (lambda image bootstrap path)
5. task525 (DB URL secret bootstrap)
6. task519 (ops scripts generalized)
7. task522 (wrangler env split)
8. task520 (strict production CORS requirement)

This order minimizes dependency deadlocks and gets Terraform planning/apply unblocked early.

---

## Required Verification Commands (Final Gate)

- `terraform -chdir=iac validate`
- `terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars`
- `terraform -chdir=iac plan -var-file=environments/prod/terraform.tfvars`
- `python3 -m pytest server/tests/test_config.py`
- Any updated ops-script smoke checks in `scripts/ops/` for both dev and prod parameters.

If all checks pass, blockers 518-525 can be considered production-ready for deployment execution.
