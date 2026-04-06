#!/usr/bin/env bash
set -euo pipefail

# Adds required REGISTRY_* secrets to the ECS task definition used by a service,
# registers a new task definition revision, updates the service, and waits for stability.

PROFILE="jerry"
REGION="us-west-2"
CLUSTER="kinnoo-dev-cluster"
SERVICE="kinnoo-dev-service"
CONTAINER_NAME=""
KEEP_ARTIFACTS="false"
REGISTRY_LOCAL_STORAGE_ROOT="/data/.registry-storage"

usage() {
  cat <<'EOF'
Usage:
  scripts/add-registry-secrets.sh [options]

Options:
  --profile <name>         AWS CLI profile (default: jerry)
  --region <region>        AWS region (default: us-west-2)
  --cluster <name>         ECS cluster name (default: kinnoo-dev-cluster)
  --service <name>         ECS service name (default: kinnoo-dev-service)
  --container <name>       Container name in task definition (default: first container)
  --storage-root <path>    REGISTRY_LOCAL_STORAGE_ROOT value (default: /data/.registry-storage)
  --keep-artifacts         Keep generated td-current.json and td-new.json files
  -h, --help               Show help

Requirements:
  - aws CLI authenticated for the target account
  - jq installed
  - openssl available

What it does:
  1) Reads current service task definition ARN
  2) Generates 4 random REGISTRY_* secrets
  3) Clones task definition and injects/overwrites secret env vars
  4) Registers a new task definition revision
  5) Updates service to new revision and forces new deployment
  6) Waits for service to become stable
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --cluster)
      CLUSTER="$2"
      shift 2
      ;;
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --container)
      CONTAINER_NAME="$2"
      shift 2
      ;;
    --storage-root)
      REGISTRY_LOCAL_STORAGE_ROOT="$2"
      shift 2
      ;;
    --keep-artifacts)
      KEEP_ARTIFACTS="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd aws
require_cmd jq
require_cmd openssl

echo "[1/8] Fetching current task definition ARN for service ${SERVICE}..."
TD_ARN=$(aws --profile "$PROFILE" --region "$REGION" ecs describe-services \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)

if [[ -z "$TD_ARN" || "$TD_ARN" == "None" ]]; then
  echo "Could not resolve task definition ARN for ${SERVICE} in ${CLUSTER}" >&2
  exit 1
fi

echo "Current task definition: $TD_ARN"

if [[ -z "$CONTAINER_NAME" ]]; then
  echo "[2/8] Resolving container name from current task definition..."
  CONTAINER_NAME=$(aws --profile "$PROFILE" --region "$REGION" ecs describe-task-definition \
    --task-definition "$TD_ARN" \
    --query 'taskDefinition.containerDefinitions[0].name' --output text)
fi

if [[ -z "$CONTAINER_NAME" || "$CONTAINER_NAME" == "None" ]]; then
  echo "Could not resolve container name" >&2
  exit 1
fi

echo "Target container: $CONTAINER_NAME"

echo "[3/8] Generating random secret values..."
REGISTRY_TOKEN_SIGNING_SECRET=$(openssl rand -hex 64)
REGISTRY_SESSION_SIGNING_SECRET=$(openssl rand -hex 64)
REGISTRY_REGISTER_TOKEN_SECRET=$(openssl rand -hex 64)
REGISTRY_PASSWORD_RESET_TOKEN_SECRET=$(openssl rand -hex 64)

export REGISTRY_TOKEN_SIGNING_SECRET
export REGISTRY_SESSION_SIGNING_SECRET
export REGISTRY_REGISTER_TOKEN_SECRET
export REGISTRY_PASSWORD_RESET_TOKEN_SECRET
export CONTAINER_NAME
export REGISTRY_LOCAL_STORAGE_ROOT

echo "[4/8] Downloading current task definition JSON..."
aws --profile "$PROFILE" --region "$REGION" ecs describe-task-definition \
  --task-definition "$TD_ARN" \
  --query 'taskDefinition' --output json > td-current.json

echo "[5/8] Building new task definition payload with REGISTRY_* secrets..."
jq '
  del(
    .taskDefinitionArn,
    .revision,
    .status,
    .requiresAttributes,
    .compatibilities,
    .registeredAt,
    .registeredBy
  )
  | .containerDefinitions |= map(
      if .name == env.CONTAINER_NAME then
        .environment = (
          ((.environment // []) | map(select(
            .name != "REGISTRY_TOKEN_SIGNING_SECRET" and
            .name != "REGISTRY_SESSION_SIGNING_SECRET" and
            .name != "REGISTRY_REGISTER_TOKEN_SECRET" and
            .name != "REGISTRY_PASSWORD_RESET_TOKEN_SECRET" and
            .name != "REGISTRY_LOCAL_STORAGE_ROOT"
          )))
          + [
            {"name":"REGISTRY_TOKEN_SIGNING_SECRET","value":env.REGISTRY_TOKEN_SIGNING_SECRET},
            {"name":"REGISTRY_SESSION_SIGNING_SECRET","value":env.REGISTRY_SESSION_SIGNING_SECRET},
            {"name":"REGISTRY_REGISTER_TOKEN_SECRET","value":env.REGISTRY_REGISTER_TOKEN_SECRET},
            {"name":"REGISTRY_PASSWORD_RESET_TOKEN_SECRET","value":env.REGISTRY_PASSWORD_RESET_TOKEN_SECRET},
            {"name":"REGISTRY_LOCAL_STORAGE_ROOT","value":env.REGISTRY_LOCAL_STORAGE_ROOT}
          ]
        )
      else . end
    )
' td-current.json > td-new.json

echo "[6/8] Registering new task definition revision..."
NEW_TD_ARN=$(aws --profile "$PROFILE" --region "$REGION" ecs register-task-definition \
  --cli-input-json file://td-new.json \
  --query 'taskDefinition.taskDefinitionArn' --output text)

echo "New task definition: $NEW_TD_ARN"

echo "[7/8] Updating service and forcing new deployment..."
aws --profile "$PROFILE" --region "$REGION" ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --task-definition "$NEW_TD_ARN" \
  --force-new-deployment >/dev/null

echo "[8/8] Waiting for service stability..."
aws --profile "$PROFILE" --region "$REGION" ecs wait services-stable \
  --cluster "$CLUSTER" --services "$SERVICE"

echo "Deployment stabilized. Latest service summary:"
aws --profile "$PROFILE" --region "$REGION" ecs describe-services \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,taskDefinition:taskDefinition}' \
  --output table

if [[ "$KEEP_ARTIFACTS" != "true" ]]; then
  rm -f td-current.json td-new.json
fi

echo "Done."
