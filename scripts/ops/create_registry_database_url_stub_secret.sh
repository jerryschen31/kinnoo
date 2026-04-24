#!/usr/bin/env bash
#
# Idempotently create the /<project>/<environment>/REGISTRY_DATABASE_URL
# Secrets Manager secret with a clearly-marked placeholder value so the first
# `terraform apply` can succeed before RDS exists. After RDS is provisioned,
# `scripts/ops/refresh_registry_database_url_secret.sh` should be run to
# replace the placeholder with the real connection string.
#
# Behavior contract (task525):
#   1. If the secret does not exist, create it with the placeholder JSON.
#   2. If the secret exists with a placeholder value (contains the marker
#      string), leave it as-is and exit 0 (idempotent).
#   3. If the secret exists with a non-placeholder (real) value, refuse to
#      overwrite and exit 0.
#
# Usage:
#   scripts/ops/create_registry_database_url_stub_secret.sh \
#       --environment prod \
#       [--project-name kinnoo] \
#       [--region us-west-2]
#
# Or via env vars:
#   ENVIRONMENT=prod scripts/ops/create_registry_database_url_stub_secret.sh
#
set -euo pipefail

PLACEHOLDER_MARKER="REGISTRY_DATABASE_URL_STUB_PLACEHOLDER"
PLACEHOLDER_URL="postgresql+psycopg://${PLACEHOLDER_MARKER}:${PLACEHOLDER_MARKER}@${PLACEHOLDER_MARKER}/kinnoo_registry"

usage() {
  cat >&2 <<'USAGE'
Usage:
  create_registry_database_url_stub_secret.sh \
      --environment <env> [--project-name <name>] [--region <aws-region>]

Required:
  --environment | $ENVIRONMENT     Environment label (dev|prod|...).

Optional:
  --project-name | $PROJECT_NAME   Project prefix (default: kinnoo).
  --region | $AWS_REGION           AWS region (default: us-west-2).
  --dry-run                        Print actions without calling AWS.

Behavior:
  - Creates Secrets Manager secret '/<project>/<env>/REGISTRY_DATABASE_URL'
    with a placeholder JSON value if it does not already exist.
  - Idempotent: never overwrites an existing real value.
USAGE
}

ENVIRONMENT="${ENVIRONMENT:-}"
PROJECT_NAME="${PROJECT_NAME:-kinnoo}"
AWS_REGION="${AWS_REGION:-us-west-2}"
DRY_RUN="${DRY_RUN:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment)   ENVIRONMENT="${2:-}"; shift 2 ;;
    --project-name)  PROJECT_NAME="${2:-}"; shift 2 ;;
    --region)        AWS_REGION="${2:-}"; shift 2 ;;
    --dry-run)       DRY_RUN=1; shift ;;
    -h|--help)       usage; exit 0 ;;
    *) echo "[error] Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$ENVIRONMENT" ]]; then
  echo "[error] --environment (or \$ENVIRONMENT) is required" >&2
  usage
  exit 2
fi

SECRET_NAME="/${PROJECT_NAME}/${ENVIRONMENT}/REGISTRY_DATABASE_URL"
PAYLOAD="$(printf '{"REGISTRY_DATABASE_URL":"%s"}' "$PLACEHOLDER_URL")"

run_aws() {
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "[dry-run] aws $*" >&2
    return 0
  fi
  AWS_PAGER='' aws "$@"
}

if [[ "$DRY_RUN" != "1" ]] && ! command -v aws >/dev/null 2>&1; then
  echo "[error] aws CLI is required but not found in PATH." >&2
  exit 1
fi

echo "[info] Target secret: ${SECRET_NAME} (region=${AWS_REGION})"

existing="$(AWS_PAGER='' aws secretsmanager describe-secret \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_NAME" \
  --query ARN --output text 2>/dev/null || true)"

if [[ -z "$existing" || "$existing" == "None" ]]; then
  echo "[info] Secret does not exist; creating placeholder."
  run_aws secretsmanager create-secret \
    --region "$AWS_REGION" \
    --name "$SECRET_NAME" \
    --description "Stub created by create_registry_database_url_stub_secret.sh; replace via refresh_registry_database_url_secret.sh once RDS exists." \
    --secret-string "$PAYLOAD" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=bootstrap-script" \
    >/dev/null
  echo "[ok] Created stub secret ${SECRET_NAME}"
  exit 0
fi

current="$(AWS_PAGER='' aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_NAME" \
  --query SecretString --output text 2>/dev/null || true)"

if [[ -z "$current" ]]; then
  echo "[warn] Secret ${SECRET_NAME} exists but has no SecretString; writing placeholder."
  run_aws secretsmanager put-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$SECRET_NAME" \
    --secret-string "$PAYLOAD" >/dev/null
  echo "[ok] Wrote placeholder to ${SECRET_NAME}"
  exit 0
fi

if [[ "$current" == *"$PLACEHOLDER_MARKER"* ]]; then
  echo "[ok] Secret ${SECRET_NAME} already holds placeholder; no-op."
  exit 0
fi

echo "[ok] Secret ${SECRET_NAME} already holds a non-placeholder value; refusing to overwrite."
exit 0
