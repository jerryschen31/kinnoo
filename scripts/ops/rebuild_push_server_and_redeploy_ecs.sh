#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IAC_DIR="$ROOT_DIR/iac"

AWS_PROFILE="${AWS_PROFILE:-jerry}"
AWS_REGION="${AWS_REGION:-us-west-2}"

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required but not found in PATH." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but not found in PATH." >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required but not found in PATH." >&2
  exit 1
fi

if [[ ! -f "$ROOT_DIR/Dockerfile" ]]; then
  echo "Missing Dockerfile at repo root: $ROOT_DIR/Dockerfile" >&2
  exit 1
fi

export AWS_PROFILE
export AWS_REGION

echo "Resolving Terraform outputs..."
ECR_REPO_URI="$(terraform -chdir="$IAC_DIR" output -raw ecr_repo_uri 2>/dev/null || true)"
if [[ -z "$ECR_REPO_URI" ]]; then
  ECR_REPO_URI="$(terraform -chdir="$IAC_DIR" output -raw ecr_repository_url 2>/dev/null || true)"
fi
if [[ -z "$ECR_REPO_URI" ]]; then
  echo "Could not read ECR repository output (tried ecr_repo_uri and ecr_repository_url)." >&2
  exit 1
fi

ECS_SERVICE="kinnoo-dev-service"
# "$(terraform -chdir="$IAC_DIR" output -raw ecs_service_name 2>/dev/null || true)"
if [[ -z "$ECS_SERVICE" ]]; then
  echo "Could not read ecs_service_name from Terraform outputs." >&2
  exit 1
fi

ECS_CLUSTER="kinnoo-dev-cluster"
# "$(terraform -chdir="$IAC_DIR" output -raw ecs_cluster_name 2>/dev/null || true)"
if [[ -z "$ECS_CLUSTER" ]]; then
  ECS_CLUSTER_ARN="$(terraform -chdir="$IAC_DIR" output -raw ecs_cluster_arn 2>/dev/null || true)"
  if [[ -z "$ECS_CLUSTER_ARN" ]]; then
    echo "Could not read ECS cluster output (tried ecs_cluster_name and ecs_cluster_arn)." >&2
    exit 1
  fi
  ECS_CLUSTER="${ECS_CLUSTER_ARN##*/}"
fi

echo "Using AWS profile: $AWS_PROFILE"
echo "Using AWS region: $AWS_REGION"
echo "Using ECR repo: $ECR_REPO_URI"
echo "Using ECS cluster: $ECS_CLUSTER"
echo "Using ECS service: $ECS_SERVICE"

echo "Building server image..."
DOCKER_BUILDKIT=1 docker build -t "$ECR_REPO_URI:latest" "$ROOT_DIR"

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REPO_URI"

echo "Pushing server image..."
docker push "$ECR_REPO_URI:latest"

echo "Forcing ECS service deployment..."
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --force-new-deployment >/dev/null

echo "Done. ECS redeploy requested for $ECS_CLUSTER / $ECS_SERVICE."
