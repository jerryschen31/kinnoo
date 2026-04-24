# Production Deployment Instructions (Issue #369)

Last updated: 2026-04-24
Owner: DevOps operator + SWE follow-up tasks

This runbook is the current source of truth for first production deployment of Kinnoo based on the code in this repository.

## 0) Scope and hard constraints

- Dev and Prod must remain strictly separated.
- No Dev secrets, domains, env vars, or process flows may be reused in Prod.
- The production web frontend should mirror Dev behavior, but with Prod-specific domains/config.
- If any required deployment behavior is not currently implemented in IaC/runtime/scripts, that is recorded as a tracked gap task before deployment continues.

## 1) Current repo reality (verified from code)

### 1.1 Environment-specific Terraform files already exist

- `iac/environments/dev/backend.hcl`
- `iac/environments/prod/backend.hcl`
- `iac/environments/dev/terraform.tfvars`
- `iac/environments/prod/terraform.tfvars`

### 1.2 State bucket bootstrap stack exists

- `iac/state/main.tf` can create a state bucket.
- Defaults are Dev-oriented; Prod values must be passed explicitly.

### 1.3 Major production blockers/gaps exist right now

These are tracked in task518-task521 and must be resolved before full Prod cutover:

1. Root IaC hardcodes `api_domain = "dev-api.kinnoo.ai"` in `iac/main.tf`.
2. Cloudflare module currently manages Dev records only (`dev`, `dev-api`) and does not define Prod `api`/frontend records.
3. `scripts/ops/rebuild_push_server_and_redeploy_ecs.sh` is hardcoded to `kinnoo-dev-*` ECS names.
4. Production fallback CORS defaults in `server/config.py` still point at Dev domains.
5. Terraform providers in `iac/providers.tf` and `iac/state/main.tf` hardcode profile `jerry`.

## 2) Deployment phases and go/no-go gates

Do not proceed to the next phase unless the current phase passes.

---

## Phase A - Operator preflight

### A.1 Required tools

- Terraform >= 1.10
- AWS CLI
- Docker
- Python 3

### A.2 Required shell env

```bash
export AWS_PROFILE=<prod-aws-profile>
export AWS_REGION=us-west-2
export AWS_SDK_LOAD_CONFIG=1

# Cloudflare provider uses this:
export CLOUDFLARE_API_TOKEN=<prod-cloudflare-token>

# Required Terraform variable not present in prod tfvars by default:
export TF_VAR_zone_id=<cloudflare-zone-id>
```

### A.3 Repo checks

```bash
cd /home/runner/work/kinnoo/kinnoo
python3 scripts/validate_project_manifests.py
```

### Gate A pass criteria

- Tools available.
- Credentials exported.
- Manifest validation passes.

---

## Phase B - Bootstrap Terraform state bucket for Prod

Use the dedicated state stack before the main `iac/` root stack.

```bash
cd /home/runner/work/kinnoo/kinnoo/iac/state
terraform init
terraform plan \
  -var='environment=prod' \
  -var='state_bucket_name=kinnoo-terraform-state-prod' \
  -out=tfplan-state-prod
terraform apply tfplan-state-prod
```

### Gate B pass criteria

- S3 bucket `kinnoo-terraform-state-prod` exists.
- Bucket has versioning + encryption + public-access block.

---

## Phase C - Prepare Prod runtime/IaC inputs

### C.1 Review and complete `iac/environments/prod/terraform.tfvars`

Current file includes baseline networking/backend pool vars, but operator must confirm and set all required prod-safe values.

### C.2 Confirm required runtime secrets exist (Prod namespace)

The secrets module expects these secret names for Prod (prefix `kinnoo/prod/...`):

- Managed by Terraform: `jwt-secret`, `session-secret`, `admin-password`
- Referenced out-of-band and required by ECS secret injection:
  - `AUTH_PROVIDER`
  - `KINDE_WEB_CLIENT_ID`
  - `KINDE_WEB_CLIENT_SECRET`
  - `KINDE_CLI_CLIENT_ID`
  - `KINDE_ISSUER_URL`
  - `KINDE_AUDIENCE`
  - `KINDE_WEB_REDIRECT_URI`
  - `KINDE_LOGOUT_REDIRECT_URI`
  - `JWKS_ENDPOINT_URL`
  - `TOKEN_ENDPOINT`
  - `AUTHORIZATION_ENDPOINT`
  - `LOGOUT_ENDPOINT`
  - `USERINFO_ENDPOINT`
  - `REVOCATION_ENDPOINT`
  - `REGISTRY_DATABASE_URL`

