# Production Deployment Instructions

Source issue: <https://github.com/jerryschen31/kinnoo/issues/369>
Last updated: 2026-04-24
Audience: A DevOps operator who is **not** familiar with the Kinnoo codebase.
Baseline: The current Dev deployment (`dev.kinnoo.ai` / `dev-api.kinnoo.ai`) is stable and is the reference implementation. Prod must mirror Dev's architecture but must not share any Dev resource, secret, domain, or runtime config.

---

## How to read this runbook

- Each phase has: **Goal**, **Preconditions**, **Steps** (copy-pasteable), **Smoke check** (scripted where possible), **Gotchas**.
- Do **not** advance to the next phase unless the current phase's smoke check passes.
- Every shell snippet assumes you have set the environment variables in Phase 0.
- The Dev pipeline is documented in `notes/how-to-terraform-apply-and-redeploy-ECS.md`. This Prod runbook is the same shape, with explicit Prod safeguards and the chicken-and-egg ordering called out.
- **Open production blockers** (must be fixed before this runbook can run end-to-end) are listed in section "Known production blockers" below and tracked as `task518`-`task525`. Until those are resolved, treat the corresponding phases as blocked and stop.

---

## Operator quick map

| Phase | What it does | Approx. duration |
|-------|--------------|------------------|
| 0 | Operator preflight: tools, credentials, env vars | 15 min |
| 1 | Bootstrap Terraform state bucket for Prod | 5 min |
| 2 | Pre-create Prod secrets in AWS Secrets Manager | 30 min |
| 3 | Bootstrap initial Prod Lambda image (chicken-and-egg) | 20 min |
| 4 | First `terraform apply` for Prod root stack | 30-60 min |
| 5 | Hydrate Prod RDS connection secret | 10 min |
| 6 | Run database migrations | 10 min |
| 7 | Build/push server image and force ECS deployment | 20 min |
| 8 | DNS / Cloudflare cutover for `kinnoo.ai` and `api.kinnoo.ai` | 30 min |
| 9 | End-to-end smoke + rollback drill | 60 min |

---

## Known production blockers (do not bypass)

The following are tracked in `TASKS.txt` and must be resolved before this runbook can run end-to-end. Until then, mark the noted phases as blocked and stop:

- `task518`: `iac/main.tf` hardcodes `api_domain = "dev-api.kinnoo.ai"` and the Cloudflare module hardcodes `dev` and `dev-api` records. Blocks Phases 4 and 8.
- `task519`: `scripts/ops/rebuild_push_server_and_redeploy_ecs.sh` and `scripts/ops/check_cloudflare_dns_setup.sh` are hardcoded to `kinnoo-dev-*`. Blocks Phase 7 and Phase 8 smoke check.
- `task520`: `server/config.py` production-mode fallback CORS includes Dev origins. Blocks Phase 9 origin smoke check.
- `task521`: `iac/providers.tf` and `iac/state/main.tf` hardcode AWS profile `jerry`. Blocks Phases 1 and 4 unless you happen to use that profile name.
- `task522`: `web/wrangler.jsonc` is hardcoded to `dev.kinnoo.ai` and `https://dev-api.kinnoo.ai`. Blocks Phase 8 frontend deployment.
- `task523`: No documented or scripted procedure to bootstrap the initial Prod Lambda image. Blocks Phase 3.
- `task524`: `iac/environments/prod/terraform.tfvars` is missing required values (`lambda_security_check_image_uri`, `auth_provider`, and any prod-only DNS overrides). Blocks Phase 4.
- `task525`: No script to safely pre-create the `REGISTRY_DATABASE_URL` stub secret for first apply. Blocks Phase 2.

Reference: `task517` (this runbook) is the parent of these gaps under `feature121`.

---

## Phase 0 - Operator preflight

**Goal**: Workstation is ready to run all subsequent commands.

### Preconditions

- Read access to the GitHub repo and a clean local clone.
- AWS account for Prod (separate account or separate IAM principals from Dev) with admin/devops permissions.
- Cloudflare account with `kinnoo.ai` zone and an API token scoped to that zone.
- Kinde Prod application(s) already provisioned (tenant + web app + CLI app).

### Steps

1. Install/verify tooling on your workstation:

   ```bash
   terraform version    # must be >= 1.10
   aws --version
   docker --version
   docker buildx version
   python3 --version    # must be >= 3.11
   jq --version
   ```

2. Log in to AWS using the operator's credentials (the chosen profile name is up to the operator after `task521` is fixed):

   ```bash
   aws sso login --profile <prod-profile>      # or aws configure sso
   aws sts get-caller-identity --profile <prod-profile>
   ```

