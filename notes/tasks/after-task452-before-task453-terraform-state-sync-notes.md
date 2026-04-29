# Terraform state-sync notes (after task452, before task453)

Date: 2026-04-10
Scope: Terraform code changes in `iac/` made to align plan/apply behavior with current deployed infrastructure and avoid unintended drift corrections.

## Why these changes were made

During drift reconciliation, Terraform was attempting to manage values that are currently controlled out-of-band in live infra (notably ECS runtime/task-definition details and the `dev.kinnoo.ai` DNS shape in Cloudflare). The objective was to:

- keep apply safe (no accidental infra mutation),
- make default plan behavior match the currently deployed environment,
- keep future management explicit via Terraform variables.

## Terraform code changes made

### 1) Root-level Cloudflare dev record controls

File: `iac/variables.tf`

Added:

- `dev_record_type` (string, default `"CNAME"`)
- `dev_record_content` (string, default `"kinnoo.pages.dev"`)
- `manage_dev_record` (bool, default `false`)

Reason:

- decouple DNS behavior from hardcoded Pages assumptions,
- allow Worker-compatible DNS inputs,
- set safe default so a plain `terraform apply` does not create `dev_pages` unexpectedly.

### 2) Wire new Cloudflare inputs from root module call

File: `iac/main.tf`

Changed Cloudflare module inputs from a hardcoded `pages_target` to:

- `dev_record_type = var.dev_record_type`
- `dev_record_content = var.dev_record_content`
- `manage_dev_record = var.manage_dev_record`

Reason:

- centralize behavior under explicit root vars,
- support env-specific overrides cleanly.

### 3) Cloudflare module variable model update

File: `iac/modules/cloudflare/variables.tf`

Replaced old `pages_target` variable with:

- `dev_record_type` (default `"CNAME"`)
- `dev_record_content` (default `"kinnoo.pages.dev"`)
- `manage_dev_record` (default `false`)

Reason:

- make the module flexible for multiple dev DNS backends,
- default to non-management for safer no-var-file runs.

### 4) Cloudflare dev record made conditional and configurable

File: `iac/modules/cloudflare/main.tf`

Updated `cloudflare_record.dev_pages`:

- added `count = var.manage_dev_record ? 1 : 0`
- changed `type` from fixed `"CNAME"` to `var.dev_record_type`
- changed `content` from `var.pages_target` to `var.dev_record_content`

Reason:

- prevent forced creation/management when dev DNS is intentionally not Terraform-managed,
- allow Worker-style DNS configuration when desired.

### 5) Dev environment tfvars aligned to current dev DNS reality

File: `iac/environments/dev/terraform.tfvars`

Added:

- `dev_record_type = "AAAA"`
- `dev_record_content = "100::"`
- `manage_dev_record = false`

Reason:

- reflect current Worker-style dev domain setup,
- explicitly disable Terraform ownership of the `dev` record in dev env.

### 6) ECS service execute-command setting made explicit/controllable

File: `iac/modules/ecs-fargate/variables.tf`

Added variable:

- `enable_execute_command` (bool, default `true`)

File: `iac/modules/ecs-fargate/main.tf`

Set on service resource:

- `enable_execute_command = var.enable_execute_command`

Reason:

- avoid implicit/provider-default mismatch causing drift noise,
- make ECS Exec behavior explicit in module API.

### 7) ECS task definition drift guardrail (safe no-change strategy)

File: `iac/modules/ecs-fargate/main.tf`

Added lifecycle ignore on task definition:

- `ignore_changes = [container_definitions, volume]`

Reason:

- do not force Terraform to overwrite live, out-of-band task-definition wiring while stabilizing state sync,
- keep applies non-disruptive to running service setup.

### 8) ECS service drift guardrail for manual rollout revisions

File: `iac/modules/ecs-fargate/main.tf`

Added lifecycle ignore on service:

- `ignore_changes = [task_definition]`

Reason:

- prevent apply from trying to roll service back/forward solely due to manual task revision changes,
- preserve no-change posture while state is being reconciled.

## Final effect of these code changes

- Cloudflare `dev_pages` creation is prevented by default unless explicitly enabled.
- Dev DNS can be modeled as Pages or Worker-style via vars without module rewrite.
- ECS plan noise/drift from out-of-band task-definition/service revision changes is suppressed under the safe strategy.
- Terraform plans are now focused on intentional changes, reducing accidental infra mutation risk.

## Notes for follow-up (task453+)

- If/when we want Terraform to re-own `dev.kinnoo.ai`, set `manage_dev_record = true` in the target env and ensure type/content match the intended backend.
- If drift guardrails are no longer needed, remove lifecycle `ignore_changes` incrementally after confirming live ECS config has been fully codified.
