# Phase 5 Cloudflare Tunnel Runbook (20 minutes)

Use this to test the Phase 5 NextJS login/dashboard over a public HTTPS URL without AWS/S3.

## Goal

Get this working end-to-end:

- NextJS login page at /login
- NextJS registry dashboard at /registry
- Backend API calls proxied through NextJS to local FastAPI backend

## You do NOT need yet

- AWS account
- S3 buckets
- ECS/Lambda/ALB

## Important distinction

- Tunnel to backend port 8000: you will see legacy FastAPI pages (/login, /agents, /search)
- Tunnel to frontend port 3002: you will see Phase 5 NextJS pages (/login, /registry)

---

## Architecture used here

Browser -> Cloudflare (HTTPS) -> cloudflared tunnel -> local NextJS frontend (https://127.0.0.1:3002) -> local FastAPI backend (http://127.0.0.1:8000)

---

## 0) Prerequisites (2-3 min)

```bash
brew install cloudflared
cloudflared --version
python3 --version
node --version
npm --version
```

From repo root:

```bash
cd /Users/jerry/gh/kinnoo
```

---

## 1) Python environment and backend deps (2 min)

```bash
python3 -m venv .venv-phase5
source .venv-phase5/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -r server/requirements.txt
```

---

## 2) Set backend env vars (1 min)

```bash
export REGISTRY_STORAGE_BACKEND=local
export REGISTRY_LOCAL_STORAGE_ROOT="$PWD/.registry-storage-phase5"

export REGISTRY_ADMIN_EMAIL="<your-admin-email>"
export REGISTRY_ADMIN_PASSWORD="<set-a-strong-admin-password>"

export REGISTRY_TOKEN_SIGNING_SECRET="dev-token-secret-phase5"
export REGISTRY_SESSION_SIGNING_SECRET="dev-session-secret-phase5"
export REGISTRY_LOGIN_CSRF_SECRET="dev-login-csrf-secret-phase5"
```

---

## 3) Start local backend (Terminal A, 1 min)

```bash
cd /Users/jerry/gh/kinnoo
source .venv-phase5/bin/activate
python -m uvicorn server.app:create_app --factory --host 127.0.0.1 --port 8000
```

Health check from another terminal:

```bash
curl -sS http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

---

## 4) Start local NextJS frontend (Terminal B, 1 min)

Use HTTP backend URL because backend is local HTTP in this runbook.

```bash
cd /Users/jerry/gh/kinnoo
BACKEND_URL="http://127.0.0.1:8000" WEB_HOST=127.0.0.1 WEB_PORT=3002 ./scripts/start_frontend_phase5
```

Confirm local frontend is up:

```bash
curl -k -I https://127.0.0.1:3002/login
```

Confirm the process is listening on the exact tunnel target:

```bash
lsof -nP -iTCP:3002 -sTCP:LISTEN
```

Expected output should show 127.0.0.1:3002 or *:3002.

---

## 5) Create tunnel and DNS route (Terminal C, 6-8 min)

Use your Cloudflare hostname, example:

- registry-dev.kinnoo.ai

Login (if needed):

```bash
cloudflared tunnel login
```

Create tunnel:

```bash
cloudflared tunnel create kinnoo-phase5
```

Find tunnel ID:

```bash
TUNNEL_ID="$(cloudflared tunnel list | awk '/kinnoo-phase5/{print $1; exit}')"
echo "$TUNNEL_ID"
```

Create config:

```bash
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${HOME}/.cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: registry-dev.kinnoo.ai
    service: https://127.0.0.1:3002
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF
```

Create DNS route:

```bash
cloudflared tunnel route dns kinnoo-phase5 registry-dev.kinnoo.ai
```

Run tunnel:

```bash
cloudflared tunnel --config ~/.cloudflared/config.yml run
```

---

## 6) Validate Phase 5 UI over public HTTPS (3-4 min)

Open these in browser:

1. https://registry-dev.kinnoo.ai/login (must be NextJS login page)
2. Log in with:
- username/email: value from REGISTRY_ADMIN_EMAIL
- password: value from REGISTRY_ADMIN_PASSWORD
3. Verify redirect to:
- https://registry-dev.kinnoo.ai/registry (Phase 5 dashboard)

If you see legacy pages (/agents, /search), your tunnel is still targeting backend port 8000.

---

## 7) API spot checks through frontend domain (2-3 min)

Token endpoint through Next proxy:

```bash
curl -sS -X POST "https://registry-dev.kinnoo.ai/api/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username":"'"${REGISTRY_ADMIN_EMAIL}"'","password":"'"${REGISTRY_ADMIN_PASSWORD}"'","tenant_slug":"global"}'
```

Auth check without session cookie (expect 401):

```bash
curl -i -sS "https://registry-dev.kinnoo.ai/api/auth/me" | head -n 20
```

---

## Stop

- Terminal C (tunnel): Ctrl+C
- Terminal B (frontend): Ctrl+C
- Terminal A (backend): Ctrl+C

Optional cleanup:

```bash
rm -rf /Users/jerry/gh/kinnoo/.registry-storage-phase5
```

---

## Troubleshooting

- Legacy page at /login:
  - Tunnel ingress is pointing to backend http://127.0.0.1:8000
  - It must point to frontend https://127.0.0.1:3002 with noTLSVerify true
- Login loops in NextJS UI:
  - Start frontend with BACKEND_URL=http://127.0.0.1:8000
  - Ensure /api/login and /api/logout rewrites are ordered before /api/:path*
- 502 from Cloudflare:
  - Frontend or backend process is down
  - Wrong local service URL in ~/.cloudflared/config.yml
  - Host binding mismatch: cloudflared targets 127.0.0.1:3002, but Next is bound to localhost/::1 only
    - Start frontend with WEB_HOST=127.0.0.1
    - Or change tunnel service to https://localhost:3002
