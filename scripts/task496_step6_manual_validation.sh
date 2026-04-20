#!/usr/bin/env bash
set -euo pipefail

# Task496 Step6 manual post-deploy validation helper.
# It automates safe HTTP checks and records guided manual checks into a report.

FRONTEND_URL="https://dev.kinnoo.ai"
BACKEND_URL="https://dev-api.kinnoo.ai"
TOKEN="${KINNOO_TEST_BEARER_TOKEN:-}"
VERIFIED_BY="${USER:-unknown}"
REPORT_PATH=""

usage() {
  cat <<'EOF'
Usage: scripts/task496_step6_manual_validation.sh [options]

Options:
  --frontend-url URL    Frontend URL (default: https://dev.kinnoo.ai)
  --backend-url URL     Backend URL (default: https://dev-api.kinnoo.ai)
  --token TOKEN         Bearer token for authenticated /api/auth/me check (optional)
  --verified-by NAME    Name recorded in report (default: $USER)
  --report PATH         Output report path (default: outputs/task496-step6-<timestamp>.md)
  --help                Show this help

Env shortcuts:
  KINNOO_TEST_BEARER_TOKEN
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --frontend-url)
      FRONTEND_URL="$2"
      shift 2
      ;;
    --backend-url)
      BACKEND_URL="$2"
      shift 2
      ;;
    --token)
      TOKEN="$2"
      shift 2
      ;;
    --verified-by)
      VERIFIED_BY="$2"
      shift 2
      ;;
    --report)
      REPORT_PATH="$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$REPORT_PATH" ]]; then
  ts="$(date +%Y%m%d-%H%M%S)"
  REPORT_PATH="outputs/task496-step6-${ts}.md"
fi

mkdir -p "$(dirname "$REPORT_PATH")"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required but not installed." >&2
  exit 1
fi

# Results arrays (simple line-based storage)
AUTOMATED_RESULTS=()
MANUAL_RESULTS=()
FAIL_COUNT=0

record_auto() {
  local status="$1"
  local label="$2"
  local details="$3"
  AUTOMATED_RESULTS+=("- [${status}] ${label} - ${details}")
  if [[ "$status" == "FAIL" ]]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

record_manual() {
  local status="$1"
  local label="$2"
  local details="$3"
  MANUAL_RESULTS+=("- [${status}] ${label} - ${details}")
  if [[ "$status" == "FAIL" ]]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

http_code() {
  local url="$1"
  shift
  curl -sS -o /dev/null -w "%{http_code}" "$@" "$url"
}

ask_yes_no() {
  local prompt="$1"
  local answer
  local normalized
  while true; do
    read -r -p "$prompt [y/n]: " answer
    normalized="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]')"
    case "$normalized" in
      y|yes) return 0 ;;
      n|no) return 1 ;;
      *) echo "Please answer y or n." ;;
    esac
  done
}

note_input() {
  local prompt="$1"
  local value
  read -r -p "$prompt: " value
  printf "%s" "$value"
}

echo "Running Task496 Step6 validation helper..."
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"

# 1) Automated routing and health checks
login_code="$(http_code "${FRONTEND_URL}/login")"
if [[ "$login_code" =~ ^(200|301|302|303|307|308)$ ]]; then
  record_auto "PASS" "Frontend /login reachable" "HTTP ${login_code}"
else
  record_auto "FAIL" "Frontend /login reachable" "HTTP ${login_code}"
fi

health_code="$(http_code "${BACKEND_URL}/health")"
if [[ "$health_code" == "200" ]]; then
  record_auto "PASS" "Backend /health" "HTTP 200"
else
  record_auto "FAIL" "Backend /health" "HTTP ${health_code}"
fi

ready_code="$(http_code "${BACKEND_URL}/ready")"
if [[ "$ready_code" == "200" ]]; then
  record_auto "PASS" "Backend /ready" "HTTP 200"
else
  record_auto "FAIL" "Backend /ready" "HTTP ${ready_code}"
fi

# 2) Unauthenticated auth-path behavior
backend_me_unauth_code="$(http_code "${BACKEND_URL}/api/auth/me")"
if [[ "$backend_me_unauth_code" =~ ^(401|403)$ ]]; then
  record_auto "PASS" "Backend unauth /api/auth/me rejection" "HTTP ${backend_me_unauth_code}"
else
  record_auto "FAIL" "Backend unauth /api/auth/me rejection" "HTTP ${backend_me_unauth_code}"
fi