3. Set the operator environment for the rest of the runbook:

   ```bash
   export KINNOO_ROOT="$(pwd)"                          # repo root after `cd` into clone
   export AWS_PROFILE=<prod-profile>
   export AWS_REGION=us-west-2
   export AWS_PAGER=""
   export CLOUDFLARE_API_TOKEN=<prod-cloudflare-token>
   export CLOUDFLARE_ZONE_ID=<kinnoo-ai-zone-id>
   export TF_VAR_zone_id="$CLOUDFLARE_ZONE_ID"
   ```

4. Sanity-check the repo manifests:

   ```bash
   cd "$KINNOO_ROOT"
   python3 scripts/validate_project_manifests.py
   ```

### Smoke check

```bash
# All of these should print non-empty values without errors.
terraform version
aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text
curl -fsS -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID" \
  | jq -r '.success, .result.name'
python3 scripts/validate_project_manifests.py
```

Expected: AWS account ID printed, Cloudflare reports `true` and `kinnoo.ai`, manifest validation prints `Validation passed`.

### Gotchas

- The Cloudflare token must have `Zone.DNS:Edit` and `Zone.Zone:Read` for the `kinnoo.ai` zone, not the API key. Tokens are zone-scoped; an account-scoped token may still work but is unnecessarily broad.
- `TF_VAR_zone_id` is **required** — `iac/variables.tf` declares `zone_id` with no default. Forgetting it causes `terraform plan` to prompt interactively or fail in CI.
- Do not reuse your Dev `AWS_PROFILE` or Dev Cloudflare token. The whole point of Phase 0 is to fence Prod off from Dev.

---

## Phase 1 - Bootstrap Terraform state bucket for Prod

**Goal**: Create the S3 bucket `kinnoo-terraform-state-prod` referenced by `iac/environments/prod/backend.hcl`. This bucket holds the Prod Terraform state.

### Preconditions

- Phase 0 complete.
- `task521` is done OR you happen to use AWS profile `jerry` (current hardcode in `iac/state/main.tf`). Otherwise you must temporarily set the profile in your shell.

### Steps

```bash
cd "$KINNOO_ROOT/iac/state"
terraform init
terraform plan \
  -var='environment=prod' \
  -var='state_bucket_name=kinnoo-terraform-state-prod' \
  -out=tfplan-state-prod
terraform apply tfplan-state-prod
```

### Smoke check

```bash
aws s3api get-bucket-versioning --bucket kinnoo-terraform-state-prod \
  --query Status --output text
# Expected: Enabled

aws s3api get-bucket-encryption --bucket kinnoo-terraform-state-prod \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' \
  --output text
# Expected: AES256

aws s3api get-public-access-block --bucket kinnoo-terraform-state-prod \
  --query PublicAccessBlockConfiguration --output json
# Expected: all four values true
```

### Gotchas

- This stack uses local state (it bootstraps the remote state itself), so make sure you do not commit the resulting `terraform.tfstate` files in `iac/state/` to git. They are already gitignored, but verify with `git status`.
- S3 bucket names are global. If `kinnoo-terraform-state-prod` is already taken in another AWS account, choose a different name and **also** update `iac/environments/prod/backend.hcl` accordingly.

---

## Phase 2 - Pre-create Prod secrets in AWS Secrets Manager

**Goal**: Create every secret that the IaC `secrets` module reads via `data "aws_secretsmanager_secret"`. If any of these are missing, `terraform plan` in Phase 4 will fail with `Error: Secrets Manager Secret not found`.

### Preconditions

- Phase 1 complete.
- You have the Kinde Prod app credentials and OIDC endpoints to hand.

### What the IaC reads (from `iac/modules/secrets/main.tf`)

These secret names are referenced (must exist before Phase 4) and consumed by ECS task definition for runtime injection:

```text
kinnoo/prod/AUTH_PROVIDER
kinnoo/prod/KINDE_WEB_CLIENT_ID
kinnoo/prod/KINDE_WEB_CLIENT_SECRET
kinnoo/prod/KINDE_CLI_CLIENT_ID
kinnoo/prod/KINDE_ISSUER_URL
kinnoo/prod/KINDE_AUDIENCE
kinnoo/prod/KINDE_WEB_REDIRECT_URI
kinnoo/prod/KINDE_LOGOUT_REDIRECT_URI
kinnoo/prod/JWKS_ENDPOINT_URL
kinnoo/prod/TOKEN_ENDPOINT
kinnoo/prod/AUTHORIZATION_ENDPOINT
kinnoo/prod/LOGOUT_ENDPOINT
kinnoo/prod/USERINFO_ENDPOINT
kinnoo/prod/REVOCATION_ENDPOINT
/kinnoo/prod/REGISTRY_DATABASE_URL          # note the leading slash
```

These are **created** by the secrets module (do **not** pre-create them):

```text
kinnoo/prod/jwt-secret
kinnoo/prod/session-secret
kinnoo/prod/admin-password
```

