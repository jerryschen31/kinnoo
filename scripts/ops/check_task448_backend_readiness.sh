#!/usr/bin/env bash
set -euo pipefail

# Verifies task448 backend readiness actions completed:
# - Secrets have AWSCURRENT values
# - ECR has at least one image
# - ECS service has running tasks
# - ALB target group has healthy targets

AWS_PROFILE="${AWS_PROFILE:-jerry}"
AWS_REGION="${AWS_REGION:-us-west-2}"
CLUSTER_NAME="${CLUSTER_NAME:-kinnoo-dev-cluster}"
SERVICE_NAME="${SERVICE_NAME:-kinnoo-dev-service}"
REPO_NAME="${REPO_NAME:-kinnoo-dev-server}"
TARGET_GROUP_NAME="${TARGET_GROUP_NAME:-kinnoo-dev-tg}"

required_secrets=(
  "kinnoo/dev/jwt-secret"
  "kinnoo/dev/session-secret"
  "kinnoo/dev/admin-password"
)

for secret_id in "${required_secrets[@]}"; do
  stages="$(aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
    secretsmanager list-secret-version-ids \
    --secret-id "$secret_id" \
    --query 'Versions[].VersionStages[]' \
    --output text)"

  if [[ "$stages" != *"AWSCURRENT"* ]]; then
    echo "[error] Secret has no AWSCURRENT value: $secret_id" >&2
    exit 1
  fi
  echo "[ok] Secret has AWSCURRENT: $secret_id"
done

image_count="$(aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  ecr describe-images \
  --repository-name "$REPO_NAME" \
  --query 'length(imageDetails)' \
  --output text)"

if [[ "$image_count" == "None" || "$image_count" -lt 1 ]]; then
  echo "[error] ECR repository has no images: $REPO_NAME" >&2
  exit 1
fi

echo "[ok] ECR image count: $image_count"

running_count="$(aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  ecs describe-services \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME" \
  --query 'services[0].runningCount' \
  --output text)"

if [[ "$running_count" == "None" || "$running_count" -lt 1 ]]; then
  echo "[error] ECS service has no running tasks: ${CLUSTER_NAME}/${SERVICE_NAME}" >&2
  exit 1
fi

echo "[ok] ECS running tasks: $running_count"

target_group_arn="$(aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  elbv2 describe-target-groups \
  --names "$TARGET_GROUP_NAME" \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)"

if [[ -z "$target_group_arn" || "$target_group_arn" == "None" ]]; then
  echo "[error] Could not resolve target group ARN for $TARGET_GROUP_NAME" >&2
  exit 1
fi

healthy_count="$(aws --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  elbv2 describe-target-health \
  --target-group-arn "$target_group_arn" \
  --query 'length(TargetHealthDescriptions[?TargetHealth.State==`healthy`])' \
  --output text)"

if [[ "$healthy_count" == "None" || "$healthy_count" -lt 1 ]]; then
  echo "[error] No healthy targets registered in $TARGET_GROUP_NAME" >&2
  exit 1
fi

echo "[ok] Healthy target count: $healthy_count"
echo "[ok] task448 backend readiness checks passed"
