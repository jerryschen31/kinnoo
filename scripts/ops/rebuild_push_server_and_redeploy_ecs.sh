#!/usr/bin/env bash
#
# Rebuild the server image and force an ECS service redeploy.
#
# Environment-aware (task519): pass --env dev|prod (or set ENVIRONMENT=...).
# ECS cluster/service and ECR repo are resolved from terraform outputs of the
# selected environment, not from hardcoded `kinnoo-dev-*` names.
#
# Usage:
#   scripts/ops/rebuild_push_server_and_redeploy_ecs.sh [--env dev|prod]
#   ENVIRONMENT=prod scripts/ops/rebuild_push_server_and_redeploy_ecs.sh
#
# Optional overrides (advanced; rarely needed):
#   ECS_CLUSTER=...    Override resolved cluster name
#   ECS_SERVICE=...    Override resolved service name
#   ECR_REPO_URI=...   Override resolved ECR URI
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IAC_DIR="$ROOT_DIR/iac"

ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-west-2}"
DRY_RUN="${DRY_RUN:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env|--environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --region)            AWS_REGION="${2:-}"; shift 2 ;;
    --dry-run)           DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '1,20p' "$0" >&2
      exit 0 ;;
    *) echo "[error] Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "[error] --env must be 'dev' or 'prod' (got: ${ENVIRONMENT})" >&2
  exit 2
fi

for cmd in terraform docker aws; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "$cmd is required but not found in PATH." >&2
    exit 1
  fi
done

if [[ ! -f "$ROOT_DIR/Dockerfile" ]]; then
  echo "Missing Dockerfile at repo root: $ROOT_DIR/Dockerfile" >&2
  exit 1
fi

BACKEND_HCL="$IAC_DIR/environments/${ENVIRONMENT}/backend.hcl"
TFVARS_FILE="$IAC_DIR/environments/${ENVIRONMENT}/terraform.tfvars"
if [[ ! -f "$BACKEND_HCL" ]]; then
  echo "[error] Missing backend file: $BACKEND_HCL" >&2
  exit 1
fi

export AWS_REGION

echo "[info] Initializing terraform against ${ENVIRONMENT} backend..."
if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] terraform -chdir=$IAC_DIR init -reconfigure -backend-config=$BACKEND_HCL"
else
  terraform -chdir="$IAC_DIR" init -reconfigure -backend-config="$BACKEND_HCL" >/dev/null
fi

resolve_output() {
  local name="$1"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo ""
    return 0
  fi
  terraform -chdir="$IAC_DIR" output -raw "$name" 2>/dev/null || true
}

ECR_REPO_URI="${ECR_REPO_URI:-$(resolve_output ecr_repository_url)}"
if [[ -z "$ECR_REPO_URI" && "$DRY_RUN" != "1" ]]; then
  ECR_REPO_URI="$(resolve_output ecr_repo_uri)"
fi

ECS_SERVICE="${ECS_SERVICE:-$(resolve_output ecs_service_name)}"
ECS_CLUSTER="${ECS_CLUSTER:-}"
if [[ -z "$ECS_CLUSTER" ]]; then
  ECS_CLUSTER_ARN="$(resolve_output ecs_cluster_arn)"
  if [[ -n "$ECS_CLUSTER_ARN" ]]; then
    ECS_CLUSTER="${ECS_CLUSTER_ARN##*/}"
  fi
fi

if [[ "$DRY_RUN" == "1" ]]; then
  ECR_REPO_URI="${ECR_REPO_URI:-000000000000.dkr.ecr.${AWS_REGION}.amazonaws.com/kinnoo-${ENVIRONMENT}-server}"
  ECS_SERVICE="${ECS_SERVICE:-kinnoo-${ENVIRONMENT}-service}"
  ECS_CLUSTER="${ECS_CLUSTER:-kinnoo-${ENVIRONMENT}-cluster}"
fi

if [[ -z "$ECR_REPO_URI" ]]; then
  echo "[error] Could not resolve ECR repository (run a full apply against ${ENVIRONMENT} first)." >&2
  exit 1
fi
if [[ -z "$ECS_SERVICE" ]]; then
  echo "[error] Could not resolve ecs_service_name from terraform outputs." >&2
  exit 1
fi
if [[ -z "$ECS_CLUSTER" ]]; then
  echo "[error] Could not resolve ecs_cluster_arn/name from terraform outputs." >&2
  exit 1
fi

ECS_CONTAINER_NAME="${ECS_CONTAINER_NAME:-kinnoo-server}"