### C.3 Mandatory anti-cross-contamination checks

- No `kinnoo/dev/*` secret names in Prod task-definition wiring.
- No `dev.kinnoo.ai` or `dev-api.kinnoo.ai` in Prod env vars.
- Prod Kinde redirect/logout URIs are Prod-only.

### Gate C pass criteria

- All required Prod secrets exist.
- No Dev-prefixed secret references remain in Prod deploy plan.

---

## Phase D - Plan/apply main IaC root stack with Prod backend

```bash
cd /home/runner/work/kinnoo/kinnoo/iac
terraform init -reconfigure -backend-config=environments/prod/backend.hcl
terraform validate
terraform plan -var-file=environments/prod/terraform.tfvars -out=tfplan-prod
```

Only after plan review:

```bash
terraform apply tfplan-prod
```

### Gate D pass criteria

- Plan/apply succeed.
- Resource names are `*-prod-*` where expected.
- Plan does not attempt to mutate Dev resources.

---

## Phase E - Build/push server image and redeploy ECS

Use explicit commands (not the current helper script, which is Dev-hardcoded).

```bash
cd /home/runner/work/kinnoo/kinnoo

ECR_REPO_URI="$(terraform -chdir=iac output -raw ecr_repository_url)"
ECS_SERVICE="$(terraform -chdir=iac output -raw ecs_service_name)"
ECS_CLUSTER_ARN="$(terraform -chdir=iac output -raw ecs_cluster_arn)"
ECS_CLUSTER="${ECS_CLUSTER_ARN##*/}"

DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t "${ECR_REPO_URI}:latest" .
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPO_URI"
docker push "${ECR_REPO_URI}:latest"
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --force-new-deployment
```

### Gate E pass criteria

- New image exists in ECR.
- ECS service deployment reaches stable running state.

---

## Phase F - DNS/frontend production cutover

Current IaC is not fully production-ready for Cloudflare DNS/frontend routing (`task518`, `task519` blockers).

Until those are complete, treat Prod DNS/frontend cutover as blocked.

### Gate F pass criteria (after blockers are done)

- Prod API hostname resolves to Prod ALB target.
- Prod frontend hostname resolves to Prod frontend target/worker.
- No wildcard/route overlap that can route Prod traffic to Dev infrastructure.

---

## Phase G - Smoke tests and rollback gate

Run after Phases D/E (and F when unblocked).

### G.1 API smoke

- `GET /health` returns success.
- `GET /ready` returns success.

### G.2 Auth smoke

- Web login/logout works on Prod domain.
- CLI hosted login works with Prod registry URL.

### G.3 Registry smoke

- publish
- search
- install
- fetch/download

### G.4 Rollback drill

- Re-deploy prior known-good image tag.
- Re-apply prior known-good terraform plan/commit if needed.
- Confirm `/health` and `/ready` recovery.

### Gate G pass criteria

- All smoke tests pass.
- Rollback path is verified and executable.

---

## 3) Gap register (must be tracked and resolved)

- `task518`: Parameterize prod API/frontend domains in IaC and remove dev-domain hardcoding from root wiring.
- `task519`: Add prod-safe deploy/smoke scripts; remove dev-hardcoded ECS/script assumptions.
- `task520`: Remove dev-domain defaults from production runtime config and enforce explicit Prod CORS/frontend contract.
- `task521`: Remove hardcoded Terraform AWS profile (`jerry`) from provider config for operator portability.

## 4) Required deployment evidence artifacts

Capture and store in `notes/` after each phase:

1. Terraform plan/apply outputs for state + main stacks.
2. ECS deployment output and running task evidence.
3. DNS record evidence for Prod hostnames.
4. Smoke test command outputs.
5. Rollback drill output and timing notes.
