# Dev Stable to First Prod Install Checklist

Date: 2026-04-18
Owner: Solo operator
Goal: Keep Dev as long-lived integration environment and perform first clean Prod install with IaC, without reusing Dev URLs, DNS, or worker bindings.

---

## Release Strategy for This Repo

1. Dev remains Dev permanently.
2. Prod is a fresh install from the same validated code, not a rename of Dev.
3. Promotion means code and infrastructure pattern promotion, not domain/environment promotion.

Concretely in this codebase:
- Dev backend state is in iac/environments/dev.
- Prod backend state is in iac/environments/prod.
- Terraform backend state files are already split by environment in:
  - iac/environments/dev/backend.hcl
  - iac/environments/prod/backend.hcl

---

## Preconditions

1. Rollback branch exists from build:
   - stable-before-auth-migration
2. You accept dev data reset and no migration of existing dev agents.
3. No team dependencies or approval gates required beyond your own go/no-go checks.

---

## Gate Model (Exact Go/No-Go)

Use these gates exactly. Do not proceed to next gate until current gate is green.

### Gate 0: Repo + Branch Safety

Pass criteria:
1. Rollback branch exists and points to pre-auth migration baseline.
2. Working branch for auth/postgres changes is clean and reproducible.

Commands:
1. git checkout build
2. git branch stable-before-auth-migration
3. git checkout -b feature/auth-postgres-cutover
4. git status

Go if:
- stable-before-auth-migration exists
- working tree has only intended changes

---

### Gate 1: Dev Infra and DNS Baseline Is Healthy

Pass criteria:
1. Dev Terraform config validates and plans cleanly.
2. Dev DNS records resolve correctly for Dev only.
3. API health endpoint is healthy through Dev API hostname.

Commands:
1. cd iac
2. terraform fmt -check -recursive
3. terraform init -reconfigure -backend-config=environments/dev/backend.hcl
4. terraform validate
5. terraform plan -var-file=environments/dev/terraform.tfvars -out=tfplan-dev

Cloudflare verification (existing script):
1. export CLOUDFLARE_API_TOKEN=...
2. export CLOUDFLARE_ZONE_ID=...
3. bash scripts/ops/check_cloudflare_dns_setup.sh

Runtime verification:
1. curl -sS https://dev-api.kinnoo.ai/health

Go if:
- plan has expected changes only
- Cloudflare check script passes
- health returns status ok

Context files:
- iac/main.tf
- iac/modules/cloudflare/main.tf
- iac/environments/dev/terraform.tfvars
- server/app.py

---

### Gate 2: Dev Auth Migration Works End-to-End

Pass criteria:
1. Kinde-based login works for Dev domain.
2. CLI auth path works against Dev.
3. Protected routes and publish/install flows work in Dev.
4. No fallback dependence on local-only secrets that will break in Prod.

Minimum checklist:
1. Browser login/logout successful via Dev frontend and API.
2. CLI login works against Dev URL.
3. Publish, search, install, download smoke tests pass.
4. /health and /ready remain green under expected load.

Go if:
- all auth and core registry workflows pass in Dev for 24h stability window

Recommended evidence to save in notes:
1. timestamped smoke test outputs
2. short incident log (if any) and fixes

---

### Gate 3: Config Externalization Complete (No Dev Hardcoding)

Pass criteria:
1. No hardcoded dev hostnames remain in runtime logic for values that differ by env.
2. Env variables are the source of truth for domain, CORS, secrets, and backend mode.

Current relevant config surface:
- server/config.py
- server/app.py
- iac/modules/ecs-fargate/main.tf

Required checks:
1. Search for dev host strings in server and iac:
   - dev.kinnoo.ai
   - dev-api.kinnoo.ai
2. Confirm final values come from env/terraform vars for each environment.

Go if:
- hardcoded values are removed or explicitly scoped to dev-only infrastructure modules

---

### Gate 4: Prod IaC Plan Is Clean and Isolated from Dev