### Steps

1. Create each Kinde-related secret with its real value. Each secret must store JSON whose key matches the secret name's last segment, because the ECS task definition uses Secrets Manager `valueFrom` with a JSON pointer:

   ```bash
   create_kinde_secret() {
     local name="$1"
     local key="${name##*/}"
     local value="$2"
     local payload
     payload="$(python3 -c 'import json,sys; print(json.dumps({sys.argv[1]: sys.argv[2]}))' "$key" "$value")"
     aws secretsmanager create-secret \
       --name "$name" \
       --secret-string "$payload" >/dev/null \
       || aws secretsmanager put-secret-value \
            --secret-id "$name" \
            --secret-string "$payload" >/dev/null
     echo "ok: $name"
   }

   create_kinde_secret kinnoo/prod/AUTH_PROVIDER          "oidc_kinde"
   create_kinde_secret kinnoo/prod/KINDE_WEB_CLIENT_ID    "<prod-web-client-id>"
   create_kinde_secret kinnoo/prod/KINDE_WEB_CLIENT_SECRET "<prod-web-client-secret>"
   create_kinde_secret kinnoo/prod/KINDE_CLI_CLIENT_ID    "<prod-cli-client-id>"
   create_kinde_secret kinnoo/prod/KINDE_ISSUER_URL       "https://<your-tenant>.kinde.com"
   create_kinde_secret kinnoo/prod/KINDE_AUDIENCE         "<prod-api-audience>"
   create_kinde_secret kinnoo/prod/KINDE_WEB_REDIRECT_URI "https://kinnoo.ai/api/auth/callback"
   create_kinde_secret kinnoo/prod/KINDE_LOGOUT_REDIRECT_URI "https://kinnoo.ai"
   create_kinde_secret kinnoo/prod/JWKS_ENDPOINT_URL      "https://<your-tenant>.kinde.com/.well-known/jwks"
   create_kinde_secret kinnoo/prod/TOKEN_ENDPOINT         "https://<your-tenant>.kinde.com/oauth2/token"
   create_kinde_secret kinnoo/prod/AUTHORIZATION_ENDPOINT "https://<your-tenant>.kinde.com/oauth2/auth"
   create_kinde_secret kinnoo/prod/LOGOUT_ENDPOINT        "https://<your-tenant>.kinde.com/logout"
   create_kinde_secret kinnoo/prod/USERINFO_ENDPOINT      "https://<your-tenant>.kinde.com/oauth2/v2/user_profile"
   create_kinde_secret kinnoo/prod/REVOCATION_ENDPOINT    "https://<your-tenant>.kinde.com/oauth2/revoke"
   ```

2. Pre-create a **stub** REGISTRY_DATABASE_URL secret. Phase 5 overwrites it with the real RDS URL. The stub lets Phase 4 plan/apply succeed because the data source can resolve the secret. The leading slash is required to match `iac/modules/secrets/main.tf`:

   ```bash
   aws secretsmanager create-secret \
     --name "/kinnoo/prod/REGISTRY_DATABASE_URL" \
     --secret-string '{"REGISTRY_DATABASE_URL":"postgresql+psycopg://placeholder:placeholder@placeholder:5432/placeholder"}' \
     >/dev/null \
     || echo "Already exists, leaving as-is."
   ```

### Smoke check

```bash
required_secrets=(
  kinnoo/prod/AUTH_PROVIDER
  kinnoo/prod/KINDE_WEB_CLIENT_ID
  kinnoo/prod/KINDE_WEB_CLIENT_SECRET
  kinnoo/prod/KINDE_CLI_CLIENT_ID
  kinnoo/prod/KINDE_ISSUER_URL
  kinnoo/prod/KINDE_AUDIENCE
  kinnoo/prod/KINDE_WEB_REDIRECT_URI
  kinnoo/prod/KINDE_LOGOUT_REDIRECT_URI
  kinnoo/prod/JWKS_ENDPOINT_URL
  kinnoo/prod/TOKEN_ENDPOINT
  kinnoo/prod/AUTHORIZATION_ENDPOINT
  kinnoo/prod/LOGOUT_ENDPOINT
  kinnoo/prod/USERINFO_ENDPOINT
  kinnoo/prod/REVOCATION_ENDPOINT
  /kinnoo/prod/REGISTRY_DATABASE_URL
)
missing=0
for s in "${required_secrets[@]}"; do
  if ! aws secretsmanager describe-secret --secret-id "$s" >/dev/null 2>&1; then
    echo "MISSING: $s"
    missing=$((missing+1))
  else
    echo "ok: $s"
  fi
done
[ "$missing" -eq 0 ] && echo "All required prod secrets present."
```

Expected: `All required prod secrets present.`

### Gotchas

