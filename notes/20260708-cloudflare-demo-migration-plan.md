# Kinnoo Demo Hosting Migration Plan — AWS → Cloudflare-centric

**Date:** 2026-07-08
**Goal:** Run a low-cost "always demo-able" kinnoo registry after tearing down the AWS prod stack. All CLI commands (`login`, `publish`, `search`, `install`, `run`) and the web registry must work. Use Cloudflare for storage (and, where sensible, "DB") plus a single backend API server.

---

## TL;DR / Recommendation

Kinnoo's server already has **pluggable storage** (`local` | `s3`) and **pluggable metadata** (`json` | `postgres`). This is the whole game:

- **Storage → Cloudflare R2** via the existing `s3` adapter. R2 is S3-compatible and `S3StorageBackend` already accepts a custom `endpoint_url` + keys. **Zero code changes — env vars only.**
- **"Database" → delete it.** Use the `json` metadata backend, which stores all registry metadata as JSON objects *in the storage backend* (i.e. in R2). This fully replaces RDS Postgres. **Zero code changes — one env var.**
- **Compute → one small always-on server** running the existing Docker image, exposed at `api.kinnoo.ai` through a **Cloudflare Tunnel**. No inbound ports, no load balancer, no NAT gateway.
- **Auth → unchanged.** Kinde OIDC stays as-is (you kept the tenant). Auth state (SQLite + files) lives on the compute host's local disk.
- **Frontend → already on Cloudflare Pages** (`kinnoo.pages.dev` → `www.kinnoo.ai`). Free, unaffected.

**Estimated cost: $0–5/month** (R2 free tier covers a demo; Tunnel is free; compute is either your Mac at $0 or a tiny host at ~$0–5), vs. the ~$60–100/mo AWS stack.

The one real decision is **where the single server runs** (see "Compute options"). Everything else is settled by the code we already have.

---

## Why this is mostly config, not a rewrite

Findings from the server code:

| Concern | Code location | What it means for us |
|---|---|---|
| Storage is an interface | `server/storage/base.py` (`StorageBackend` Protocol) | Swappable without touching business logic. |
| S3 adapter already supports custom endpoints | `server/storage/s3.py` — takes `endpoint_url`, `access_key_id`, `secret_access_key` | **R2 is a drop-in.** R2 exposes an S3 API at `https://<account_id>.r2.cloudflarestorage.com`. |
| Storage backend chosen by env | `server/config.py` → `REGISTRY_STORAGE_BACKEND`, `REGISTRY_S3_*` | Flip to `s3` + point at R2. |
| `json` metadata backend writes metadata into storage | `server/metadata/manager.py` (keys like `metadata/global/index.v1.json`) | With R2 storage, **metadata lives in R2 → no database needed.** |
| Metadata backend chosen by env | `server/config.py` → `REGISTRY_METADATA_BACKEND` (`json`\|`postgres`) | Set `json`. Postgres was only for concurrent-write/search scale — irrelevant for a demo. |
| Auth persistence is local disk, **not** Postgres | `server/app.py`: `UserStore`, `SessionService`, `SQLiteAuthStore` all under `local_storage_root/auth` | RDS was never the auth store. Compute just needs a small persistent (or re-bootstrappable) disk. |
| Download flow | `server/routes/download.py` | Returns an R2 presigned URL for `s3` backends; also has a streaming `/archive` fallback. Both work with R2 (see gotcha). |
| Packaging | `Dockerfile` (uvicorn factory on :8000, healthcheck `/health`) | Runs anywhere Docker runs. |

**Net code change to migrate off AWS storage + DB: none.** It's environment variables plus a bucket.

---

## Target architecture

```
  kinnoo CLI ────────────────┐
                             │  HTTPS (api.kinnoo.ai)
  Browser ── www.kinnoo.ai ──┤
   (Cloudflare Pages, free)  │
                             ▼
              Cloudflare edge  ──►  Cloudflare Tunnel (cloudflared, free)
                                        │  outbound-only, no open ports
                                        ▼
                          Single server: kinnoo Docker image (uvicorn :8000)
                          - metadata backend = json
                          - storage backend  = s3 → Cloudflare R2
                          - auth state        = local disk (SQLite + files)
                                        │
                        S3 API (SigV4)  ▼
                          Cloudflare R2 bucket  kinnoo-registry-demo
                          - agent archives (.kno)
                          - metadata/*.json  (the "database")
                                        ▲
                          Kinde OIDC (external) ─ token validation
```

