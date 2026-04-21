#!/usr/bin/env bash
# Load hosted-auth env vars for kinnoo login from AWS Secrets Manager.
#
# Usage (recommended, source into current shell):
#   source scripts/load_kinnoo_auth_env.sh [environment] [region] [project]
# Example:
#   source scripts/load_kinnoo_auth_env.sh dev us-west-2 kinnoo
#
# Alternate usage (without sourcing):
#   eval "$(scripts/load_kinnoo_auth_env.sh dev us-west-2 kinnoo)"

kinnoo_load_auth_env() {
  set -euo pipefail

  local environment="${1:-dev}"
  local aws_region="${2:-us-west-2}"
  local project_name="${3:-kinnoo}"

  if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI is required but not found in PATH." >&2
    return 1
  fi

  _extract_secret_value() {
    local raw_value="$1"
    shift
    python3 - <<'PY' "$raw_value" "$@"
import json
import sys

raw = sys.argv[1]
keys = sys.argv[2:]

try:
    parsed = json.loads(raw)
except Exception:
    parsed = None

if isinstance(parsed, dict):
    for key in keys:
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            print(value.strip())
            raise SystemExit(0)
    raise SystemExit(1)

if isinstance(raw, str) and raw.strip():
    print(raw.strip())
    raise SystemExit(0)

raise SystemExit(1)
PY
  }

  _fetch_secret_first() {
    local raw_value=""
    local extract_keys="$1"
    shift
    local secret_name=""
    for secret_name in "$@"; do
      raw_value="$(AWS_PAGER='' aws secretsmanager get-secret-value \
        --region "$aws_region" \
        --secret-id "$secret_name" \
        --query SecretString \
        --output text 2>/dev/null || true)"
      if [[ -n "${raw_value// }" ]]; then
        local parsed_value=""
        if parsed_value="$(_extract_secret_value "$raw_value" $extract_keys 2>/dev/null)"; then
          printf '%s' "$parsed_value"
          return 0
        fi
      fi
    done
    return 1
  }

  local audience
  local cli_client_id
  local authorization_endpoint
  local token_endpoint

  audience="$(_fetch_secret_first "KINDE_AUDIENCE AUTH_AUDIENCE" \
    "${project_name}/${environment}/KINDE_AUDIENCE" \
    "${project_name}/${environment}/AUTH_AUDIENCE")" || {
      echo "Could not resolve audience secret for ${project_name}/${environment}." >&2
      return 1
    }

  cli_client_id="$(_fetch_secret_first "KINDE_CLI_CLIENT_ID AUTH_CLI_CLIENT_ID" \
    "${project_name}/${environment}/KINDE_CLI_CLIENT_ID" \
    "${project_name}/${environment}/AUTH_CLI_CLIENT_ID")" || {
      echo "Could not resolve CLI client ID secret for ${project_name}/${environment}." >&2
      return 1
    }

  authorization_endpoint="$(_fetch_secret_first "AUTHORIZATION_ENDPOINT AUTH_AUTHORIZATION_ENDPOINT" \
    "${project_name}/${environment}/AUTHORIZATION_ENDPOINT" \
    "${project_name}/${environment}/AUTH_AUTHORIZATION_ENDPOINT")" || {
      echo "Could not resolve authorization endpoint secret for ${project_name}/${environment}." >&2
      return 1
    }

  token_endpoint="$(_fetch_secret_first "TOKEN_ENDPOINT AUTH_TOKEN_ENDPOINT" \
    "${project_name}/${environment}/TOKEN_ENDPOINT" \
    "${project_name}/${environment}/AUTH_TOKEN_ENDPOINT")" || {
      echo "Could not resolve token endpoint secret for ${project_name}/${environment}." >&2
      return 1
    }

  export AUTH_AUDIENCE="$audience"
  export KINDE_AUDIENCE="$audience"
  export AUTH_CLI_CLIENT_ID="$cli_client_id"
  export KINDE_CLI_CLIENT_ID="$cli_client_id"
  export AUTH_AUTHORIZATION_ENDPOINT="$authorization_endpoint"
  export AUTHORIZATION_ENDPOINT="$authorization_endpoint"
  export AUTH_TOKEN_ENDPOINT="$token_endpoint"
  export TOKEN_ENDPOINT="$token_endpoint"

  echo "Loaded hosted auth env for ${project_name}/${environment} in ${aws_region}."
  echo "AUTH_AUDIENCE=$AUTH_AUDIENCE"
  echo "AUTH_CLI_CLIENT_ID=$AUTH_CLI_CLIENT_ID"
  echo "AUTH_AUTHORIZATION_ENDPOINT=$AUTH_AUTHORIZATION_ENDPOINT"
  echo "AUTH_TOKEN_ENDPOINT=$AUTH_TOKEN_ENDPOINT"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  # Executed directly: emit export lines for eval usage.
  set -euo pipefail

  environment="${1:-dev}"
  aws_region="${2:-us-west-2}"
  project_name="${3:-kinnoo}"

  if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI is required but not found in PATH." >&2
    exit 1
  fi

  extract_secret_value() {
    local raw_value="$1"
    shift
    python3 - <<'PY' "$raw_value" "$@"
import json
import sys

raw = sys.argv[1]
keys = sys.argv[2:]

try:
    parsed = json.loads(raw)
except Exception:
    parsed = None

if isinstance(parsed, dict):
    for key in keys:
        value = parsed.get(key)
        if isinstance(value, str) and value.strip():
            print(value.strip())
            raise SystemExit(0)
    raise SystemExit(1)

if isinstance(raw, str) and raw.strip():
    print(raw.strip())
    raise SystemExit(0)

raise SystemExit(1)
PY
  }

  fetch_secret_first() {
    local raw_value=""
    local extract_keys="$1"
    shift
    local secret_name=""
    for secret_name in "$@"; do
      raw_value="$(AWS_PAGER='' aws secretsmanager get-secret-value \
        --region "$aws_region" \
        --secret-id "$secret_name" \
        --query SecretString \
        --output text 2>/dev/null || true)"
      if [[ -n "${raw_value// }" ]]; then
        local parsed_value=""
        if parsed_value="$(extract_secret_value "$raw_value" $extract_keys 2>/dev/null)"; then
          printf '%s' "$parsed_value"
          return 0
        fi
      fi
    done
    return 1
  }

  audience="$(fetch_secret_first "KINDE_AUDIENCE AUTH_AUDIENCE" \
    "${project_name}/${environment}/KINDE_AUDIENCE" \
    "${project_name}/${environment}/AUTH_AUDIENCE")"
  cli_client_id="$(fetch_secret_first "KINDE_CLI_CLIENT_ID AUTH_CLI_CLIENT_ID" \
    "${project_name}/${environment}/KINDE_CLI_CLIENT_ID" \
    "${project_name}/${environment}/AUTH_CLI_CLIENT_ID")"
  authorization_endpoint="$(fetch_secret_first "AUTHORIZATION_ENDPOINT AUTH_AUTHORIZATION_ENDPOINT" \
    "${project_name}/${environment}/AUTHORIZATION_ENDPOINT" \
    "${project_name}/${environment}/AUTH_AUTHORIZATION_ENDPOINT")"
  token_endpoint="$(fetch_secret_first "TOKEN_ENDPOINT AUTH_TOKEN_ENDPOINT" \
    "${project_name}/${environment}/TOKEN_ENDPOINT" \
    "${project_name}/${environment}/AUTH_TOKEN_ENDPOINT")"

  cat <<EOF
export AUTH_AUDIENCE='${audience}'
export KINDE_AUDIENCE='${audience}'
export AUTH_CLI_CLIENT_ID='${cli_client_id}'
export KINDE_CLI_CLIENT_ID='${cli_client_id}'
export AUTH_AUTHORIZATION_ENDPOINT='${authorization_endpoint}'
export AUTHORIZATION_ENDPOINT='${authorization_endpoint}'
export AUTH_TOKEN_ENDPOINT='${token_endpoint}'
export TOKEN_ENDPOINT='${token_endpoint}'
EOF
fi
