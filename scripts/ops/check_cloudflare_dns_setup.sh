#!/usr/bin/env bash
set -euo pipefail

# Verifies feature106 live DNS setup in Cloudflare.
# Requires Cloudflare API token and zone ID.

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[error] Missing required environment variable: $name" >&2
    exit 2
  fi
}

require_env CLOUDFLARE_API_TOKEN
require_env CLOUDFLARE_ZONE_ID

CF_API="https://api.cloudflare.com/client/v4"
AUTH_HEADER="Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"

records_json="$(curl -fsSL \
  -H "$AUTH_HEADER" \
  "${CF_API}/zones/${CLOUDFLARE_ZONE_ID}/dns_records?per_page=500")"

python3 - <<'PY' "$records_json"
import json
import sys

payload = json.loads(sys.argv[1])
if not payload.get("success"):
    raise SystemExit("[error] Cloudflare API returned success=false")

records = payload.get("result", [])

by_name = {}
for record in records:
    by_name.setdefault(record.get("name", ""), []).append(record)

dev = by_name.get("dev.kinnoo.ai", [])
dev_api = by_name.get("dev-api.kinnoo.ai", [])

if not dev:
    raise SystemExit("[error] Missing DNS record for dev.kinnoo.ai")
if not dev_api:
    raise SystemExit("[error] Missing DNS record for dev-api.kinnoo.ai")

# Ensure expected dev records exist and are proxied.
if not any(r.get("type") == "CNAME" and bool(r.get("proxied")) for r in dev):
    raise SystemExit("[error] dev.kinnoo.ai must be a proxied CNAME")

if not any(
    r.get("type") == "CNAME"
    and bool(r.get("proxied"))
    and str(r.get("content", "")).endswith("elb.amazonaws.com")
    for r in dev_api
):
    raise SystemExit("[error] dev-api.kinnoo.ai must be proxied CNAME to ALB (elb.amazonaws.com)")

# ACM validation should exist as non-proxied CNAME to acm-validations.aws.
acm_candidates = [
    r for r in records
    if r.get("type") == "CNAME"
    and str(r.get("name", "")).endswith(".dev-api.kinnoo.ai")
    and str(r.get("content", "")).endswith("acm-validations.aws")
]

if not acm_candidates:
    raise SystemExit("[error] Missing ACM validation CNAME for dev-api.kinnoo.ai")

if any(bool(r.get("proxied")) for r in acm_candidates):
    raise SystemExit("[error] ACM validation CNAME must not be proxied")

print("[ok] Cloudflare DNS setup checks passed for dev/dev-api and ACM validation")
PY
