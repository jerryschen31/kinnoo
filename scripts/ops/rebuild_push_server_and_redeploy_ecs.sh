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