- The Kinde redirect URIs you put into `KINDE_WEB_REDIRECT_URI` and `KINDE_LOGOUT_REDIRECT_URI` **must also be configured in the Kinde Prod app dashboard**. Otherwise login will fail at callback time with `redirect_uri mismatch`.
- The JSON key inside each secret must equal the secret name's last segment. The ECS task definition extracts the value with the `secret-arn:KEY::` pointer (see `iac/modules/secrets/main.tf` `format("%s:%s::", arn, "KEY")`). Storing a raw string instead of JSON will produce empty env vars at runtime.
- For `REGISTRY_DATABASE_URL`, the secret name has a **leading slash** (`/kinnoo/prod/REGISTRY_DATABASE_URL`). Do not create `kinnoo/prod/REGISTRY_DATABASE_URL` — the data source will not find it.
- Do **not** pre-create `kinnoo/prod/jwt-secret`, `kinnoo/prod/session-secret`, `kinnoo/prod/admin-password`. These are managed by Terraform and will conflict.

---

## Phase 3 - Bootstrap initial Prod Lambda image (chicken-and-egg)

**Goal**: Push an initial security-check Lambda image to the **Prod** ECR repository so Phase 4's apply has a valid `lambda_security_check_image_uri` to set. This phase is the documented workaround for the chicken-and-egg between `iac/modules/lambda-security-check` (which requires an `image_uri`) and `iac/modules/ecr` (which creates the Lambda ECR repo as part of the same apply).

### Preconditions

- Phase 2 complete.
- `task523` is done (otherwise the operator must follow the manual variant below).

### Steps (target end state once `task523` ships an env-aware bootstrap script)

```bash
cd "$KINNOO_ROOT"
ENVIRONMENT=prod scripts/ops/build_and_push_lambda_security_check_image.sh v0
```

### Manual interim variant (until `task523` is done)

The current script in `scripts/ops/build_and_push_lambda_security_check_image.sh` reads `terraform output lambda_security_check_ecr_repository_url`, which does not yet exist before first apply. Use this manual sequence until the script is environment-aware:

```bash
cd "$KINNOO_ROOT/iac"

# Targeted apply: create only the Prod Lambda ECR repo.
# The placeholder URI must match the private-ECR regex enforced by
# `iac/variables.tf` (`^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/.+:.+$`).
# Resolve your account id and pass a placeholder that satisfies the regex; the
# value is never pulled because the targeted apply does not create the Lambda.
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
PLACEHOLDER_LAMBDA_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/kinnoo-prod-lambda-security-check:bootstrap"

terraform init -reconfigure -backend-config=environments/prod/backend.hcl
terraform apply \
  -var-file=environments/prod/terraform.tfvars \
  -var="lambda_security_check_image_uri=${PLACEHOLDER_LAMBDA_URI}" \
  -target=module.ecr

LAMBDA_ECR_URI="$(terraform output -raw lambda_security_check_ecr_repository_url)"
LAMBDA_TAG="v0"

cd "$KINNOO_ROOT"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$LAMBDA_ECR_URI"

docker buildx build \
  --platform linux/amd64 --provenance=false --sbom=false \
  -f Dockerfile.lambda \
  -t "${LAMBDA_ECR_URI}:${LAMBDA_TAG}" --push .
```

Then update `iac/environments/prod/terraform.tfvars` with the resulting URI:

```hcl
lambda_security_check_image_uri = "<account-id>.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:v0"
```

### Smoke check

```bash
LAMBDA_ECR_URI="$(terraform -chdir="$KINNOO_ROOT/iac" output -raw lambda_security_check_ecr_repository_url)"
aws ecr describe-images \
  --repository-name "${LAMBDA_ECR_URI##*/}" \
  --query 'length(imageDetails)' --output text
# Expected: >= 1
```

### Gotchas

- The temporary `-var=lambda_security_check_image_uri=...` in the targeted apply is needed because `iac/variables.tf` declares the variable with `nullable = false` and a regex that requires a **private** ECR URI of the form `^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/.+:.+$`. Plain `terraform apply -target=module.ecr` will refuse to plan without a value, and a public ECR URI like `public.ecr.aws/lambda/python:3.11` will fail the regex. Use a placeholder that matches the regex (the value is never pulled because the targeted apply does not create the Lambda function).
- Lambda images **must be `linux/amd64`**. If you build on Apple Silicon without `--platform linux/amd64`, Lambda will reject the image at create time.
- Use a real version tag (e.g. `v0`, `2026-04-24-001`), not `latest`, so subsequent deploys can be rolled back deterministically.

---

## Phase 4 - First `terraform apply` for Prod root stack

**Goal**: Stand up VPC, RDS, ECS, ALB, ECR, IAM, Lambda, secrets, and (still hardcoded to dev domains today) Cloudflare records.

### Preconditions

