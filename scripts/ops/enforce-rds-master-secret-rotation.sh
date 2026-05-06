#!/usr/bin/env bash

# Enforce rotation state for an RDS-managed master user secret.
# Intended for Terraform local-exec usage so dev/prod tfvars can toggle
# rotation behavior consistently.

set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  enforce-rds-master-secret-rotation.sh \
    --secret-id <secret-id-or-arn> \
    --enabled <true|false> \
    [--days <n>] \
    [--region <aws-region>] \
    [--db-instance-identifier <id>] \
    [--environment <env>] \
    [--project <name>] \
    [--sync-registry-database-url <true|false>]

Examples:
  enforce-rds-master-secret-rotation.sh \
    --secret-id arn:aws:secretsmanager:...:secret:rds!db-... \
    --enabled false \
    --region us-west-2

  enforce-rds-master-secret-rotation.sh \
    --secret-id rds!db-... \
    --enabled true \
    --days 7 \
    --region us-west-2 \
    --db-instance-identifier kinnoo-prod-postgres \
    --environment prod \
    --project kinnoo \
    --sync-registry-database-url true
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[error] Required command not found: $1" >&2
    exit 1
  fi
}

SECRET_ID=""
ENABLED=""
DAYS="7"
AWS_REGION="us-west-2"
DB_INSTANCE_IDENTIFIER=""
ENVIRONMENT=""
PROJECT_NAME="kinnoo"
SYNC_REGISTRY_DATABASE_URL="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --secret-id) SECRET_ID="${2:-}"; shift 2 ;;
    --enabled) ENABLED="${2:-}"; shift 2 ;;
    --days) DAYS="${2:-}"; shift 2 ;;
    --region) AWS_REGION="${2:-}"; shift 2 ;;
    --db-instance-identifier) DB_INSTANCE_IDENTIFIER="${2:-}"; shift 2 ;;
    --environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --project) PROJECT_NAME="${2:-}"; shift 2 ;;
    --sync-registry-database-url) SYNC_REGISTRY_DATABASE_URL="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[error] Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$SECRET_ID" ]]; then
  echo "[error] --secret-id is required" >&2
  usage
  exit 2
fi

if [[ "$ENABLED" != "true" && "$ENABLED" != "false" ]]; then
  echo "[error] --enabled must be true or false" >&2
  usage
  exit 2
fi

if ! [[ "$DAYS" =~ ^[0-9]+$ ]] || [[ "$DAYS" -lt 1 ]]; then
  echo "[error] --days must be an integer >= 1" >&2
  exit 2
fi

if [[ "$SYNC_REGISTRY_DATABASE_URL" != "true" && "$SYNC_REGISTRY_DATABASE_URL" != "false" ]]; then
  echo "[error] --sync-registry-database-url must be true or false" >&2
  exit 2
fi

require_cmd aws

current_enabled_raw="$(AWS_PAGER='' aws secretsmanager describe-secret \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ID" \
  --query 'RotationEnabled' \
  --output text)"

current_days_raw="$(AWS_PAGER='' aws secretsmanager describe-secret \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ID" \
  --query 'RotationRules.AutomaticallyAfterDays' \
  --output text)"

current_enabled="false"
if [[ "$current_enabled_raw" == "True" || "$current_enabled_raw" == "true" ]]; then
  current_enabled="true"
fi

current_days="0"
if [[ -n "$current_days_raw" && "$current_days_raw" != "None" ]]; then
  current_days="$current_days_raw"
fi

if [[ "$ENABLED" == "false" ]]; then
  if [[ "$current_enabled" == "true" ]]; then
    echo "[info] Disabling rotation for secret: $SECRET_ID"
    AWS_PAGER='' aws secretsmanager cancel-rotate-secret \
      --region "$AWS_REGION" \
      --secret-id "$SECRET_ID" >/dev/null
    echo "[ok] Rotation disabled"
  else
    echo "[ok] Rotation already disabled"
  fi
else
  if [[ "$current_enabled" != "true" || "$current_days" != "$DAYS" ]]; then
    echo "[info] Enabling/updating rotation for secret: $SECRET_ID (days=$DAYS)"
    AWS_PAGER='' aws secretsmanager rotate-secret \
      --region "$AWS_REGION" \
      --secret-id "$SECRET_ID" \
      --rotation-rules "AutomaticallyAfterDays=$DAYS" >/dev/null
    echo "[ok] Rotation enabled/updated"
  else
    echo "[ok] Rotation already enabled with AutomaticallyAfterDays=$DAYS"
  fi
fi

if [[ "$SYNC_REGISTRY_DATABASE_URL" == "true" ]]; then
  if [[ -z "$DB_INSTANCE_IDENTIFIER" || -z "$ENVIRONMENT" ]]; then
    echo "[error] --db-instance-identifier and --environment are required when sync is enabled" >&2
    exit 2
  fi

  refresh_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/refresh_registry_database_url_secret.sh"
  if [[ ! -x "$refresh_script" ]]; then
    echo "[error] Missing executable sync helper: $refresh_script" >&2
    exit 1
  fi

  echo "[info] Refreshing /${PROJECT_NAME}/${ENVIRONMENT}/REGISTRY_DATABASE_URL from current RDS master secret"
  "$refresh_script" "$DB_INSTANCE_IDENTIFIER" "$ENVIRONMENT" "$AWS_REGION" "$PROJECT_NAME"
fi
