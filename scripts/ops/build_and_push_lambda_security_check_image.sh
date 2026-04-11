#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IAC_DIR="$ROOT_DIR/iac"
AWS_REGION="${AWS_REGION:-us-west-2}"
IMAGE_TAG="${1:-$(date +%Y%m%d%H%M%S)}"

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

LAMBDA_ECR_REPO_URI="$(terraform -chdir="$IAC_DIR" output -raw lambda_security_check_ecr_repository_url 2>/dev/null || true)"
if [[ -z "$LAMBDA_ECR_REPO_URI" ]]; then
  echo "Could not read lambda_security_check_ecr_repository_url from Terraform outputs." >&2
  echo "Run Terraform apply in iac/ first so the Lambda ECR repo exists." >&2
  exit 1
fi

LAMBDA_IMAGE_URI="$LAMBDA_ECR_REPO_URI:$IMAGE_TAG"

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
echo "Pushed successfully. Set this in iac/environments/dev/terraform.tfvars:"
echo "lambda_security_check_image_uri = \"$LAMBDA_IMAGE_URI\""