- Phases 1, 2, 3 complete.
- `task518` and `task524` are done. Until then the apply will either target dev DNS records or fail validation.
- `iac/environments/prod/terraform.tfvars` includes (post-`task524`) at minimum:
  - `lambda_security_check_image_uri = "<account>.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:<tag>"`
  - `auth_provider = "oidc_kinde"`
  - any prod-specific DNS overrides exposed by `task518`.

### Steps

```bash
cd "$KINNOO_ROOT/iac"
terraform init -reconfigure -backend-config=environments/prod/backend.hcl
terraform validate
terraform plan -var-file=environments/prod/terraform.tfvars -out=tfplan-prod
# REVIEW the plan. Do not skip this. Look for any `~` or `-` that touches
# resources whose name contains `dev` - that is a red flag.
terraform apply tfplan-prod
```

### Smoke check

```bash
cd "$KINNOO_ROOT/iac"

terraform output -raw ecs_cluster_arn          | grep -q 'kinnoo-prod-cluster$'   && echo 'ok: ecs cluster'
terraform output -raw ecs_service_name         | grep -q '^kinnoo-prod-service$'  && echo 'ok: ecs service'
terraform output -raw ecr_repository_url       | grep -q '/kinnoo-prod-server$'   && echo 'ok: ecr server'
terraform output -raw alb_dns_name             | grep -qE '\.elb\.amazonaws\.com$' && echo 'ok: alb dns'
terraform output -raw registry_db_identifier   | grep -q '^kinnoo-prod-postgres$' && echo 'ok: rds id'

# RDS multi-az and deletion protection must be on for prod (see iac/modules/rds-postgres/main.tf).
DB_ID="$(terraform output -raw registry_db_identifier)"
aws rds describe-db-instances --db-instance-identifier "$DB_ID" \
  --query 'DBInstances[0].[MultiAZ,DeletionProtection,StorageEncrypted]' --output text
# Expected: True   True   True
```

### Gotchas

- The very first apply of `module.cloudflare` will fail until `task518` is done, because `iac/modules/cloudflare/main.tf` only models `dev` and `dev-api` records. If you run a plan today against the prod backend, expect it to attempt to mutate dev records — this is exactly the cross-contamination this runbook forbids. **Stop and resolve `task518` first.**
- ACM DNS validation can take 5-30 minutes. The ALB HTTPS listener depends on certificate validation, which depends on the Cloudflare validation CNAME being created. If the apply hangs at the ACM resource, check the validation CNAME exists in Cloudflare and is **not proxied** (orange cloud must be off).
- RDS first creation typically takes 10-15 minutes. Do not Ctrl-C; just let `terraform apply` finish.

---

## Phase 5 - Hydrate Prod RDS connection secret

**Goal**: Replace the placeholder value of `/kinnoo/prod/REGISTRY_DATABASE_URL` (created in Phase 2) with a real connection string built from the RDS-managed master password and the freshly created RDS endpoint.

### Preconditions

- Phase 4 complete (RDS exists).

### Steps

```bash
cd "$KINNOO_ROOT"
DB_ID="$(terraform -chdir=iac output -raw registry_db_identifier)"
source scripts/ops/refresh_registry_database_url_secret.sh
refresh_registry_database_url_secret "$DB_ID" prod "$AWS_REGION" kinnoo
```

The function above:
1. Reads the RDS-managed master credential JSON from Secrets Manager.
2. Reads the RDS endpoint and port.
3. Builds `postgresql+psycopg://<user>:<pwd>@<host>:<port>/kinnoo_registry`.
4. Writes JSON `{"REGISTRY_DATABASE_URL": "..."}` into `/kinnoo/prod/REGISTRY_DATABASE_URL`.

### Smoke check

```bash
aws secretsmanager get-secret-value \
  --secret-id "/kinnoo/prod/REGISTRY_DATABASE_URL" \
  --query SecretString --output text \
  | python3 -c 'import json,sys; v=json.loads(sys.stdin.read())["REGISTRY_DATABASE_URL"]; \
                assert v.startswith("postgresql+psycopg://"), v; \
                assert "placeholder" not in v, "still placeholder"; \
                print("ok: REGISTRY_DATABASE_URL hydrated for prod")'
```

### Gotchas

- The script writes the URL with **userinfo URL-encoded** so RDS-generated symbols in the password do not break the DSN. If you build the URL by hand instead, remember to URL-encode `@`, `:`, `/`, `#`, `?`, and `%` in the password.
- The driver scheme is `postgresql+psycopg` (sync). Server runtime uses sync engine for migrations and async for some paths via SQLAlchemy. Do **not** change to `psycopg2` or `asyncpg` here; the server resolves drivers internally.
- This script does not restart ECS. Phase 7 will force a new deployment that picks up the hydrated secret.

---

