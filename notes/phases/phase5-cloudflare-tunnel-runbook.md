# Phase 5 Cloudflare Tunnel Runbook (20 minutes)

This runbook gets you a public HTTPS URL for testing login and registry backend behavior without doing full AWS/S3 setup.

## What this validates

- Login form and session cookie behavior over real HTTPS
- Registry web pages (`/agents`, `/search`)
- Backend API auth and agent listing endpoints

## What this does NOT require

- AWS account
- S3 bucket
- ECS/Lambda/ALB

Use local storage for now. Add S3 later only when you need publish/download storage parity.

## Architecture for this runbook

Browser -> Cloudflare (HTTPS) -> Tunnel -> local FastAPI backend (`http://127.0.0.1:8000`)

This avoids frontend proxy/rewrite issues and directly validates backend auth + registry routes.

---

## 0) Prerequisites (2-3 min)

On macOS:

```bash
brew install cloudflared
cloudflared --version
python3 --version
```

From repo root:

```bash
cd /Users/jerry/gh/kinnoo
```

---

## 1) Create and activate Python env (2 min)

```bash
python3 -m venv .venv-phase5
source .venv-phase5/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r server/requirements.txt
```

---

## 2) Set exact backend env vars (1 min)

Use these exact names/values (change password/domain values to your own):

```bash
export REGISTRY_STORAGE_BACKEND=local
export REGISTRY_LOCAL_STORAGE_ROOT="$PWD/.registry-storage-phase5"

export REGISTRY_ADMIN_EMAIL="admin@example.com"
export REGISTRY_ADMIN_PASSWORD="ChangeMe-Phase5-123!"

export REGISTRY_TOKEN_SIGNING_SECRET="dev-token-secret-phase5"
export REGISTRY_SESSION_SIGNING_SECRET="dev-session-secret-phase5"
export REGISTRY_LOGIN_CSRF_SECRET="dev-login-csrf-secret-phase5"
```

---

## 3) Start backend locally (Terminal A, 1 min)

```bash
cd /Users/jerry/gh/kinnoo
source .venv-phase5/bin/activate
python -m uvicorn server.app:create_app --factory --host 127.0.0.1 --port 8000
```

Smoke check from another terminal:

```bash
curl -sS http://127.0.0.1:8000/health
```

Expected output:

```json
{"status":"ok"}
```

---

## 4) Create Cloudflare tunnel and DNS route (Terminal B, 6-8 min)

Pick a hostname under your zone, for example:

- `registry-dev.yourdomain.com`

Log in cloudflared to your Cloudflare account:

```bash
cloudflared tunnel login
```

Create named tunnel:

```bash
cloudflared tunnel create kinnoo-phase5
```

Get tunnel UUID:

```bash
TUNNEL_ID="$(cloudflared tunnel list | awk '/kinnoo-phase5/{print $1; exit}')"
echo "$TUNNEL_ID"
```

Create config file:

```bash
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: registry-dev.yourdomain.com
    service: http://127.0.0.1:8000
  - service: http_status:404
EOF
```

Create DNS route:

```bash
cloudflared tunnel route dns kinnoo-phase5 registry-dev.yourdomain.com
```

Run tunnel (keep this terminal open):

```bash
cloudflared tunnel --config ~/.cloudflared/config.yml run
```

---

## 5) Test login and registry pages over public HTTPS (3-4 min)

In browser:

1. Open `https://registry-dev.yourdomain.com/login`
2. Login with:
- username/email: `admin@example.com`
- password: `ChangeMe-Phase5-123!`
3. Verify redirect to:
- `https://registry-dev.yourdomain.com/agents`
4. Open search page:
- `https://registry-dev.yourdomain.com/search`

If login loops, open DevTools Network and confirm:

- POST `/login` returns `303`
- Response includes `Set-Cookie: kinnoo_session=...; Secure; HttpOnly`

---

## 6) Test backend APIs over tunnel (2-3 min)

Get token:

```bash
curl -sS -X POST "https://registry-dev.yourdomain.com/api/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"ChangeMe-Phase5-123!","tenant_slug":"global"}'
```

Health:

```bash
curl -sS "https://registry-dev.yourdomain.com/health"
```

Auth check without cookie (should be 401):

```bash
curl -i -sS "https://registry-dev.yourdomain.com/api/auth/me" | head -n 20
```

List agents with bearer token (paste token from auth response):

```bash
export TOKEN="PASTE_ACCESS_TOKEN_HERE"
curl -sS "https://registry-dev.yourdomain.com/api/agents" \
  -H "Authorization: Bearer ${TOKEN}"
```

---

## Optional: tunnel the Next.js frontend instead of backend

Only do this after backend-first checks pass.

1. Start backend locally on `127.0.0.1:8000` (same as above).
2. Start frontend locally:

```bash
cd /Users/jerry/gh/kinnoo
BACKEND_URL="http://127.0.0.1:8000" WEB_PORT=3002 ./scripts/start_frontend_phase5
```

3. In `~/.cloudflared/config.yml`, change ingress service to frontend:

```yaml
ingress:
  - hostname: registry-dev.yourdomain.com
    service: https://127.0.0.1:3002
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

4. Restart tunnel command:

```bash
cloudflared tunnel --config ~/.cloudflared/config.yml run
```

---

## Stop and cleanup

Stop tunnel: Ctrl+C in tunnel terminal.

Stop backend: Ctrl+C in uvicorn terminal.

Optional local cleanup:

```bash
rm -rf /Users/jerry/gh/kinnoo/.registry-storage-phase5
```

Delete tunnel later (optional):

```bash
cloudflared tunnel delete kinnoo-phase5
```

---

## Troubleshooting quick hits

- `ERR_CONNECTION_REFUSED` at public URL:
  - tunnel not running or backend not listening on `127.0.0.1:8000`
- Login returns to login page:
  - confirm POST `/login` is `303` and `Set-Cookie` is present
  - ensure you are using `https://` URL, not `http://`
- DNS not resolving:
  - rerun `cloudflared tunnel route dns ...` and wait 1-2 minutes
- 502 from Cloudflare:
  - local service URL in `config.yml` is wrong or local process is down
