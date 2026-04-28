#!/usr/bin/env bash

# Refreshes /<project>/<environment>/REGISTRY_DATABASE_URL by reading the
# current RDS-managed master secret, URL-encoding credentials, and writing
# the JSON-keyed secret expected by ECS secret injection.
refresh_registry_database_url_secret() {
  set -euo pipefail

  local db_id="${1:-}"
  local db_instance_identifier=""
  local environment="${2:-dev}"
  local aws_region="${3:-us-west-2}"
  local project_name="${4:-kinnoo}"
  local db_name="${5:-kinnoo_registry}"

  if [[ -z "$db_id" ]]; then
    echo "Usage: refresh_registry_database_url_secret <db_instance_identifier> [environment] [aws_region] [project_name] [db_name]" >&2
    return 2
  fi

  if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI is required but not found in PATH." >&2
    return 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but not found in PATH." >&2
    return 1
  fi

  local target_secret="/${project_name}/${environment}/REGISTRY_DATABASE_URL"

  local master_secret_arn
  local master_json
  local host
  local port
  local db_url
  local payload
  local shape

  # Accept either DB instance identifier (e.g. kinnoo-prod-postgres)
  # or RDS resource id (e.g. db-ABCDEFG...).
  if AWS_PAGER='' aws rds describe-db-instances \
    --region "$aws_region" \
    --db-instance-identifier "$db_id" \
    --query 'DBInstances[0].DBInstanceIdentifier' \
    --output text >/dev/null 2>&1; then
    db_instance_identifier="$db_id"
  else
    db_instance_identifier="$(AWS_PAGER='' aws rds describe-db-instances \
      --region "$aws_region" \
      --query "DBInstances[?DbiResourceId=='${db_id}'].DBInstanceIdentifier | [0]" \
      --output text)"
  fi

  if [[ -z "$db_instance_identifier" || "$db_instance_identifier" == "None" ]]; then
    echo "Could not resolve DB instance identifier from input '$db_id'." >&2
    return 1
  fi

  master_secret_arn="$(AWS_PAGER='' aws rds describe-db-instances \
    --region "$aws_region" \
    --db-instance-identifier "$db_instance_identifier" \
    --query 'DBInstances[0].MasterUserSecret.SecretArn' \
    --output text)"

  if [[ -z "$master_secret_arn" || "$master_secret_arn" == "None" ]]; then
    echo "Could not resolve MasterUserSecret ARN for DB instance '$db_id'." >&2
    return 1
  fi

  master_json="$(AWS_PAGER='' aws secretsmanager get-secret-value \
    --region "$aws_region" \
    --secret-id "$master_secret_arn" \
    --query SecretString \
    --output text)"

  host="$(AWS_PAGER='' aws rds describe-db-instances \
    --region "$aws_region" \
    --db-instance-identifier "$db_instance_identifier" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)"

  port="$(AWS_PAGER='' aws rds describe-db-instances \
    --region "$aws_region" \
    --db-instance-identifier "$db_instance_identifier" \
    --query 'DBInstances[0].Endpoint.Port' \
    --output text)"

  db_url="$(python3 - <<'PY' "$master_json" "$host" "$port" "$db_name"
import json
import sys
from urllib.parse import quote

secret = json.loads(sys.argv[1])
host = sys.argv[2]
port = sys.argv[3]
db_name = sys.argv[4]
username = quote(str(secret["username"]), safe="")
password = quote(str(secret["password"]), safe="")
print(f"postgresql+psycopg://{username}:{password}@{host}:{port}/{db_name}")
PY
  )"

  payload="$(python3 - <<'PY' "$db_url"
import json
import sys

print(json.dumps({"REGISTRY_DATABASE_URL": sys.argv[1]}))
PY
  )"

  AWS_PAGER='' aws secretsmanager put-secret-value \
    --region "$aws_region" \
    --secret-id "$target_secret" \
    --secret-string "$payload" >/dev/null

  shape="$(python3 - <<'PY' "$db_url"
import sys

v = sys.argv[1]
scheme, rest = v.split('://', 1)
_userinfo, hostpath = rest.split('@', 1)
print(f"{scheme}://***:***@{hostpath}")
PY
  )"

  echo "Updated secret: $target_secret"
  echo "RDS instance: $db_instance_identifier"
  echo "Stored URL shape: $shape"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  refresh_registry_database_url_secret "$@"
fi