## Phase 6 - Run database migrations

**Goal**: Apply Alembic migrations against the new Prod RDS so the schema is ready before any traffic hits Postgres-backed paths.

### Preconditions

- Phase 5 complete.
- ECS Exec is enabled (it is, by default in `iac/modules/ecs-fargate/variables.tf`: `enable_execute_command = true`).

### Steps

Pick one of two approaches.

**Option A (recommended for first migration): run via ECS Exec inside the live task**

```bash
CLUSTER="$(terraform -chdir="$KINNOO_ROOT/iac" output -raw ecs_cluster_arn | awk -F/ '{print $NF}')"
SERVICE="$(terraform -chdir="$KINNOO_ROOT/iac" output -raw ecs_service_name)"

# Wait for Phase 7 to deploy a real image first if this is the very first deploy.
TASK_ARN="$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" \
  --query 'taskArns[0]' --output text)"

aws ecs execute-command \
  --cluster "$CLUSTER" --task "$TASK_ARN" \
  --container kinnoo-server \
  --interactive --command "python3 -m server.cli db migrate"
```

**Option B: run from a workstation with VPN/bastion access to the RDS instance**

Only do this if the operator workstation has network access to the private subnet (e.g. via SSM Session Manager port forwarding):

```bash
aws ssm start-session --target <bastion-instance-id> \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters host="<rds-endpoint>",portNumber="5432",localPortNumber="5432"

# In another shell:
cd "$KINNOO_ROOT"
export REGISTRY_DATABASE_URL="$(aws secretsmanager get-secret-value \
  --secret-id /kinnoo/prod/REGISTRY_DATABASE_URL \
  --query SecretString --output text | jq -r .REGISTRY_DATABASE_URL \
  | sed -E 's#@[^/]+:5432#@127.0.0.1:5432#')"
python3 -m server.cli db migrate
```

### Smoke check

```bash
# Inside the ECS Exec session OR from a workstation with DB access:
python3 -m alembic -c server/database/migrations/alembic.ini current
# Expected: prints the head revision (matches files in
# server/database/migrations/versions/) without errors.
```

### Gotchas

- Phase 6 is logically **after** Phase 5 but **may need Phase 7 first** if you are using Option A: there has to be a running task to `ecs execute-command` into. If this is the very first deploy, push the server image (Phase 7) first, then run migrations via the new task.
- If `ecs execute-command` errors with `InvalidParameterException`, confirm `enable_execute_command = true` is set on the service and the task role has the `ssmmessages:*` policies (already wired in `iac/modules/iam`).

---

## Phase 7 - Build/push server image and force ECS deployment

**Goal**: Publish the production server container image to the Prod ECR `kinnoo-prod-server` repository and force ECS to redeploy.

### Preconditions

- Phase 6 complete (migrations applied; OR ready to apply via Option A immediately after this phase).
- `task519` is done (otherwise the helper script targets dev). Until then, use the inline commands below.

### Steps (until `task519` ships an env-aware helper)

```bash
cd "$KINNOO_ROOT"
ECR_REPO_URI="$(terraform -chdir=iac output -raw ecr_repository_url)"
ECS_SERVICE="$(terraform -chdir=iac output -raw ecs_service_name)"
ECS_CLUSTER="$(terraform -chdir=iac output -raw ecs_cluster_arn | awk -F/ '{print $NF}')"
IMAGE_TAG="$(git rev-parse --short HEAD)"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REPO_URI"

DOCKER_BUILDKIT=1 docker build \
  --platform linux/amd64 \
  -t "${ECR_REPO_URI}:${IMAGE_TAG}" \
  -t "${ECR_REPO_URI}:latest" .

docker push "${ECR_REPO_URI}:${IMAGE_TAG}"
docker push "${ECR_REPO_URI}:latest"

aws ecs update-service \
  --cluster "$ECS_CLUSTER" \
  --service "$ECS_SERVICE" \
  --force-new-deployment >/dev/null

aws ecs wait services-stable \
  --cluster "$ECS_CLUSTER" \
  --services "$ECS_SERVICE"
```

### Smoke check

```bash
# 1. Service has running tasks and is stable.
aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].[runningCount,desiredCount,deployments[0].rolloutState]' --output text
# Expected: "1 1 COMPLETED" (or higher if desired_count was raised).

# 2. ALB target group has at least one healthy target.
TG_ARN="$(terraform -chdir="$KINNOO_ROOT/iac" output -raw alb_target_group_arn)"
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" \
  --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' --output text
# Expected: >= 1

# 3. Direct ALB /health (bypassing Cloudflare) returns ok.
ALB_DNS="$(terraform -chdir="$KINNOO_ROOT/iac" output -raw alb_dns_name)"
# ALB has only an HTTPS listener; the ALB cert is for api.kinnoo.ai (post-task518),
# so use --resolve to send the right SNI without DNS being live yet.
curl -fsS --resolve "api.kinnoo.ai:443:$(dig +short "$ALB_DNS" | head -n1)" \
  https://api.kinnoo.ai/health | jq .
# Expected: {"status": "ok", "version": "<x.y.z>"}
```

