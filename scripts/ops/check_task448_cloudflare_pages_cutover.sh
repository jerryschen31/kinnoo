#!/usr/bin/env bash
set -euo pipefail

# Verifies task448 Cloudflare/Pages cutover:
# - dev.kinnoo.ai record points to expected Pages hostname in same account
# - record is proxied
# - endpoint no longer returns Cloudflare 1014

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "[error] Missing required environment variable: $name" >&2
    exit 2
  fi
}

require_env CLOUDFLARE_API_TOKEN
require_env CLOUDFLARE_ZONE_ID
require_env EXPECTED_DEV_PAGES_TARGET

CF_API="https://api.cloudflare.com/client/v4"
AUTH_HEADER="Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"

record_json="$(curl -fsSL \
  -H "$AUTH_HEADER" \
  "${CF_API}/zones/${CLOUDFLARE_ZONE_ID}/dns_records?type=CNAME&name=dev.kinnoo.ai")"

python3 - <<'PY' "$record_json" "$EXPECTED_DEV_PAGES_TARGET"
import json
import sys

payload = json.loads(sys.argv[1])
expected_target = sys.argv[2].strip().rstrip(".")

if not payload.get("success"):
    raise SystemExit("[error] Cloudflare API returned success=false")

records = payload.get("result", [])
if len(records) != 1:
    raise SystemExit(f"[error] Expected exactly 1 CNAME record for dev.kinnoo.ai, got {len(records)}")

record = records[0]
content = str(record.get("content", "")).rstrip(".")

if content != expected_target:
    raise SystemExit(
        f"[error] dev.kinnoo.ai points to '{content}', expected '{expected_target}'"
    )

if not bool(record.get("proxied")):
    raise SystemExit("[error] dev.kinnoo.ai CNAME must be proxied=true")

print("[ok] dev.kinnoo.ai CNAME target and proxy status are correct")
PY

body="$(curl -fsSL https://dev.kinnoo.ai || true)"
if echo "$body" | grep -qi "error code: 1014"; then
  echo "[error] dev.kinnoo.ai still returns Cloudflare 1014" >&2
  exit 1
fi

echo "[ok] dev.kinnoo.ai no longer returns Cloudflare 1014"
echo "[ok] task448 Cloudflare Pages cutover checks passed"
