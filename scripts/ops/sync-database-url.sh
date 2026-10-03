#!/usr/bin/env bash

# Sync /<project>/<environment>/REGISTRY_DATABASE_URL so its embedded
# username/password match the current RDS admin secret for that environment.
#
# Safety properties:
# - Does not echo credential values.
# - Does not pass credential values in command arguments.
# - Uses temporary files with restrictive permissions for transient processing.
# - Prints only redacted status and YES/NO verification flags.

set -euo pipefail
set +x

usage() {
  cat <<'EOF' >&2
Usage:
  sync-database-url.sh <environment> [--region <aws-region>] [--project <project-name>] [--db-instance <db-instance-id>] [--dry-run] [--fail-on-mismatch]

Arguments:
  <environment>          One of: dev, prod

Options:
  --region <aws-region>  AWS region (default: us-west-2)
  --project <name>       Project prefix for URL secret path (default: kinnoo)
  --db-instance <id>     Override DB instance identifier (default: <project>-<environment>-postgres)
  --dry-run              Validate and compare only; do not update secret
  --fail-on-mismatch     Exit non-zero when username/password do not match
  -h, --help             Show this help

Behavior:
  - Reads environment-specific RDS admin secret.
  - Reads /<project>/<environment>/REGISTRY_DATABASE_URL.
  - Rebuilds URL with updated username/password while preserving host/port/path/query.
  - Updates URL secret unless --dry-run is set.
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $1" >&2
    exit 1
  fi
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

environment="$1"
shift

aws_region="us-west-2"
project_name="kinnoo"
db_instance_identifier=""
dry_run=0
fail_on_mismatch=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      aws_region="${2:-}"
      shift 2
      ;;
    --project)
      project_name="${2:-}"
      shift 2
      ;;
    --db-instance)
      db_instance_identifier="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --fail-on-mismatch)
      fail_on_mismatch=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

case "$environment" in
  dev|prod)
    ;;
  *)
    echo "ERROR: environment must be one of: dev, prod" >&2
    exit 2
    ;;
esac

if [[ -z "$db_instance_identifier" ]]; then
  db_instance_identifier="${project_name}-${environment}-postgres"
fi

url_secret_id="/${project_name}/${environment}/REGISTRY_DATABASE_URL"

require_cmd aws
require_cmd python3

admin_secret_id="$(AWS_PAGER='' aws rds describe-db-instances \
  --region "$aws_region" \
  --db-instance-identifier "$db_instance_identifier" \
  --query 'DBInstances[0].MasterUserSecret.SecretArn' \
  --output text 2>/dev/null || true)"

if [[ -z "$admin_secret_id" || "$admin_secret_id" == "None" ]]; then
  echo "ERROR: could not resolve MasterUserSecret ARN for DB instance: $db_instance_identifier" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
chmod 700 "$TMP_DIR"
TMP_ADMIN="$TMP_DIR/admin.json"
TMP_URLRAW="$TMP_DIR/url.raw"
TMP_NEW="$TMP_DIR/new.secret"
TMP_VERIFY="$TMP_DIR/verify.raw"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Read source secrets into temp files without printing secret content.
AWS_PAGER='' aws secretsmanager get-secret-value \
  --region "$aws_region" \
  --secret-id "$admin_secret_id" \
  --query SecretString \
  --output text > "$TMP_ADMIN"

AWS_PAGER='' aws secretsmanager get-secret-value \
  --region "$aws_region" \
  --secret-id "$url_secret_id" \
  --query SecretString \
  --output text > "$TMP_URLRAW"

# Build the new URL secret by preserving URL structure and replacing credentials.
python3 - "$TMP_ADMIN" "$TMP_URLRAW" "$TMP_NEW" <<'PY'
import json
import sys
from urllib.parse import quote, urlsplit, urlunsplit

admin_path, urlraw_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

with open(admin_path, 'r', encoding='utf-8') as f:
    admin = json.load(f)