### Gotchas

- Apple Silicon laptops must use `--platform linux/amd64`; Fargate runs on x86_64.
- The ECS task definition mounts EFS at `/data` for SQLite auth state and local registry storage fallback. EFS mount targets are created in the same subnets as the ECS service. If a task fails to start with `ResourceInitializationError` mentioning `efs`, check that all public subnets have a corresponding EFS mount target (Terraform creates one per subnet — re-apply if you added subnets later).
- The first deploy can take 5-10 minutes for the target group to mark the task healthy because `/health` polling happens at 30s intervals (see `iac/modules/alb/main.tf`).

---

## Phase 8 - DNS / Cloudflare cutover for `kinnoo.ai` and `api.kinnoo.ai`

**Goal**: Route production traffic. After `task518` and `task522`:

- `kinnoo.ai` (and optionally `www.kinnoo.ai`) -> Cloudflare Pages/Worker serving the `web/` frontend with `BACKEND_URL=https://api.kinnoo.ai`.
- `api.kinnoo.ai` -> proxied CNAME to the Prod ALB DNS name.
- ACM validation CNAME for `api.kinnoo.ai` -> non-proxied CNAME at `acm-validations.aws`.

### Preconditions

- Phase 7 complete with `/health` proven healthy via direct ALB.
- `task518` (Cloudflare module supports prod `api` + frontend) and `task522` (web wrangler prod config) are done.

### Steps

1. Re-run `terraform apply` in `iac/` so `module.cloudflare` creates the prod records.
2. Deploy the web frontend Worker against the prod wrangler config (added by `task522`):

   ```bash
   cd "$KINNOO_ROOT/web"
   npx wrangler deploy --config wrangler.prod.jsonc
   ```

3. In the Kinde Prod app, confirm `https://kinnoo.ai/api/auth/callback` and `https://kinnoo.ai` are in the allowed redirect/logout URLs.

### Smoke check

```bash
# A Prod-aware version of scripts/ops/check_cloudflare_dns_setup.sh is delivered by task519.
# Until then, ad-hoc checks:

# 1. api.kinnoo.ai resolves to a Cloudflare-proxied CNAME.
dig +short api.kinnoo.ai | head -n5
# Expected: A records owned by Cloudflare (e.g. 104.x / 172.x), not the raw ELB IP.

# 2. HTTPS terminates correctly and /health returns ok.
curl -fsS https://api.kinnoo.ai/health | jq .
# Expected: {"status":"ok","version":"..."}

# 3. /ready returns ready.
curl -fsS https://api.kinnoo.ai/ready | jq .
# Expected: {"status":"ready","checks":{"s3":true,"auth_store":true,"db":true}}

# 4. Frontend serves and reports correct backend.
curl -fsSI https://kinnoo.ai | head -n5
# Expected: HTTP/2 200, Server: cloudflare
```

### Gotchas