RDS, ALB, ECS Fargate, NAT gateway, S3, ECR, the security-check Lambda: **all gone** (already torn down). Kept from AWS: nothing runtime-critical (optionally the last DB snapshot + Secrets Manager, which you chose to keep at ~$7/mo — not used by this design; you can migrate those secret values to `.env`/Cloudflare and drop them later).

---

## Compute options (the only real decision)

The Python FastAPI app **cannot run on Cloudflare Workers** — it uses boto3, FastAPI/uvicorn, SQLite, and the local filesystem, none of which fit the Workers Python runtime. So "single server" has to be an actual server. Three viable homes:

### Option 1 — Cloudflare Tunnel → container on your Mac (or any machine you already have) ✅ recommended for interview demos
- Run `docker run` (or docker-compose) of the kinnoo image locally; run `cloudflared` pointed at `http://localhost:8000`, mapped to hostname `api.kinnoo.ai`.
- **Cost: $0.** Tunnel is free; R2 within free tier.
- **Code changes: none.** Auth state persists on your local disk naturally.
- **Trade-off:** the origin must be running during the demo. For a *scheduled* interview, you start it 5 minutes beforehand. Not suitable for 24/7 public uptime.

### Option 2 — Tiny always-on host + R2 + Cloudflare DNS/Tunnel
- A small always-on box (Fly.io with a persistent volume, Render, or a $4–6/mo VPS) runs the same image; Tunnel or a proxied DNS record fronts it.
- **Cost: ~$0–5/mo.** **Code changes: none.** Persistent disk keeps auth state across restarts.
- **Trade-off:** slightly more setup than Option 1; best if you want the registry reachable 24/7 without your laptop.

### Option 3 — Cloudflare Containers (native compute) ⚠️ not recommended for now
- Runs the Docker image natively on Cloudflare. Attractive because it's "all Cloudflare."
- **Blockers today:** (a) **ephemeral disk** — container disk resets on stop/sleep, which would wipe the SQLite auth store and session files; making this work requires moving auth state into R2/D1 (**a code change**). (b) Still **beta**, no SLA, cold starts, scale-to-zero after `sleepAfter`. (c) Per-use cost > free Tunnel.
- **Verdict:** revisit only if kinnoo later moves auth state off local disk. Note it as the "fully Cloudflare-native" future target.