admin_user = admin.get('username')
admin_pass = admin.get('password')
if not admin_user or not admin_pass:
    raise SystemExit('ERROR: admin secret is missing username/password')

with open(urlraw_path, 'r', encoding='utf-8') as f:
    raw = f.read().strip()

wrapped = False
wrapper_obj = None
wrapper_key = None
url_candidate = None

try:
    parsed = json.loads(raw)
    if isinstance(parsed, str):
        wrapped = True
        url_candidate = parsed
    elif isinstance(parsed, dict):
        for key in (
            'REGISTRY_DATABASE_URL',
            'DATABASE_URL',
            'database_url',
            'url',
            'connection_url',
            'connectionString',
        ):
            value = parsed.get(key)
            if isinstance(value, str) and '://' in value:
                wrapped = True
                wrapper_obj = parsed
                wrapper_key = key
                url_candidate = value
                break
except Exception:
    pass

if not url_candidate:
    url_candidate = raw

parts = urlsplit(url_candidate)
if not parts.scheme or not parts.hostname:
    raise SystemExit('ERROR: URL secret value is not a parseable URL')

userinfo = f"{quote(str(admin_user), safe='')}:{quote(str(admin_pass), safe='')}"
host = parts.hostname
port = f":{parts.port}" if parts.port else ''
netloc = f"{userinfo}@{host}{port}"

new_url = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))

if wrapped:
    if wrapper_obj is None:
        payload = json.dumps(new_url)
    else:
        wrapper_obj[wrapper_key] = new_url
        payload = json.dumps(wrapper_obj, separators=(',', ':'))
else:
    payload = new_url

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(payload)
PY

if [[ "$dry_run" -eq 0 ]]; then
  AWS_PAGER='' aws secretsmanager update-secret \
    --region "$aws_region" \
    --secret-id "$url_secret_id" \
    --secret-string "file://$TMP_NEW" >/dev/null
fi

# Re-read URL secret and verify match with admin credentials without exposing values.
AWS_PAGER='' aws secretsmanager get-secret-value \
  --region "$aws_region" \
  --secret-id "$url_secret_id" \
  --query SecretString \
  --output text > "$TMP_VERIFY"

python3 - "$TMP_ADMIN" "$TMP_VERIFY" "$environment" "$url_secret_id" "$dry_run" "$fail_on_mismatch" <<'PY'
import json
import sys
from urllib.parse import urlsplit, unquote

admin_path, urlraw_path, env_name, url_secret_id, dry_run, fail_on_mismatch = sys.argv[1:7]

with open(admin_path, 'r', encoding='utf-8') as f:
    admin = json.load(f)

with open(urlraw_path, 'r', encoding='utf-8') as f:
    raw = f.read().strip()

url_candidate = None
try:
    parsed = json.loads(raw)
    if isinstance(parsed, str):
        url_candidate = parsed
    elif isinstance(parsed, dict):
        for key in (
            'REGISTRY_DATABASE_URL',
            'DATABASE_URL',
            'database_url',
            'url',
            'connection_url',
            'connectionString',
        ):
            value = parsed.get(key)
            if isinstance(value, str) and '://' in value:
                url_candidate = value
                break
except Exception:
    pass

if not url_candidate:
    url_candidate = raw

parts = urlsplit(url_candidate)
url_user = unquote(parts.username or '')
url_pass = unquote(parts.password or '')

password_match = (url_pass == str(admin.get('password', '')))
username_match = (url_user == str(admin.get('username', '')))
mode = 'DRY_RUN' if dry_run == '1' else 'UPDATED'

print(f'SYNC_ENV={env_name}')
print(f'SYNC_TARGET_SECRET={url_secret_id}')
print(f'SYNC_MODE={mode}')
print('SYNC_RESULT_PASSWORD_MATCH=' + ('YES' if password_match else 'NO'))
print('SYNC_RESULT_USERNAME_MATCH=' + ('YES' if username_match else 'NO'))

if fail_on_mismatch == '1' and (not password_match or not username_match):
  raise SystemExit(3)
PY