- ACM validation CNAME **must not be proxied** (orange cloud off). Proxying breaks DNS-01 validation.
- The frontend Worker must self-reference (`WORKER_SELF_REFERENCE`) for the Open-Next adapter (see `web/wrangler.jsonc`). The prod wrangler config from `task522` must keep this binding and switch only `name`, `routes`, and `vars.BACKEND_URL`.
- TTL on these records is fine at default (`ttl = 1` means "auto" in Cloudflare's Terraform provider).

---

## Phase 9 - End-to-end smoke and rollback drill

**Goal**: Prove the deployed Prod environment works for the user-visible flows that matter, and prove rollback works *before* you announce go-live.

### Preconditions

- Phases 0-8 complete.

### Smoke check (run all of these and require all to pass)

```bash
# 9.1 Health and readiness over public DNS.
curl -fsS https://api.kinnoo.ai/health   | jq -e '.status == "ok"'
curl -fsS https://api.kinnoo.ai/ready    | jq -e '.status == "ready"'
curl -fsS https://api.kinnoo.ai/ready    | jq -e '.checks.db == true and .checks.s3 == true and .checks.auth_store == true'

# 9.2 CORS contract in production mode rejects an arbitrary unknown origin.
curl -fsS -o /dev/null -w '%{http_code}\n' \
  -H 'Origin: https://evil.example.com' \
  -H 'Access-Control-Request-Method: GET' \
  -X OPTIONS https://api.kinnoo.ai/api/search
# Expected: 400 (CORS rejected by FastAPI middleware) or 403, NOT 200 with allow-origin.

# 9.3 Frontend loads and proxies API.
curl -fsS https://kinnoo.ai | grep -qi '<html' && echo 'ok: frontend html'
curl -fsS https://kinnoo.ai/api/health | jq -e '.status == "ok"' && echo 'ok: frontend->api proxy'

# 9.4 Auth discovery endpoint returns prod issuer.
curl -fsS https://api.kinnoo.ai/api/auth/config \
  | jq -e '.issuer | startswith("https://")' && echo 'ok: auth config'

# 9.5 CLI smoke against prod registry.
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
python3 -m kinnoo --version
python3 -m kinnoo search ""    # expect empty or seeded results, no auth error
```

### Manual flows (perform with at least one real Kinde Prod user)

1. Web login at `https://kinnoo.ai` -> redirected to Kinde -> back to `kinnoo.ai` authenticated.
2. CLI login: `kinnoo login` -> browser flow -> token stored.
3. Publish a small test agent: `kinnoo init chatgpt smoke-agent && kinnoo publish ./smoke-agent --pack --strict --remote`.
4. `kinnoo search smoke-agent` returns the published agent.
5. `kinnoo install smoke-agent` succeeds.
6. `kinnoo logout` clears local state.
7. Web logout from `kinnoo.ai` clears Kinde session.

### Rollback drill (mandatory before go-live announcement)

1. Note the current image tag: `aws ecs describe-task-definition --task-definition kinnoo-prod-server --query 'taskDefinition.containerDefinitions[0].image' --output text`.
2. Re-deploy the previous known-good image tag:

   ```bash
   PREV_TAG=<previous-tag>
   aws ecs update-service \
     --cluster kinnoo-prod-cluster --service kinnoo-prod-service \
     --task-definition "$(aws ecs register-task-definition \
        --cli-input-json "$(aws ecs describe-task-definition \
           --task-definition kinnoo-prod-server \
           --query 'taskDefinition' \
           | jq --arg img "${ECR_REPO_URI}:${PREV_TAG}" \
                '.containerDefinitions[0].image=$img
                 | del(.taskDefinitionArn,.revision,.status,
                       .requiresAttributes,.compatibilities,
                       .registeredAt,.registeredBy)')" \
        --query 'taskDefinition.taskDefinitionArn' --output text)" \
     --force-new-deployment
   aws ecs wait services-stable --cluster kinnoo-prod-cluster --services kinnoo-prod-service
   curl -fsS https://api.kinnoo.ai/health | jq -e '.status == "ok"'
   ```

3. Re-deploy the current tag again the same way to return to the rolled-forward state.
4. Capture the timing of both transitions in `notes/prod-go-live-evidence.md` (operator creates this file).

### Gotchas

- 9.2 will fail (return `200` with allow-origin) until `task520` removes the dev-domain CORS fallback. Treat that as a Phase 9 blocker.
- The CLI smoke (`9.5`) will fail unauthenticated requests on protected endpoints. Use only `--version` and an unauthenticated `search` (which is rate-limited but public).
- During the rollback drill, do **not** delete the new task definition revision; AWS retains revisions for forensic comparison and you may need to roll forward again.

---

## Required deployment evidence artifacts

Capture and store under `notes/` as the operator works through phases:

1. `notes/prod-go-live-evidence.md` containing:
   - Phase-by-phase smoke check outputs (copy/paste of the commands above and their results).
   - Terraform apply summary (resources added/changed/destroyed counts).
   - ECS deployment IDs and timestamps for the initial deploy and the rollback drill.
   - DNS record screenshots or `dig +short` outputs for `kinnoo.ai`, `www.kinnoo.ai` (if used), `api.kinnoo.ai`, and the ACM validation CNAME.
   - Manual flow sign-off from the operator running 9 manual flows.

---

## Cross-contamination guardrails (must hold throughout)

- No resource in Prod has a name that starts with `kinnoo-dev-` or contains `dev-api`.
- No secret read by Prod ECS lives under `kinnoo/dev/...`.
- No environment variable in the Prod ECS task definition references `dev.kinnoo.ai` or `dev-api.kinnoo.ai`.
- Cloudflare records for `dev.kinnoo.ai` and `dev-api.kinnoo.ai` are untouched by `terraform apply` against the prod backend.
- Prod and Dev use distinct Kinde apps; no Kinde client ID/secret value appears in both Secrets Manager namespaces.

A quick scan you can run any time:

```bash
aws ecs describe-task-definition --task-definition kinnoo-prod-server \
  --query 'taskDefinition.containerDefinitions[0].[environment,secrets]' \
  --output json | grep -E 'dev\.kinnoo\.ai|dev-api\.kinnoo\.ai|kinnoo/dev/' \
  && { echo 'CROSS-CONTAMINATION DETECTED'; exit 1; } \
  || echo 'ok: no dev references in prod task definition'
```