frontend_me_unauth_code="$(http_code "${FRONTEND_URL}/api/auth/me")"
if [[ "$frontend_me_unauth_code" =~ ^(401|403)$ ]]; then
  record_auto "PASS" "Frontend proxy unauth /api/auth/me rejection" "HTTP ${frontend_me_unauth_code}"
else
  record_auto "FAIL" "Frontend proxy unauth /api/auth/me rejection" "HTTP ${frontend_me_unauth_code}"
fi

# 3) Optional authenticated path verification
if [[ -n "$TOKEN" ]]; then
  backend_me_auth_code="$(http_code "${BACKEND_URL}/api/auth/me" -H "Authorization: Bearer ${TOKEN}")"
  if [[ "$backend_me_auth_code" == "200" ]]; then
    record_auto "PASS" "Backend auth /api/auth/me" "HTTP 200 with bearer token"
  else
    record_auto "FAIL" "Backend auth /api/auth/me" "HTTP ${backend_me_auth_code} with bearer token"
  fi

  frontend_me_auth_code="$(http_code "${FRONTEND_URL}/api/auth/me" -H "Authorization: Bearer ${TOKEN}")"
  if [[ "$frontend_me_auth_code" == "200" ]]; then
    record_auto "PASS" "Frontend proxy auth /api/auth/me" "HTTP 200 with bearer token"
  else
    record_auto "FAIL" "Frontend proxy auth /api/auth/me" "HTTP ${frontend_me_auth_code} with bearer token"
  fi
else
  record_auto "INFO" "Authenticated /api/auth/me checks" "Skipped (no --token or KINNOO_TEST_BEARER_TOKEN provided)"
fi

# 4) Guided manual checks

echo
echo "Manual check 1: Web login/logout/callback smoke"
echo "- Open ${FRONTEND_URL}/login"
echo "- Complete login and confirm callback success"
echo "- Log out and verify return to login"
if ask_yes_no "Did web login/logout/callback smoke pass"; then
  details="$(note_input "Optional evidence note (URL, screenshot path, timestamp)")"
  record_manual "PASS" "Web login/logout/callback smoke" "${details:-Completed}"
else
  details="$(note_input "Failure detail")"
  record_manual "FAIL" "Web login/logout/callback smoke" "${details:-Failed}"
fi

echo
echo "Manual check 2: CLI login loopback callback smoke"
echo "- Run: python3 src/kinnoo/cli.py login"
echo "- Confirm browser opens and callback returns to CLI successfully"
if ask_yes_no "Did CLI login loopback smoke pass"; then
  details="$(note_input "Optional evidence note (terminal output file, timestamp)")"
  record_manual "PASS" "CLI login loopback callback smoke" "${details:-Completed}"
else
  details="$(note_input "Failure detail")"
  record_manual "FAIL" "CLI login loopback callback smoke" "${details:-Failed}"
fi

echo
echo "Manual check 3: Runtime behavior validation"
echo "- Confirm deployed runtime validates issuer/audience/signature path"
echo "- Confirm invalid token path is rejected clearly"
if ask_yes_no "Did runtime behavior validation pass"; then
  details="$(note_input "Optional evidence note")"
  record_manual "PASS" "Runtime behavior validation (issuer/audience/signature)" "${details:-Completed}"
else
  details="$(note_input "Failure detail")"
  record_manual "FAIL" "Runtime behavior validation (issuer/audience/signature)" "${details:-Failed}"
fi

# Write report
{
  echo "# Task496 Step6 Manual Post-Deploy Validation Report"
  echo
  echo "- Date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo "- Verified by: ${VERIFIED_BY}"
  echo "- Frontend URL: ${FRONTEND_URL}"
  echo "- Backend URL: ${BACKEND_URL}"
  echo
  echo "## Automated Checks"
  for line in "${AUTOMATED_RESULTS[@]}"; do
    echo "$line"
  done
  echo
  echo "## Manual Checks"
  for line in "${MANUAL_RESULTS[@]}"; do
    echo "$line"
  done
  echo
  echo "## Summary"
  if [[ $FAIL_COUNT -eq 0 ]]; then
    echo "- Overall: PASS"
  else
    echo "- Overall: FAIL"
  fi
  echo "- Failure count: ${FAIL_COUNT}"
} >"$REPORT_PATH"

echo
echo "Report written to: $REPORT_PATH"
if [[ $FAIL_COUNT -eq 0 ]]; then
  echo "Task496 Step6 validation status: PASS"
  exit 0
fi

echo "Task496 Step6 validation status: FAIL (${FAIL_COUNT} failing checks)" >&2
exit 1