ensure_prod_cors_origins_present() {
  local service_task_definition_arn=""
  local env_cors=""
  local secret_cors=""

  service_task_definition_arn="$(aws ecs describe-services \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE" \
    --query 'services[0].taskDefinition' \
    --output text 2>/dev/null || true)"

  if [[ -z "$service_task_definition_arn" || "$service_task_definition_arn" == "None" ]]; then
    echo "[error] Could not resolve active task definition for ${ECS_CLUSTER}/${ECS_SERVICE}." >&2
    exit 1
  fi

  env_cors="$(aws ecs describe-task-definition \
    --task-definition "$service_task_definition_arn" \
    --query "taskDefinition.containerDefinitions[?name=='${ECS_CONTAINER_NAME}'].environment[] | [?name=='CORS_ORIGINS'].value | [0]" \
    --output text 2>/dev/null || true)"

  secret_cors="$(aws ecs describe-task-definition \
    --task-definition "$service_task_definition_arn" \
    --query "taskDefinition.containerDefinitions[?name=='${ECS_CONTAINER_NAME}'].secrets[] | [?name=='CORS_ORIGINS'].valueFrom | [0]" \
    --output text 2>/dev/null || true)"

  if [[ "$env_cors" == "None" ]]; then
    env_cors=""
  fi
  if [[ "$secret_cors" == "None" ]]; then
    secret_cors=""
  fi

  if [[ -z "$env_cors" && -z "$secret_cors" ]]; then
    echo "[error] Production guardrail: CORS_ORIGINS is missing for container '${ECS_CONTAINER_NAME}'" >&2
    echo "        on active task definition ${service_task_definition_arn}." >&2
    echo "        Set CORS_ORIGINS (environment or secret) before redeploying." >&2
    exit 1
  fi
}

ensure_registry_database_url_in_sync() {
  local sync_script="$ROOT_DIR/scripts/ops/sync-database-url.sh"
  if [[ ! -x "$sync_script" ]]; then
    echo "[error] Missing executable sync script: $sync_script" >&2
    exit 1
  fi

  if "$sync_script" "$ENVIRONMENT" --region "$AWS_REGION" --project "kinnoo" --dry-run --fail-on-mismatch >/dev/null; then
    echo "[ok] REGISTRY_DATABASE_URL credentials already match current RDS master secret"
    return 0
  fi

  echo "[warn] REGISTRY_DATABASE_URL credentials are out of sync; refreshing now..."
  "$sync_script" "$ENVIRONMENT" --region "$AWS_REGION" --project "kinnoo" >/dev/null

  if "$sync_script" "$ENVIRONMENT" --region "$AWS_REGION" --project "kinnoo" --dry-run --fail-on-mismatch >/dev/null; then
    echo "[ok] REGISTRY_DATABASE_URL credentials are now in sync"
    return 0
  fi

  echo "[error] REGISTRY_DATABASE_URL remains out of sync after refresh attempt" >&2
  exit 1
}

# Defensive guard: never push a prod image into a dev cluster or vice versa.
case "$ENVIRONMENT" in
  prod)
    if [[ "$ECS_CLUSTER" == *"-dev-"* || "$ECS_SERVICE" == *"-dev-"* || "$ECR_REPO_URI" == *"-dev-"* ]]; then
      echo "[error] Resolved targets look dev-scoped while ENVIRONMENT=prod" >&2
      echo "        cluster=$ECS_CLUSTER service=$ECS_SERVICE ecr=$ECR_REPO_URI" >&2
      exit 1
    fi ;;
  dev)
    if [[ "$ECS_CLUSTER" == *"-prod-"* || "$ECS_SERVICE" == *"-prod-"* || "$ECR_REPO_URI" == *"-prod-"* ]]; then
      echo "[error] Resolved targets look prod-scoped while ENVIRONMENT=dev" >&2
      echo "        cluster=$ECS_CLUSTER service=$ECS_SERVICE ecr=$ECR_REPO_URI" >&2
      exit 1
    fi ;;
esac

echo "[info] Environment: $ENVIRONMENT"
echo "[info] AWS region: $AWS_REGION"
echo "[info] ECR repo: $ECR_REPO_URI"
echo "[info] ECS cluster: $ECS_CLUSTER"
echo "[info] ECS service: $ECS_SERVICE"

echo "[info] Validating REGISTRY_DATABASE_URL secret is in sync with RDS master secret..."
if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] Would check/sync REGISTRY_DATABASE_URL against current RDS master secret"
else
  ensure_registry_database_url_in_sync
fi

if [[ "$ENVIRONMENT" == "prod" ]]; then
  echo "[info] Validating production CORS_ORIGINS configuration..."
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] Would verify active task definition contains CORS_ORIGINS for ${ECS_CONTAINER_NAME}" 
  else
    ensure_prod_cors_origins_present
  fi
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] Would build/push $ECR_REPO_URI:latest and force-redeploy $ECS_CLUSTER/$ECS_SERVICE"
  exit 0
fi

echo "Building server image..."
DOCKER_BUILDKIT=1 docker build --platform linux/amd64 -t "$ECR_REPO_URI:latest" "$ROOT_DIR"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPO_URI"

echo "Pushing server image..."
docker push "$ECR_REPO_URI:latest"

echo "Forcing ECS service deployment..."
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --force-new-deployment >/dev/null

echo "Done. ECS redeploy requested for $ECS_CLUSTER / $ECS_SERVICE."
