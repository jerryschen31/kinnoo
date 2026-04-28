#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IAC_DIR="$ROOT_DIR/iac"
AWS_REGION="${AWS_REGION:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
IMAGE_TAG="${1:-$(date +%Y%m%d%H%M%S)}"
BACKEND_CONFIG_PATH="$IAC_DIR/environments/${ENVIRONMENT}/backend.hcl"

if [[ ! -f "$ROOT_DIR/Dockerfile.lambda" ]]; then
  echo "Missing Dockerfile.lambda at repo root." >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/lambda_handler.py" ]]; then
  echo "Missing lambda_handler.py at repo root." >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required but not found in PATH." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but not found in PATH." >&2
  exit 1
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "docker buildx is required but unavailable." >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required but not found in PATH." >&2
  exit 1
fi

if [[ ! -f "$BACKEND_CONFIG_PATH" ]]; then
  echo "Missing Terraform backend config for ENVIRONMENT=${ENVIRONMENT}: $BACKEND_CONFIG_PATH" >&2
  exit 1
fi

echo "Initializing Terraform backend for ENVIRONMENT=${ENVIRONMENT}..."
terraform -chdir="$IAC_DIR" init -reconfigure -backend-config="environments/${ENVIRONMENT}/backend.hcl" -no-color >/dev/null

TF_OUTPUT_RAW="$(terraform -chdir="$IAC_DIR" output -raw -no-color lambda_security_check_ecr_repository_url 2>&1 || true)"
LAMBDA_ECR_REPO_URI="$(printf '%s\n' "$TF_OUTPUT_RAW" | grep -Eo '[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[^[:space:]]+' | head -n 1 || true)"

if [[ -z "$LAMBDA_ECR_REPO_URI" ]]; then
  echo "Could not read lambda_security_check_ecr_repository_url from Terraform outputs." >&2
  echo "This usually means the selected backend state has no outputs yet." >&2
  echo "Backend config: $BACKEND_CONFIG_PATH" >&2
  if [[ -n "$TF_OUTPUT_RAW" ]]; then
    echo "terraform output response:" >&2
    echo "$TF_OUTPUT_RAW" >&2
  fi
  echo "Run Terraform apply in iac/ for ENVIRONMENT=${ENVIRONMENT}, then re-run this script." >&2
  exit 1
fi

LAMBDA_IMAGE_URI="$LAMBDA_ECR_REPO_URI:$IMAGE_TAG"
LAMBDA_IMAGE_URI_LATEST="$LAMBDA_ECR_REPO_URI:latest"
LAMBDA_ECR_REGISTRY_HOST="${LAMBDA_ECR_REPO_URI%%/*}"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$LAMBDA_ECR_REGISTRY_HOST"

echo "Building and pushing Lambda images:"
echo "  - $LAMBDA_IMAGE_URI"
echo "  - $LAMBDA_IMAGE_URI_LATEST"
docker buildx build \
  --platform linux/amd64 \
  --provenance=false \
  --sbom=false \
  -f "$ROOT_DIR/Dockerfile.lambda" \
  -t "$LAMBDA_IMAGE_URI" \
  -t "$LAMBDA_IMAGE_URI_LATEST" \
  --push \
  "$ROOT_DIR"

echo ""
echo "Pushed successfully. Set this in iac/environments/${ENVIRONMENT}/terraform.tfvars:"
echo "lambda_security_check_image_uri = \"$LAMBDA_IMAGE_URI\""
