#!/usr/bin/env bash
#
# Build and push the security-check Lambda container image to the appropriate
# environment's ECR repository.
#
# Environment-aware (task523): pass --env dev|prod (or set ENVIRONMENT=...) to
# select which Terraform workspace/state to read the ECR repo URL from.
#
# Bootstrap path for first apply (chicken-and-egg):
#   1. terraform -chdir=iac apply -target=module.ecr -var-file=environments/${ENV}/terraform.tfvars
#      (creates the ECR repo without needing a real image URI).
#      If iac/variables.tf still rejects the placeholder image URI, set
#      lambda_security_check_image_uri to the placeholder URI from
#      iac/environments/${ENV}/terraform.tfvars first; the validation regex
#      accepts it without contacting ECR.
#   2. ENVIRONMENT=${ENV} scripts/ops/build_and_push_lambda_security_check_image.sh
#   3. Paste the printed image URI into iac/environments/${ENV}/terraform.tfvars
#      and run a full `terraform apply` for the stack.
#
# Usage:
#   scripts/ops/build_and_push_lambda_security_check_image.sh [--env dev|prod] [<image-tag>]
#   ENVIRONMENT=prod scripts/ops/build_and_push_lambda_security_check_image.sh v1
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IAC_DIR="$ROOT_DIR/iac"

ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-west-2}"
DRY_RUN="${DRY_RUN:-0}"

# Parse flags (positional image tag is preserved after flags).
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env|--environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --region)            AWS_REGION="${2:-}"; shift 2 ;;
    --dry-run)           DRY_RUN=1; shift ;;
    -h|--help)
      sed -n '1,30p' "$0" >&2
      exit 0 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]:-}"

IMAGE_TAG="${1:-$(date +%Y%m%d%H%M%S)}"

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "[error] --env must be 'dev' or 'prod' (got: ${ENVIRONMENT})" >&2
  exit 2
fi

if [[ ! -f "$ROOT_DIR/Dockerfile.lambda" ]]; then
  echo "Missing Dockerfile.lambda at repo root." >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/lambda_handler.py" ]]; then
  echo "Missing lambda_handler.py at repo root." >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  if [[ "$DRY_RUN" != "1" ]]; then
    echo "terraform is required but not found in PATH." >&2
    exit 1
  fi
fi

if ! command -v docker >/dev/null 2>&1; then
  if [[ "$DRY_RUN" != "1" ]]; then
    echo "docker is required but not found in PATH." >&2
    exit 1
  fi
fi

if [[ "$DRY_RUN" != "1" ]] && ! docker buildx version >/dev/null 2>&1; then
  echo "docker buildx is required but unavailable." >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  if [[ "$DRY_RUN" != "1" ]]; then
    echo "aws CLI is required but not found in PATH." >&2
    exit 1
  fi
fi

# Initialize against the requested environment's backend so terraform output
# returns the env's ECR repo URL. Use -reconfigure to switch backends safely.
BACKEND_HCL="$IAC_DIR/environments/${ENVIRONMENT}/backend.hcl"
TFVARS_FILE="$IAC_DIR/environments/${ENVIRONMENT}/terraform.tfvars"
if [[ ! -f "$BACKEND_HCL" ]]; then
  echo "[error] Missing backend file: $BACKEND_HCL" >&2
  exit 1
fi
if [[ ! -f "$TFVARS_FILE" ]]; then
  echo "[error] Missing tfvars file: $TFVARS_FILE" >&2
  exit 1
fi

echo "[info] Initializing terraform against ${ENVIRONMENT} backend..."
if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] terraform -chdir=$IAC_DIR init -reconfigure -backend-config=$BACKEND_HCL"
  LAMBDA_ECR_REPO_URI="000000000000.dkr.ecr.${AWS_REGION}.amazonaws.com/kinnoo-${ENVIRONMENT}-lambda-security-check"
else
  terraform -chdir="$IAC_DIR" init -reconfigure -backend-config="$BACKEND_HCL" >/dev/null
  LAMBDA_ECR_REPO_URI="$(terraform -chdir="$IAC_DIR" output -raw lambda_security_check_ecr_repository_url 2>/dev/null || true)"
fi

if [[ -z "$LAMBDA_ECR_REPO_URI" ]]; then
  echo "[error] Could not read lambda_security_check_ecr_repository_url from Terraform outputs." >&2
  echo "[error] Run a targeted apply first to create the ECR repo:" >&2
  echo "        terraform -chdir=$IAC_DIR apply -target=module.ecr -var-file=$TFVARS_FILE" >&2
  exit 1
fi

# Defensive check: prevent a dev terraform output from being pushed to under
# the prod env tag and vice versa.
case "$ENVIRONMENT" in
  prod)
    if [[ "$LAMBDA_ECR_REPO_URI" == *"-dev-"* ]]; then
      echo "[error] Resolved ECR repo URI looks dev-scoped while ENVIRONMENT=prod: $LAMBDA_ECR_REPO_URI" >&2
      exit 1
    fi ;;
  dev)
    if [[ "$LAMBDA_ECR_REPO_URI" == *"-prod-"* ]]; then
      echo "[error] Resolved ECR repo URI looks prod-scoped while ENVIRONMENT=dev: $LAMBDA_ECR_REPO_URI" >&2
      exit 1
    fi ;;
esac

LAMBDA_IMAGE_URI="$LAMBDA_ECR_REPO_URI:$IMAGE_TAG"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[dry-run] Would build/push: $LAMBDA_IMAGE_URI"
  echo "[dry-run] Would emit tfvars line for ${ENVIRONMENT}:"
  echo "[dry-run]   lambda_security_check_image_uri = \"$LAMBDA_IMAGE_URI\""
  exit 0
fi

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$LAMBDA_ECR_REPO_URI"

echo "Building and pushing Lambda image: $LAMBDA_IMAGE_URI"
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f "$ROOT_DIR/Dockerfile.lambda" \
  -t "$LAMBDA_IMAGE_URI" \
  --push \
  "$ROOT_DIR"

echo ""
echo "Pushed successfully. Set this in iac/environments/${ENVIRONMENT}/terraform.tfvars:"
echo "lambda_security_check_image_uri = \"$LAMBDA_IMAGE_URI\""