Pass criteria:
1. Prod backend state is used, not Dev.
2. Prod plan does not alter Dev resources.
3. Prod DNS/worker resources are separate from Dev resources.

Commands:
1. cd iac
2. terraform init -reconfigure -backend-config=environments/prod/backend.hcl
3. terraform validate
4. terraform plan -var-file=environments/prod/terraform.tfvars -out=tfplan-prod

Go if:
- plan targets only prod-named resources
- no dev record/resource changes appear

Context files:
- iac/environments/prod/backend.hcl
- iac/environments/prod/terraform.tfvars

---

### Gate 5: First Prod Install

Pass criteria:
1. Infrastructure apply succeeds.
2. DNS and TLS are valid.
3. App boots with production secrets.
4. Health/readiness are green.

Commands:
1. cd iac
2. terraform init -reconfigure -backend-config=environments/prod/backend.hcl
3. terraform apply -var-file=environments/prod/terraform.tfvars

Post-apply checks:
1. Resolve outputs:
   - terraform output alb_dns_name
   - terraform output acm_validation_record
2. Verify DNS in Cloudflare for prod hostnames (separate from dev)
3. Hit prod endpoints:
   - /health
   - /ready

Go if:
- prod endpoints are healthy and reachable over intended prod domains

---

### Gate 6: Prod Smoke + Rollback Drill

Pass criteria:
1. Prod login, publish, search, install, download smoke pass.
2. Rollback procedure is executable and tested.

Rollback drill options:
1. Infra rollback:
   - re-apply last known-good tfvars/commit for prod
2. App rollback:
   - redeploy previous known-good image tag
3. Feature-flag rollback (when metadata backend flag exists):
   - switch REGISTRY_METADATA_BACKEND from postgres to json and redeploy

Go if:
- you can restore service quickly from a documented command path

---

## Cloudflare Worker and Environment Separation Rules

Use strict separation. No shared bindings between Dev and Prod.

1. Separate hostnames
- Dev:
  - dev.kinnoo.ai
  - dev-api.kinnoo.ai
- Prod:
  - kinnoo.ai (or app.kinnoo.ai)
  - api.kinnoo.ai

2. Separate Cloudflare worker environments
- If using Workers for frontend or edge routing, define explicit envs:
  - dev environment bound to dev routes only
  - production environment bound to prod routes only
- Never attach a worker route pattern that matches both dev and prod accidentally.

3. Separate secrets per environment
- Kinde client credentials
- JWT/session/token secrets
- Any API keys

4. Terraform ownership clarity
- Keep Terraform ownership for DNS records explicit.
- In this repo, dev record management is controlled by:
  - iac/modules/cloudflare/main.tf
  - variable manage_dev_record in iac/variables.tf and env tfvars
- If a worker manages a route manually, document that route as out-of-band and avoid overlapping Terraform-managed records.

5. Cloudflare verification before and after prod cutover
- Use scripts/ops/check_cloudflare_dns_setup.sh as a baseline for dev checks.
- Add equivalent prod check script when prod records are finalized.

---

## Dev vs Prod Environment Variable Matrix

This matrix is split into current vars already used by the app and planned vars for Postgres/Auth migration.

### A. Current Runtime Vars (already used now)

| Variable | Dev | Prod | Source in repo |
|---|---|---|---|
| KINNOO_ENV | dev | production | server/config.py, iac/modules/ecs-fargate/main.tf |
| REGISTRY_STORAGE_BACKEND | local or s3 | s3 | server/config.py, iac/modules/ecs-fargate/main.tf |
| REGISTRY_LOCAL_STORAGE_ROOT | local path | /data/.registry-storage | server/config.py, iac/modules/ecs-fargate/main.tf |
| REGISTRY_S3_BUCKET | dev bucket | prod bucket | server/config.py, iac/main.tf |
| REGISTRY_S3_REGION | region | region | server/config.py |
| CORS_ORIGINS | permissive during dev | explicit prod origins only | server/config.py |
| FRONTEND_URL | https://dev.kinnoo.ai | https://kinnoo.ai or prod app host | server/config.py |
| REGISTRY_TOKEN_SIGNING_SECRET | dev secret | strong prod secret | server/app.py |
| REGISTRY_SESSION_SIGNING_SECRET | dev secret | strong prod secret | server/app.py |
| REGISTRY_REGISTER_TOKEN_SECRET | dev secret | strong prod secret | server/config.py, server/app.py |
| REGISTRY_PASSWORD_RESET_TOKEN_SECRET | dev secret | strong prod secret | server/config.py, server/app.py |

