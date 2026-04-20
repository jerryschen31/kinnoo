# Task496 SWE Handoff - Dual-App Auth IaC Alignment and Manual Validation Split

## Objective
Implement task496 step5 as IaC work owned by SWE, while preserving task496 step6 as human-run post-deploy validation.

This handoff covers exact Terraform implementation pointers for:
1. Secrets Manager resources/references for dual-app auth runtime config.
2. ECS task-definition env/secret injection alignment.
3. Dev environment tfvars contract updates.
4. Cloudflare runtime variable strategy (IaC where supported; explicit manual fallback otherwise).

## Scope Boundaries
- In scope (SWE/IaC): Terraform updates under iac/ and automated checks for new test717 and test718.
- Out of scope (human/manual): e2e login/logout/callback smoke and deployed runtime behavior checks in test719.

## Current IaC State (Important)
- `iac/modules/secrets/main.tf` only defines `JWT_SECRET`, `SESSION_SECRET`, `ADMIN_PASSWORD`.
- `iac/modules/ecs-fargate/main.tf` only injects those legacy keys via `ordered_secret_keys`.
- `iac/modules/ecs-fargate/main.tf` currently has lifecycle `ignore_changes = [container_definitions, volume]` on `aws_ecs_task_definition.app`; this can prevent Step5 auth wiring from applying.
- `iac/modules/cloudflare/main.tf` currently manages DNS records only (no runtime Worker/Pages vars).

## File-by-File Implementation Pointers

### 1) iac/modules/secrets/main.tf
Required changes:
1. Expand `local.secret_names` with dual-app auth keys:
   - `KINDE_ISSUER_URL`
   - `KINDE_WEB_CLIENT_ID`
   - `KINDE_WEB_CLIENT_SECRET`
   - `KINDE_CLI_CLIENT_ID`
   - `KINDE_AUDIENCE`
   - optionally endpoint keys used by runtime (`JWKS_ENDPOINT_URL`, `AUTHORIZATION_ENDPOINT`, `TOKEN_ENDPOINT`, `LOGOUT_ENDPOINT`, `USERINFO_ENDPOINT`, `REVOCATION_ENDPOINT`) if runtime contract requires explicit env wiring.
2. Add corresponding `aws_secretsmanager_secret` resources.
3. Extend `output "secret_arns"` and `output "secret_names"` with the new keys.
4. Preserve existing legacy secrets for backward compatibility unless explicitly removed in a separate task.

Implementation notes:
- This module currently creates secret containers only (not secret versions). Keep that pattern unless root design requires value management.
- Do not commit plaintext values to repo.

### 2) iac/modules/ecs-fargate/main.tf
Required changes:
1. Expand `ordered_secret_keys` to include the new dual-app auth keys from secrets module outputs.
2. Ensure `local.container_secrets` maps each key to `valueFrom = var.secret_arns[key]`.
3. Add explicit non-secret environment variables only where appropriate (for example `AUTH_PROVIDER` if non-sensitive).
4. Review task-definition lifecycle ignore behavior:
   - Current `ignore_changes = [container_definitions, volume]` can block deployment of secret/env updates.
   - For this task, ensure auth-related container definition updates are actually applied by Terraform (remove/narrow ignore as needed).
5. Keep existing runtime env keys unrelated to auth intact.

Implementation notes:
- This file is the source of truth for ECS runtime env/secret wiring that test717 validates.
- Keep container env names aligned with task496/task501 contract.

### 3) iac/modules/ecs-fargate/variables.tf
Required changes:
1. No schema change is required if `secret_arns` map remains the single input.
2. If adding any new plain env map input (optional), define typed variable and docs here.

### 4) iac/main.tf
Required changes:
1. Keep module linkage from `module.secrets.secret_arns` to `module.ecs_fargate.secret_arns`.
2. If new cloudflare runtime var module inputs are added, thread them through here.

### 5) iac/variables.tf
Required changes:
1. Add only non-sensitive root variables needed for cloudflare runtime var control (if implementing runtime vars in Terraform).
2. Do not add sensitive auth secret values here.

### 6) iac/environments/dev/terraform.tfvars
Required changes:
1. Add required non-secret dev inputs for any new IaC toggles/vars introduced in step5.
2. Keep secret values out of tfvars.
3. If Cloudflare runtime vars cannot be Terraform-managed in current model, include only control flags and keep manual values documented in notes.