**Recommendation:** Option 1 for interview-day demos (zero cost, zero changes, you control when it's up). Graduate to Option 2 if you want it always-on. Keep Option 3 on the roadmap.

---

## On using a Cloudflare "DB" (D1)

You mentioned Cloudflare DB. Be aware:
- **D1 is not a drop-in.** The app's only SQL backend is Postgres (`postgres` metadata backend), and D1 is SQLite-over-HTTP, not Postgres-wire-compatible. Using D1 would require writing a new metadata backend (and/or porting the auth store). That's real work for no demo benefit.
- **Hyperdrive** only accelerates connections to an *existing* Postgres/MySQL — it doesn't replace RDS; you'd still pay for a Postgres somewhere.
- **The cheapest, already-supported "database" is no database:** the `json` backend on R2. Metadata reads/writes become R2 object GET/PUT. Perfectly adequate at demo scale.

If you *later* want server-native SQL search/concurrency again, the clean path is a small D1-backed metadata backend implementing `MetadataManagerProtocol` (`server/metadata/types.py`). Out of scope here.

---

## Cost comparison

| Item | AWS (prod, before teardown) | Cloudflare demo design |
|---|---|---|
| Compute | ECS Fargate 0.5 vCPU/1GB + ALB + NAT GW | Tunnel → Mac ($0) or tiny host (~$0–5) |
| Database | RDS Postgres single-AZ (~$15–30) | **None** (json backend on R2) → $0 |
| Object storage | S3 + requests | R2 (10 GB, 1M Class A, 10M Class B free) → $0 |
| Edge / TLS / DNS | ALB + ACM | Cloudflare edge + Tunnel → $0 |
| Frontend | Cloudflare Pages | unchanged, $0 |
| **Total** | **~$60–100/mo** | **~$0–5/mo** |

R2 paid rates if you ever exceed free tier: $0.015/GB-mo storage, $4.50/M Class A ops, $0.36/M Class B ops, **egress free**. A demo will not approach these.

---

## Implementation steps

### Phase 0 — Prerequisites
- [ ] Cloudflare account with the `kinnoo.ai` zone already present (it is — used by Pages today).
- [ ] `wrangler` and/or Cloudflare dashboard access; `cloudflared` installed on the compute host.
- [ ] Docker on the compute host. Confirm the kinnoo image builds: `docker build -t kinnoo-server .`
- [ ] Have Kinde OIDC values handy (from `~/kinnoo-backups/prod-secrets.json` you exported during teardown).

### Phase 1 — Create the R2 bucket
- [ ] Create bucket, e.g. `kinnoo-registry-demo` (dashboard → R2, or `wrangler r2 bucket create kinnoo-registry-demo`).
- [ ] Create an **R2 API token** (S3 auth) with Object Read & Write scoped to that bucket. Record Access Key ID + Secret Access Key.
- [ ] Note the S3 endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
- [ ] (Optional) Seed data: `aws s3 sync ~/kinnoo-backups/registry-prod/ s3://kinnoo-registry-demo/ --endpoint-url https://<ACCOUNT_ID>.r2.cloudflarestorage.com` using the R2 keys. This restores your previously published agents *and* their `metadata/*.json`, so the registry comes back populated.

### Phase 2 — Configure the server (env only)
Create an `.env` for the container (do **not** commit; keep alongside your teardown backups):

```bash
# Runtime
KINNOO_ENV=production
KINNOO_VERSION=0.30.0
FRONTEND_URL=https://www.kinnoo.ai
CORS_ORIGINS=https://kinnoo.ai,https://www.kinnoo.ai

# Storage → Cloudflare R2 (drop-in via the s3 adapter)
REGISTRY_STORAGE_BACKEND=s3
REGISTRY_S3_BUCKET=kinnoo-registry-demo
REGISTRY_S3_REGION=auto                       # R2 expects "auto"
REGISTRY_S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
REGISTRY_S3_ACCESS_KEY_ID=<r2_access_key_id>
REGISTRY_S3_SECRET_ACCESS_KEY=<r2_secret_access_key>
REGISTRY_PRESIGN_TTL_SECONDS=900
REGISTRY_MAX_UPLOAD_MB=50

# Metadata → no database
REGISTRY_METADATA_BACKEND=json

# Local auth store (persist this path on a volume if using Option 2)
REGISTRY_LOCAL_STORAGE_ROOT=/data/registry
REGISTRY_ADMIN_EMAIL=<you@example.com>
REGISTRY_ADMIN_PASSWORD=<bootstrap_admin_password>

# Production signing secrets (reuse your backed-up values or generate fresh)
REGISTRY_TOKEN_SIGNING_SECRET=<...>
REGISTRY_SESSION_SIGNING_SECRET=<...>
REGISTRY_REGISTER_TOKEN_SECRET=<...>
REGISTRY_PASSWORD_RESET_TOKEN_SECRET=<...>

# Kinde OIDC (unchanged — copy from prod-secrets.json)
AUTH_PROVIDER=oidc_kinde
KINDE_ISSUER_URL=...
JWKS_ENDPOINT_URL=...
TOKEN_ENDPOINT=...
AUTHORIZATION_ENDPOINT=...
LOGOUT_ENDPOINT=...
USERINFO_ENDPOINT=...
KINDE_AUDIENCE=...
KINDE_WEB_CLIENT_ID=...
KINDE_WEB_CLIENT_SECRET=...
KINDE_CLI_CLIENT_ID=...
KINDE_WEB_REDIRECT_URI=https://www.kinnoo.ai/...   # keep Kinde callback URLs matching
KINDE_LOGOUT_REDIRECT_URI=https://www.kinnoo.ai/...
```

Notes:
- `KINNOO_ENV=production` enforces `CORS_ORIGINS` and the four signing secrets — that's why they're listed.
- `REGISTRY_S3_REGION=auto` is important for R2 SigV4.
- If you'd rather not manage prod secrets, you *can* run `KINNOO_ENV=dev` for a lighter demo (relaxes CORS + secret requirements), but production mode most closely mirrors the real thing for an interview.

### Phase 3 — Run the server
```bash
docker run -d --name kinnoo-server \
  --env-file .env \
  -v kinnoo-data:/data/registry \      # persistent auth state (Option 1/2)
  -p 127.0.0.1:8000:8000 \
  kinnoo-server
curl -s http://127.0.0.1:8000/health   # expect {"status":"ok"}
```

### Phase 4 — Expose via Cloudflare Tunnel
```bash
cloudflared tunnel login
cloudflared tunnel create kinnoo-demo
# Map hostname → local service (creates the api.kinnoo.ai DNS record in the zone):
cloudflared tunnel route dns kinnoo-demo api.kinnoo.ai
```
`~/.cloudflared/config.yml`:
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/jerry/.cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: api.kinnoo.ai
    service: http://localhost:8000
  - service: http_status:404
```
```bash
cloudflared tunnel run kinnoo-demo    # (or install as a service for Option 2)
```

### Phase 5 — Point the frontend + verify DNS
- [ ] Confirm `api.kinnoo.ai` resolves through the tunnel and serves `/health` over HTTPS.
- [ ] Ensure the Cloudflare Pages frontend's API base URL is `https://api.kinnoo.ai` and that this origin is in `CORS_ORIGINS`.
- [ ] Confirm Kinde application callback/redirect URLs still match `www.kinnoo.ai` (unchanged from prod, so they should).

---

## Validation checklist (end-to-end)

```bash
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
kinnoo login                                   # OIDC via Kinde
kinnoo init chatgpt demo-agent
kinnoo pack demo-agent
kinnoo publish demo-agent --pack --strict --remote   # writes archive + metadata JSON to R2
kinnoo search demo                              # reads metadata JSON from R2
kinnoo install <tenant>/demo-agent              # exercises presigned R2 download
kinnoo run demo-agent 'what is 2+2?'
```
- [ ] Web registry: browse `www.kinnoo.ai`, view the agent, sign in.
- [ ] R2 dashboard shows both the `.kno` archive and `metadata/**.json` objects.

---

## Gotchas / risks

1. **R2 presigned-URL download.** `download.py` hands the CLI a boto3-presigned R2 URL (`*.r2.cloudflarestorage.com`). This works, but requires `REGISTRY_S3_REGION=auto` and correct SigV4; **test `kinnoo install` specifically**. If a presign edge case appears, the simplest fix is to force downloads through the API's streaming `/archive` route (already implemented) instead of returning the R2 URL — a small, optional server tweak. Alternatively attach an R2 custom domain (`cdn.kinnoo.ai`) and serve public objects directly.
2. **Auth state persistence.** SQLite + files live under `REGISTRY_LOCAL_STORAGE_ROOT`. Mount a volume (Option 1/2). On an ephemeral host (or Option 3), state resets and you re-bootstrap the admin from env on each start — acceptable for a throwaway demo, not for continuity.
3. **`json` backend concurrency.** The global index uses best-effort optimistic retries (`manager.py`). Fine for single-user demos; not for many concurrent publishers. That's exactly the scale where you'd reintroduce Postgres/D1 — out of scope.
4. **Tunnel uptime (Option 1).** Laptop asleep = registry down. Start the stack before any live demo; consider Option 2 if you need always-on.
5. **Cloudflare Containers ≠ free/persistent.** Don't reach for Option 3 without first moving auth state off local disk.
6. **Kinde redirect URLs.** If you ever change the API/frontend hostnames, update the Kinde app config or `login` breaks.

---

## What to do with the leftover AWS bits
- **Secrets Manager (~$7/mo you're keeping):** not used by this design. Copy needed values into `.env`, then you can delete these secrets later to drop the $7 entirely.
- **Final RDS snapshot:** irrelevant to the demo (json backend). Keep only if you want the option to reconstruct old Postgres metadata; otherwise delete to save cents.
- **Terraform:** keep `iac/` in git as portfolio evidence. This Cloudflare path is intentionally *not* Terraform-managed — it's a handful of manual resources (bucket, token, tunnel), which is appropriate at demo scale. Optionally capture them later with the Cloudflare Terraform provider if you want the IaC story to extend here too.

---

## Rollback / re-scale later
Everything here is reversible and additive:
- To return to AWS prod: the `iac/` stack still stands up (see `notes/20260706-terraform-prod-teardown-and-redeploy.md`); flip env back to `s3`(AWS) + `postgres`.
- To scale the Cloudflare path: move compute to Option 2/3, and if you outgrow `json`, implement a D1 or Postgres `MetadataManagerProtocol` backend without touching routes or storage.

---

## Effort estimate
- **Option 1 (Mac + Tunnel + R2):** ~1–2 hours first time (bucket, token, env, tunnel, e2e test). Near-zero cost.
- **Option 2 (tiny host):** +1–2 hours for host setup + persistent volume + service install.
- **Biggest single risk to de-risk first:** the R2 presigned `kinnoo install` path (gotcha #1). Test it before you rely on it in front of anyone.
</content>
</invoke>