Notes:
1. In ECS today, secrets are injected as JWT_SECRET, SESSION_SECRET, ADMIN_PASSWORD in iac/modules/ecs-fargate/main.tf.
2. Align secret names with app expectations before prod cutover so the container gets the exact env keys the app reads.

### B. Planned Migration Vars (for Postgres and metadata backend)

| Variable | Dev value | Prod value | Status |
|---|---|---|---|
| REGISTRY_METADATA_BACKEND | json or postgres during rollout | postgres after cutover | planned in Postgres plan |
| REGISTRY_DATABASE_URL | dev db URL | prod db URL | planned |
| REGISTRY_DB_POOL_SIZE | small default | tuned for prod load | planned |
| REGISTRY_DB_MAX_OVERFLOW | small default | tuned for prod load | planned |
| REGISTRY_DB_POOL_RECYCLE_SECONDS | default | default/tuned | planned |

### C. Kinde/Auth Env Separation

| Variable | Dev | Prod |
|---|---|---|
| KINDE_DOMAIN / issuer | Dev tenant env | Prod tenant env |
| KINDE_CLIENT_ID | Dev app client id | Prod app client id |
| KINDE_CLIENT_SECRET | Dev secret | Prod secret |
| KINDE_REDIRECT_URI | https://dev.kinnoo.ai/callback | https://kinnoo.ai/callback (or prod app host) |
| KINDE_LOGOUT_REDIRECT_URI | Dev URL | Prod URL |
| KINDE_AUDIENCE | Dev API audience | Prod API audience |

Rule: Never reuse Dev client secret or redirect URIs in Prod.

---

## First Prod Install Procedure (Concrete)

1. Freeze a release commit
- Tag the commit that passed Gate 2 and Gate 3.

2. Build immutable image from that commit
- Push to ECR with explicit version tag, not latest-only.

3. Prepare prod tfvars and secrets
- Fill iac/environments/prod/terraform.tfvars with prod-safe values.
- Ensure Cloudflare zone id and prod DNS strategy are finalized.
- Ensure app-required secret env names are mapped in ECS task definition.

4. Apply prod infrastructure
- Use prod backend.hcl and prod tfvars only.

5. Configure/verify Cloudflare prod routes
- Confirm api.kinnoo.ai points to prod ALB target.
- Confirm prod frontend route/worker uses prod environment bindings.

6. Deploy app to prod ECS service
- Ensure task definition uses prod image tag and prod env/secrets.

7. Run prod smoke tests
- health, ready, login, publish, search, install, download.

8. Record install baseline
- Save outputs and exact deploy command history in notes for repeatability.

---

## Quick Failure Playbook

1. Prod auth fails
- Verify Kinde redirect URIs and audience for prod app.
- Verify prod secret values and names injected to container.

2. Prod domain routes to Dev backend
- Inspect Cloudflare route/record target and worker environment binding.
- Confirm no wildcard route overlaps dev and prod.

3. CORS failures in Prod
- Set CORS_ORIGINS explicitly to prod frontend origins in server/config.py-driven env.

4. App starts but not ready
- Check storage and auth/readiness dependencies from server/app.py.
- Inspect ECS logs in CloudWatch.

---

## Exit Criteria (First Prod Install Complete)

All must be true:
1. Dev remains fully functional on dev domains.
2. Prod is running on distinct prod domains and infra state.
3. Prod smoke suite passes.
4. Rollback path is documented and validated.
5. Env var matrix and secret mappings are captured and reproducible.
