#!/usr/bin/env bash
#
# Verify Cloudflare DNS setup for the configured environment.
# Environment-aware (task519): defaults to dev for backwards compatibility, but
# can be pointed at prod by setting --env prod or BASE_DOMAIN/FRONTEND_SUBDOMAIN/API_SUBDOMAIN.
#
# Usage:
#   scripts/ops/check_cloudflare_dns_setup.sh [--env dev|prod]
#   FRONTEND_SUBDOMAIN=www API_SUBDOMAIN=api scripts/ops/check_cloudflare_dns_setup.sh
#
# Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID
#
set -euo pipefail

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[error] Missing required environment variable: $name" >&2
    exit 2
  fi
}

ENVIRONMENT="${ENVIRONMENT:-dev}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env|--environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    -h|--help)
      sed -n '1,15p' "$0" >&2
      exit 0 ;;
    *) echo "[error] Unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Per-env defaults; explicit env vars always win so the script also works for
# any custom subdomain layout.
case "$ENVIRONMENT" in
  prod)
    FRONTEND_SUBDOMAIN="${FRONTEND_SUBDOMAIN:-www}"
    API_SUBDOMAIN="${API_SUBDOMAIN:-api}" ;;
  dev|*)
    FRONTEND_SUBDOMAIN="${FRONTEND_SUBDOMAIN:-dev}"
    API_SUBDOMAIN="${API_SUBDOMAIN:-dev-api}" ;;
esac
BASE_DOMAIN="${BASE_DOMAIN:-kinnoo.ai}"

require_env CLOUDFLARE_API_TOKEN
require_env CLOUDFLARE_ZONE_ID

FRONTEND_FQDN="${FRONTEND_SUBDOMAIN}.${BASE_DOMAIN}"
API_FQDN="${API_SUBDOMAIN}.${BASE_DOMAIN}"

CF_API="https://api.cloudflare.com/client/v4"
AUTH_HEADER="Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"

records_json="$(curl -fsSL \
  -H "$AUTH_HEADER" \
  "${CF_API}/zones/${CLOUDFLARE_ZONE_ID}/dns_records?per_page=500")"

python3 - "$records_json" "$FRONTEND_FQDN" "$API_FQDN" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
frontend_fqdn = sys.argv[2]
api_fqdn = sys.argv[3]

if not payload.get("success"):
    raise SystemExit("[error] Cloudflare API returned success=false")

records = payload.get("result", [])

by_name = {}
for record in records:
    by_name.setdefault(record.get("name", ""), []).append(record)

frontend = by_name.get(frontend_fqdn, [])
api = by_name.get(api_fqdn, [])

if not frontend:
    raise SystemExit(f"[error] Missing DNS record for {frontend_fqdn}")
if not api:
    raise SystemExit(f"[error] Missing DNS record for {api_fqdn}")

# Frontend must be a proxied CNAME (or apex AAAA — accept either since prod
# may use AAAA for an apex Worker custom domain setup).
if not any(
    bool(r.get("proxied")) and r.get("type") in {"CNAME", "AAAA", "A"}
    for r in frontend
):
    raise SystemExit(f"[error] {frontend_fqdn} must be a proxied CNAME/AAAA/A")

if not any(
    r.get("type") == "CNAME"
    and bool(r.get("proxied"))
    and str(r.get("content", "")).endswith("elb.amazonaws.com")
    for r in api
):
    raise SystemExit(f"[error] {api_fqdn} must be proxied CNAME to ALB (elb.amazonaws.com)")

# ACM validation should exist as non-proxied CNAME to acm-validations.aws,
# scoped under the API subdomain.
acm_candidates = [
    r for r in records
    if r.get("type") == "CNAME"
    and str(r.get("name", "")).endswith(f".{api_fqdn}")
    and str(r.get("content", "")).endswith("acm-validations.aws")
]

if not acm_candidates:
    raise SystemExit(f"[error] Missing ACM validation CNAME for {api_fqdn}")

if any(bool(r.get("proxied")) for r in acm_candidates):
    raise SystemExit("[error] ACM validation CNAME must not be proxied")

print(f"[ok] Cloudflare DNS setup checks passed for {frontend_fqdn}, {api_fqdn}, and ACM validation")
PY

# Live API health check (best-effort): if curl can reach the API_FQDN and
# /health responds 200, log success. Non-2xx exits non-zero so the script
# fails the smoke gate.
if command -v curl >/dev/null 2>&1; then
  echo "[info] GET https://${API_FQDN}/health"
  http_status="$(curl -k -fsS -o /dev/null -w '%{http_code}' "https://${API_FQDN}/health" || true)"
  if [[ "$http_status" != "200" ]]; then
    echo "[error] https://${API_FQDN}/health returned HTTP ${http_status:-unknown}" >&2
    exit 1
  fi
  echo "[ok] https://${API_FQDN}/health returned 200"
fi
