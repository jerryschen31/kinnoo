#!/usr/bin/env bash
set -euo pipefail

# Add a user to the kinnoo dev auth store using the existing server CLI.
# Supports local mode and ECS execute-command mode.

usage() {
  cat <<'EOF'
Usage:
  scripts/add-dev-user.sh --email <email> [--role user|admin] [--mode local|ecs] [options]

Required:
  --email <email>           User email to create

Optional:
  --role <role>             user (default) or admin
  --mode <mode>             local (default) or ecs
  --password <value>        Set deterministic password after user creation (avoid in shell history)
  --password-env <name>     Read password from environment variable <name>

Local mode options:
  --store-root <path>       Auth store root (default: .registry-storage/auth)
  --python-bin <path>       Python executable (default: python3)

ECS mode options:
  --region <aws-region>     AWS region (default: us-west-2)
  --cluster <name>          ECS cluster name (default: kinnoo-dev-cluster)
  --service <name>          ECS service name (default: kinnoo-dev-service)
  --container <name>        ECS container name (default: kinnoo-server)
  --ecs-store-root <path>   Auth store root in ECS container (default: /data/.registry-storage/auth)

Examples:
  scripts/add-dev-user.sh --email newuser@example.com
  scripts/add-dev-user.sh --email admin@example.com --role admin
  scripts/add-dev-user.sh --email user@example.com --password-env KINNOOTEAM_USER_PASSWORD
  scripts/add-dev-user.sh --email dev@example.com --mode ecs --region us-west-2
EOF
}

EMAIL=""
ROLE="user"
MODE="local"
STORE_ROOT=".registry-storage/auth"
PYTHON_BIN="python3"
AWS_REGION="us-west-2"
ECS_CLUSTER="kinnoo-dev-cluster"
ECS_SERVICE="kinnoo-dev-service"
ECS_CONTAINER="kinnoo-server"
ECS_STORE_ROOT="/data/.registry-storage/auth"
PASSWORD_VALUE=""
PASSWORD_ENV_VAR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --email)
      EMAIL="${2:-}"
      shift 2
      ;;
    --role)
      ROLE="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --store-root)
      STORE_ROOT="${2:-}"
      shift 2
      ;;
    --python-bin)
      PYTHON_BIN="${2:-}"
      shift 2
      ;;
    --region)
      AWS_REGION="${2:-}"
      shift 2
      ;;
    --cluster)
      ECS_CLUSTER="${2:-}"
      shift 2
      ;;
    --service)
      ECS_SERVICE="${2:-}"
      shift 2
      ;;
    --container)
      ECS_CONTAINER="${2:-}"
      shift 2
      ;;
    --ecs-store-root)
      ECS_STORE_ROOT="${2:-}"
      shift 2
      ;;
    --password)
      PASSWORD_VALUE="${2:-}"
      shift 2
      ;;
    --password-env)
      PASSWORD_ENV_VAR="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$EMAIL" ]]; then
  echo "Error: --email is required" >&2
  usage
  exit 2
fi

if ! [[ "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
  echo "Error: --email must be a valid email address" >&2
  exit 2
fi

if [[ "$ROLE" != "user" && "$ROLE" != "admin" ]]; then
  echo "Error: --role must be one of: user, admin" >&2
  exit 2
fi

if [[ -n "$PASSWORD_VALUE" && -n "$PASSWORD_ENV_VAR" ]]; then
  echo "Error: use either --password or --password-env, not both" >&2
  exit 2
fi

resolve_password() {
  if [[ -n "$PASSWORD_ENV_VAR" ]]; then
    if [[ -z "${!PASSWORD_ENV_VAR:-}" ]]; then
      echo "Error: environment variable '$PASSWORD_ENV_VAR' is not set or empty" >&2
      exit 2
    fi
    printf '%s' "${!PASSWORD_ENV_VAR}"
    return
  fi
  printf '%s' "$PASSWORD_VALUE"
}

if [[ "$MODE" == "local" ]]; then
  echo "[info] Creating user locally using server CLI"
  echo "[info] store-root: $STORE_ROOT"
  "$PYTHON_BIN" server/cli.py user create \
    --store-root "$STORE_ROOT" \
    --email "$EMAIL" \
    --role "$ROLE"

  resolved_password="$(resolve_password)"
  if [[ -n "$resolved_password" ]]; then
    echo "[info] Setting deterministic password from provided source"
    KINNOO_PASSWORD_SET_STORE_ROOT="$STORE_ROOT" \
    KINNOO_PASSWORD_SET_EMAIL="$EMAIL" \
    KINNOO_PASSWORD_SET_VALUE="$resolved_password" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import os

from server.storage.user_store import UserStore

store = UserStore(Path(os.environ["KINNOO_PASSWORD_SET_STORE_ROOT"]))
store.reset_password(
    email=os.environ["KINNOO_PASSWORD_SET_EMAIL"],
    new_password=os.environ["KINNOO_PASSWORD_SET_VALUE"],
)
store.unlock_user(email=os.environ["KINNOO_PASSWORD_SET_EMAIL"])
print("[info] Password updated and account unlocked.")
PY
  fi
  exit 0
fi

if [[ "$MODE" == "ecs" ]]; then
  echo "[info] Creating user in ECS task via execute-command"
  task_arn="$(aws ecs list-tasks \
    --region "$AWS_REGION" \
    --cluster "$ECS_CLUSTER" \
    --service-name "$ECS_SERVICE" \
    --desired-status RUNNING \
    --query 'taskArns[0]' \
    --output text)"

  if [[ -z "$task_arn" || "$task_arn" == "None" ]]; then
    echo "Error: no running task found for service $ECS_SERVICE in cluster $ECS_CLUSTER" >&2
    exit 1
  fi

  aws ecs execute-command \
    --region "$AWS_REGION" \
    --cluster "$ECS_CLUSTER" \
    --task "$task_arn" \
    --container "$ECS_CONTAINER" \
    --interactive \
    --command "sh -lc 'PYTHONPATH=/app python /app/server/cli.py user create --store-root \"$ECS_STORE_ROOT\" --email \"$EMAIL\" --role \"$ROLE\"'"

  resolved_password="$(resolve_password)"
  if [[ -n "$resolved_password" ]]; then
    echo "[info] Setting deterministic password inside ECS task from provided source"
    aws ecs execute-command \
      --region "$AWS_REGION" \
      --cluster "$ECS_CLUSTER" \
      --task "$task_arn" \
      --container "$ECS_CONTAINER" \
      --interactive \
      --command "sh -lc 'PYTHONPATH=/app KINNOO_PASSWORD_SET_STORE_ROOT=\"$ECS_STORE_ROOT\" KINNOO_PASSWORD_SET_EMAIL=\"$EMAIL\" KINNOO_PASSWORD_SET_VALUE=\"$resolved_password\" python - <<\"PY\"\nfrom pathlib import Path\nimport os\nfrom server.storage.user_store import UserStore\nstore = UserStore(Path(os.environ[\"KINNOO_PASSWORD_SET_STORE_ROOT\"]))\nstore.reset_password(email=os.environ[\"KINNOO_PASSWORD_SET_EMAIL\"], new_password=os.environ[\"KINNOO_PASSWORD_SET_VALUE\"])\nstore.unlock_user(email=os.environ[\"KINNOO_PASSWORD_SET_EMAIL\"])\nprint(\"[info] Password updated and account unlocked.\")\nPY'"
  fi
  exit 0
fi

echo "Error: --mode must be one of: local, ecs" >&2
exit 2