### 7) iac/modules/cloudflare/main.tf and iac/modules/cloudflare/variables.tf
Required changes:
1. Evaluate whether current provider/resources in this repo can manage the runtime vars needed by frontend/proxy path.
2. If supported in current model:
   - add runtime var resources and typed variables.
   - wire values from root module.
3. If not supported in current model:
   - leave DNS resources as-is.
   - explicitly document manual Cloudflare runtime var update steps in `notes/kinde-auth-setup-dev.md` section 5.3.

Implementation notes:
- Do not block task completion on unsupported Cloudflare resource types; document fallback clearly.

### 8) tests/iac/test_auth_iac_alignment.py (new)
Create this file and implement both automated tests referenced in manifest:
1. `test_task496_dual_app_secret_wiring` (test717)
2. `test_task496_dev_tfvars_and_cloudflare_runtime_contract` (test718)

Recommended assertions:
- Parse Terraform files as text/AST-level checks (fast, deterministic CI).
- Verify required auth keys are present in secrets outputs and ECS secret wiring lists.
- Verify `terraform.tfvars` contains required non-secret contract keys for any added inputs.
- Verify Cloudflare strategy is either IaC-managed (resources exist) or manual-fallback documentation is present and current in `notes/kinde-auth-setup-dev.md`.

## Suggested Execution Order
1. Update `iac/modules/secrets/main.tf` outputs and resources.
2. Update `iac/modules/ecs-fargate/main.tf` injection and lifecycle behavior so auth changes apply.
3. Add any root/module variable threading (`iac/main.tf`, `iac/variables.tf`, `iac/modules/cloudflare/variables.tf`).
4. Update `iac/environments/dev/terraform.tfvars` for non-secret inputs.
5. Implement `tests/iac/test_auth_iac_alignment.py` for test717/test718.
6. Update `notes/kinde-auth-setup-dev.md` only if Cloudflare runtime vars remain manual in current IaC model.

## Acceptance Checklist Mapped to Tests

### test717 - task496 dual-app secret wiring
- [ ] Secrets module defines/authors dual-app auth secret containers.
- [ ] Secrets outputs expose required keys through `secret_arns`.
- [ ] ECS task-definition secret injection includes required dual-app auth env names.
- [ ] Terraform plan/validate path confirms no plaintext secret values in repo-managed files.

### test718 - dev tfvars and cloudflare runtime contract
- [ ] Dev tfvars include required non-secret control inputs introduced by step5.
- [ ] Cloudflare runtime var handling is implemented in Terraform where supported.
- [ ] If unsupported, manual fallback is documented with exact variable names/steps in `notes/kinde-auth-setup-dev.md`.

### test719 - human post-deploy smoke and runtime validation (manual)
- [ ] Web login/logout/callback smoke passes on deployed dev URLs.
- [ ] CLI loopback callback login smoke passes.
- [ ] Deployed runtime validates issuer/audience/signature behavior end-to-end.
- [ ] Evidence is recorded in `notes/kinde-auth-setup-dev.md` section 5.3.3.

## Commands SWE Should Run
1. `terraform -chdir=iac fmt -recursive`
2. `terraform -chdir=iac validate`
3. `terraform -chdir=iac plan -var-file=environments/dev/terraform.tfvars`
4. `python3 scripts/validate_project_manifests.py`
5. `python3 -m pytest tests/iac -q`

## Risks and Guardrails
- Risk: ECS task-definition `ignore_changes` masks real IaC auth wiring updates.
  - Guardrail: ensure auth-related container definition changes are not ignored for this rollout.
- Risk: plaintext secret leakage via tfvars or committed examples.
  - Guardrail: secrets are represented as Secret Manager references only.
- Risk: Cloudflare runtime vars not manageable in current provider/model.
  - Guardrail: explicit manual fallback with checklist and documented variable names.

## Done Definition for SWE Portion of Task496
- IaC changes merged and validated for dual-app auth secret + ECS wiring.
- Automated coverage for test717 and test718 implemented and passing.
- Manual validation instructions for test719 are complete and handoff-ready for human execution.
