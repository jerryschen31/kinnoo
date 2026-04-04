# Phase 8+ Infrastructure Planning — Production Deployment

_Date: April 4, 2026_
_Status: PLANNING — back-and-forth conversation_

This document captures the infrastructure planning session for kinnoo's production deployment. Three independent sub-agents evaluated the proposed plan, and the Tech Lead agent synthesized their findings.

---

## Agent Review Methodology

Three sub-agents independently evaluated the infrastructure plan:

| Agent | Role | Focus |
|-------|------|-------|
| **Agent 1** | Infrastructure Security Reviewer | Security risks, secret management, network isolation, compliance |
| **Agent 2** | DevOps & IaC Architect | Terraform modules, CI/CD pipelines, cost estimates, operational soundness |
| **Agent 3** | Application Architecture & Migration Reviewer | Code-level changes, migration paths, data model impact, production readiness |

---

## Section 1: Frontend — Cloudflare Pages

### Your Proposed Plan
Deploy Next.js frontend to Cloudflare Pages. Connect Git repo, select `web/` folder, build with `npm run build`, custom domain `kinnoo.ai`.

### Where All 3 Agents Agreed
- **Cloudflare Pages is the right choice** for the frontend. Free, simple, integrated with your existing Cloudflare account.
- **`BACKEND_URL` must be set as a build-time environment variable** in the Cloudflare Pages dashboard, not in code. This is because the Next.js rewrites in `web/next.config.ts` bake the backend URL at build time.
- **Current `web/next.config.ts` rewrites are already production-compatible.** No rewrite logic changes needed.
- **CORS is NOT needed** for the frontend-to-backend connection because Next.js rewrites proxy requests server-side (same-origin from the browser's perspective).

### Where Agents Differed

| Topic | Agent 1 | Agent 2 | Agent 3 |
|-------|---------|---------|---------|
| **SSR vs Static Export** | Didn't address | **Flagged a gotcha**: Cloudflare Pages does NOT natively support Node.js SSR for Next.js. Recommended `output: 'export'` (static export) or `next-on-pages` adapter. | Said SSR works with Cloudflare's Node.js support, but noted Edge Runtime adapter may be needed later. |
| **Security Headers** | Recommended adding CSP, X-Frame-Options, X-Content-Type-Options via `next.config.ts` headers. Flagged missing CSP as HIGH severity. | Didn't address specifically. | Didn't address. |
| **Source Maps** | Flagged as MEDIUM risk — set `productionBrowserSourceMaps: false` in prod. | Didn't address. | Didn't address. |

### Answering Your Questions

**Q: How do I specifically select the `web/` folder from my repo?**
In Cloudflare Pages build settings, set **Root directory** to `web`. This tells Cloudflare to `cd web` before running the build command. All three agents confirmed this.

**Q: Does this general step-by-step seem sound?**
Yes. The steps are correct. Additions:
- **Framework preset**: Next.js is correct.
- **Build command**: `npm run build`
- **Output directory**: Depends on export mode. If static export → `out`. If SSR → `.next`.

### Tech Lead Assessment

The Cloudflare Pages choice is solid. The **SSR compatibility issue flagged by Agent 2 is the most important finding**: Next.js 16 uses React Server Components by default, and Cloudflare Pages has limited SSR support compared to Vercel. 

**My recommendation**: Check whether your current pages use server-side features (data fetching at request time, cookies in `page.tsx`, etc.). If they do, you'll need the `@cloudflare/next-on-pages` adapter. If your pages are mostly client-side (which they appear to be from the auth client pattern in `web/lib/auth-client.ts`), static export should work fine.

**Action items:**
1. Set `BACKEND_URL=https://api.kinnoo.ai` as a Cloudflare Pages build environment variable
2. Test static export locally: add `output: 'export'` to `next.config.ts`, run `npm run build`, verify the `out/` directory works
3. Add security headers (Agent 1's recommendation is valid — CSP at minimum)
4. Set `productionBrowserSourceMaps: false` for production builds
5. Cloudflare DNS records and custom domain setup — can be managed via Terraform (Cloudflare provider)

### What Should Be IaC (Terraform)
- Cloudflare Pages project configuration
- DNS records (A/CNAME for `kinnoo.ai`)
- Environment variables (non-secret ones)

### What Should Be Manual
- Initial Git integration auth (requires GitHub OAuth token in Cloudflare dashboard — one-time setup)
- `BACKEND_URL` secret (set via Cloudflare Pages UI, not code)

---

## Section 2: Frontend-to-Backend Routing (API Entry)

### Your Proposed Plan
CNAME `api.kinnoo.ai` → AWS ALB. ACM cert for `api.kinnoo.ai`. DNS validation in Cloudflare. Cloudflare SSL Full (Strict). Orange cloud (proxied) on `api.kinnoo.ai`.

### Where All 3 Agents Agreed
- **The SSL flow is correct**: User → Cloudflare (Universal SSL) → AWS ALB (ACM cert) → Fargate (HTTP inside VPC).
- **ACM DNS validation works with Cloudflare**: Create the CNAME validation record in Cloudflare DNS, ACM will validate.
- **Full (Strict) SSL mode is the right choice**: Ensures end-to-end encryption between Cloudflare and your origin.
- **Proxied (orange cloud) on `api.kinnoo.ai` is correct**: Hides the ALB IP, provides DDoS protection.

### Where Agents Differed

| Topic | Agent 1 | Agent 2 | Agent 3 |
|-------|---------|---------|---------|
| **ALB Security Group** | **Critical**: Restrict ALB ingress to Cloudflare IP ranges only. Flagged as HIGH risk if ALB accepts traffic from any source. | Allowed `0.0.0.0/0` on ALB ingress, noting Cloudflare IPs optional. | Didn't address ALB security groups. |
| **Double TLS termination** | Noted it's "wasteful but not insecure" — Cloudflare already terminates TLS, re-terminating at ALB adds latency. Suggested ALB in HTTP mode. | Created both HTTPS (443) and HTTP (80, redirect) listeners on ALB. Used ACM cert on HTTPS listener. | Noted +50-100ms latency from Cloudflare egress, acceptable for MVP. |
| **WAF Rules** | Recommended Cloudflare WAF rules to block SQLi, XSS, path traversal before traffic hits backend. | Didn't address WAF specifically. | Didn't address. |
| **ALB Access Logging** | Recommended ALB access logs to S3 for audit trails (MEDIUM severity). | Didn't address explicitly. | Didn't address. |

### Tech Lead Assessment

Agent 1's security recommendations are the strongest here. **Restricting ALB security group to Cloudflare IPs is important** — without it, anyone who discovers your ALB DNS name can bypass Cloudflare's protections entirely. Cloudflare publishes their IP ranges at https://www.cloudflare.com/ips/ and they rarely change.

**On double TLS termination**: Since Cloudflare is proxying and you're using Full (Strict), you DO need the ACM cert on the ALB. The ALB must present a valid cert that Cloudflare can verify. This is correct as-is.

**Action items:**
1. Create CNAME `api.kinnoo.ai` → ALB DNS name (Terraform: `cloudflare_record`)
2. Request ACM cert for `api.kinnoo.ai` with DNS validation (Terraform: `aws_acm_certificate`)
3. Create ACM validation CNAME in Cloudflare (Terraform: `cloudflare_record` for validation)
4. Attach ACM cert to ALB HTTPS listener (Terraform: `aws_lb_listener`)
5. Set Cloudflare SSL to Full (Strict) (Terraform: `cloudflare_zone_settings_override`)
6. **Restrict ALB security group to Cloudflare IP ranges** (Terraform: `aws_security_group`)
7. Enable ALB access logging to S3 (Terraform: `aws_lb` with `access_logs` block)

### What Should Be IaC
Everything. All of the above items should be in Terraform.

---

## Section 3: Backend — AWS Fargate

### Your Proposed Plan
Containerize FastAPI in Docker → push to ECR → run on Fargate. IAM roles for task execution + task role (S3, KMS). VPC Endpoints for S3. ECS Service with ALB health checks.

### Where All 3 Agents Agreed
- **Fargate is the right choice** for a stateless FastAPI app. No OS management, scales to zero-ish (min 1 task for beta).
- **No Dockerfile exists yet — must create one immediately.** This is a critical blocker.
- **Multi-stage Docker build** is recommended (builder stage for pip install, runtime stage for the app).
- **Non-root user** in the container is a security requirement.
- **VPC Endpoints for S3** are important for performance and cost (avoids NAT Gateway data transfer charges).
- **Health check on `/health` endpoint** — both container-level and ALB target group level.
- **Secrets via AWS Secrets Manager**, injected into ECS task definition as `secrets` (not plaintext `environment`).

### Where Agents Differed

| Topic | Agent 1 | Agent 2 | Agent 3 |
|-------|---------|---------|---------|
| **Fargate sizing** | 512 CPU (0.5 vCPU), 1024 MB. Min 2 tasks for HA. | 256 CPU (0.25 vCPU), 512 MB. Min 1 task for beta. | Didn't specify; deferred to infra. |
| **File-based stores on Fargate** | **CRITICAL**: Sessions, users, metadata stored on ephemeral filesystem = LOST on restart. Requires migration to external stores BEFORE deployment. | Recommended persisting via ECS volume mount or migrating to RDS. But noted Phase 1 MVP could keep SQLite + JSON if using a single task with EFS. | Agreed it's a problem but recommended deferring PostgreSQL to post-beta. Suggested volume mount for beta. |
| **Rate limiting** | **CRITICAL**: In-memory rate limiter breaks with multiple instances. Requires Redis. | Acknowledges the issue; recommends Redis (ElastiCache) but defers to post-MVP. | Noted it's a problem; in-memory is acceptable for beta with 1 task. |
| **Uvicorn workers** | Didn't address. | Flagged: FastAPI runs single-process by default. Must use `--workers 2` (or more) in CMD. | Same: recommended `--workers 2` in the Docker CMD. |
| **Cost estimate** | Didn't estimate. | $37/month for 1 task (256 CPU, 512 MB) + $3/month CloudWatch = ~$41/month. | Didn't estimate. |

### Critical Discussion: File-Based Stores on Fargate

This is the **biggest architectural tension** in the plan. The current server stores users, sessions, and metadata as files on the local filesystem. Fargate containers have ephemeral storage that is lost when the task stops/restarts.

**Options for beta:**

| Option | Pros | Cons |
|--------|------|------|
| **A: Single Fargate task + EFS volume** | No code changes. All file-based stores work. | Single point of failure. EFS adds latency (~$0.30/GB/month). |
| **B: Migrate auth to Postgres (Phase 1), keep metadata on S3** | Production-grade auth. Metadata already on S3. | Requires 1-2 weeks of development (user store → Postgres, session store → Postgres). |
| **C: Move everything to S3 (users, sessions, metadata)** | Already have S3 storage backend. No new infra. | Sessions on S3 have high latency. Race conditions with concurrent writes. |

### Tech Lead Assessment

**I recommend Option A for beta launch, with Option B planned for the first post-beta sprint.**

Here's my reasoning:
1. **Beta doesn't need horizontal scaling.** One Fargate task with 0.5 vCPU and 1 GB RAM can handle hundreds of concurrent users. The rate limiter works because there's only one process.
2. **EFS is cheap and simple.** Mount a small EFS volume at `/data` for auth storage. Total cost: ~$1-2/month for the first GB.
3. **This lets us ship faster.** The PostgreSQL migration is 1-2 weeks of dev work. Doing it before shipping delays the beta unnecessarily.
4. **Risk is manageable.** If the single task crashes, EFS persists the data. Users experience a brief outage (30-60 seconds for ECS to restart the task), which is acceptable for beta.

**For Uvicorn workers**: Use `--workers 1` for beta (single task = single process, simpler). When you add multiple tasks, switch to `--workers 2`.

**Action items:**
1. Create a `Dockerfile` (multi-stage, non-root user, health check)
2. Create a `docker-compose.yml` for local development
3. Set up ECR repository (Terraform)
4. Create ECS cluster + Fargate service + task definition (Terraform)
5. Add EFS volume for persistent storage (Terraform)
6. Configure VPC Endpoints for S3 (Terraform)
7. Set up auto-scaling (min 1, max 3, target CPU 70%)

### Dockerfile (Recommended)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY server/requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
COPY --from=builder /build/wheels /wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
COPY server/ ./server/
ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
USER appuser
EXPOSE 8000
CMD ["uvicorn", "server.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Cost Estimate (Beta)

| Resource | Monthly Cost |
|----------|-------------|
| Fargate (1 task, 0.5 vCPU, 1 GB) | ~$37 |
| CloudWatch Logs (30-day retention) | ~$3 |
| ECR (image storage) | ~$1 |
| EFS (1 GB) | ~$1 |
| **Subtotal** | **~$42/month** |

### What Should Be IaC
Everything: ECR, ECS cluster, task definition, service, auto-scaling, security groups, EFS, VPC endpoints.

---

## Section 4: Storage — S3

### Your Proposed Plan
`s3://kinnoo-registry-public/<workspace_slug>/<tenant_slug>/<agent_archive_slug>/<agent_version_slug>/<agent_archive.kno>`
With `workspace_slug = "global"` for now. `archive.kno` as a generic filename.

### Current S3 Structure (in code)
```
archives/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}/{agent_slug}.kno
archives/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}/{agent_slug}.kno.sha256
metadata/tenants/{tenant_slug}/agents/{agent_slug}/versions/{version}.v1.json
metadata/tenants/{tenant_slug}/agents/{agent_slug}/index.v1.json
metadata/global/index.v1.json
```

### Where All 3 Agents Agreed
- **Keep `{agent_slug}.kno` naming** (NOT `archive.kno`). Better for debugging, S3 browsing, and download UX (user gets a descriptively-named file). The S3 key name doesn't affect the browser download filename (that's controlled by `Content-Disposition`), but self-documenting keys are easier to manage.
- **S3 bucket must be private** with presigned URLs for downloads (already implemented).
- **Enable encryption at rest** (AES-256 or KMS).
- **Enable versioning** for audit trails and disaster recovery.
- **Block all public access** via bucket policy.
- **Enable access logging** to a separate S3 bucket.

### Where Agents Differed

| Topic | Agent 1 | Agent 2 | Agent 3 |
|-------|---------|---------|---------|
| **Object Lock** | Recommended GOVERNANCE mode (90-day retention). Admins can override. | Recommended COMPLIANCE mode (365-day retention). Cannot be overridden. | Didn't recommend Object Lock specifically for beta. |
| **KMS vs AES-256** | Recommended KMS with dedicated key + Bucket Key enabled. More detailed Terraform. | Recommended AES-256 (simpler, sufficient for beta). | Didn't specify. |
| **workspace_slug prefix** | Didn't address. | Didn't address. | Recommended **skipping workspace_slug for beta**. Adds organizational overhead with no current benefit. Add it post-beta via dual-write migration. |
| **S3 cross-region replication** | Recommended CloudTrail for S3 audit. | Recommended cross-region replication to a backup bucket. | Didn't address. |
| **Current structure change** | Suggested keeping current structure. | Agreed, keep current structure. | Strongly recommended keeping current structure unchanged. Zero code changes needed. |

### Answering Your Questions

**Q: What do you think about naming every archive `archive.kno`?**
All three agents agree: **keep `{agent_slug}.kno`**. Reasons:
1. Self-documenting when browsing S3
2. Better download UX (user gets `my-agent.kno` not `archive.kno`)
3. No code changes needed (already working this way)
4. The S3 key name is independent of what the user sees when downloading (controlled by `Content-Disposition` header)

**Q: Does my S3 structure seem sound?**
Your proposed structure is sound in concept, but the agents recommend **keeping the current structure unchanged for beta** because:
1. It already works in code (`server/routes/publish.py`, `server/metadata/manager.py`)
2. The `workspace_slug` prefix adds no value until you implement multi-org workspaces
3. Migration would require changes to publish.py, download.py, metadata/manager.py, and remote_client.py — unnecessary risk for beta

### Tech Lead Assessment

**Keep the current S3 structure as-is.** It's clean, well-organized, and deeply integrated into the codebase. The `workspace_slug` prefix is premature optimization for a feature that doesn't exist yet.

For S3 security configuration:
- **Use AES-256 for encryption** (simpler than KMS for beta, can upgrade later)
- **Use GOVERNANCE mode for Object Lock** (allows admin overrides for bug fixes, unlike COMPLIANCE which is irreversible)
- **Skip cross-region replication for beta** (adds cost and complexity; S3 durability is already 11 9's)
- **Enable versioning** — this is cheap insurance

**Action items:**
1. Create S3 bucket with Terraform (encryption, versioning, public access block, access logging)
2. Create a separate S3 logs bucket
3. Configure Object Lock in GOVERNANCE mode
4. Create VPC Gateway Endpoint for S3 (free, keeps traffic inside AWS)

### Cost Estimate
~$5/month (100 agents × 10 versions × 1 MB average = negligible storage + requests)

### What Should Be IaC
Everything: S3 bucket, policies, lifecycle rules, Object Lock, VPC endpoint, logs bucket.

---

## Section 5: Metadata — PostgreSQL

### Your Proposed Plan
Phase 1: Move auth to Postgres. Phase 2: Move agent metadata to Postgres. Add repository abstraction layer.

### Where All 3 Agents Agreed
- **PostgreSQL is the right long-term database** for structured metadata, auth, and search.
- **Repository abstraction pattern** is a good idea — isolate data access to allow future backend swaps.
- **Alembic for schema migrations** (or equivalent migration tooling).

### Where Agents Differed — THIS IS THE BIGGEST DIVERGENCE

| Topic | Agent 1 | Agent 2 | Agent 3 |
|-------|---------|---------|---------|
| **When to migrate** | Do it before production. JSON stores are CRITICAL blockers for Fargate. | Phase 2 post-launch. Start beta with SQLite + JSON. Use EFS for persistence. | **Defer entirely to Phase 9.5 (post-beta)**. JSON + SQLite are fast enough for <100 users. |
| **RDS instance size** | db.t4g.small ($50/month) | db.t3.micro ($12/month) | Deferred (no cost estimate). |
| **Schema complexity** | 7+ tables including audit_log with row-level security. | 4 tables (users, sessions, registration_tokens, metadata_index). | 7 tables (users, sessions, token_consumption, agents, agent_versions, publish_events, tenants). |
| **ORM** | Didn't specify. | Didn't specify ORM, showed raw SQL. | Recommended SQLAlchemy 2.x with async support. |

### Postgres Schema (Synthesized from All 3 Agents)

Here is the minimal schema that covers auth + metadata + audit:

```sql
-- 1. Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- 'admin' or 'user'
    tenant_slug VARCHAR(255) NOT NULL,
    force_password_change BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token VARCHAR(255) UNIQUE NOT NULL,
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    invalidated_at BIGINT
);

-- 3. Consumed Tokens (replaces SQLite consumed_tokens.db)
CREATE TABLE consumed_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    token_type VARCHAR(50) NOT NULL,  -- 'register', 'password_reset'
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug VARCHAR(255) NOT NULL,
    agent_slug VARCHAR(255) NOT NULL,
    visibility VARCHAR(50) DEFAULT 'private',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_slug, agent_slug)
);

-- 5. Agent Versions
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    storage_keys JSONB NOT NULL,
    integrity JSONB NOT NULL,
    publisher_user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (agent_id, version)
);

-- 6. Publish Events (audit trail)
CREATE TABLE publish_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_version_id UUID NOT NULL REFERENCES agent_versions(id),
    user_id UUID NOT NULL REFERENCES users(id),
    archive_key VARCHAR(512),
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

That's 6 tables. Add a 7th (`tenants`) when multi-org is needed post-beta.

### Tech Lead Assessment

This is the section with the most disagreement, and I need to give a clear recommendation.

**My recommendation: Use EFS for beta. Migrate to Postgres in the first post-beta sprint (2-3 weeks after launch).**

Here's my reasoning:
1. **The Postgres migration is real work** — 1-2 weeks minimum. It touches `server/storage/user_store.py`, `server/storage/sqlite_auth_store.py`, `server/auth/session.py`, and `server/metadata/manager.py`. This delays beta launch.
2. **With a single Fargate task + EFS, the file-based stores work correctly.** EFS provides durable, shared-filesystem persistence that survives task restarts.
3. **The moment you need >1 Fargate task, you MUST have Postgres.** File-based stores with concurrent writers = race conditions. This is the trigger for the migration.
4. **SQLAlchemy 2.x + Alembic is the right stack** (Agent 3's recommendation). Async support plays well with FastAPI.

**The phased approach you described is correct:**
- Phase 1: Auth → Postgres (users, sessions, consumed_tokens)
- Phase 2: Metadata → Postgres (agents, agent_versions, publish_events)

### Cost Estimate
- db.t3.micro: ~$12/month (sufficient for beta scale)
- Storage (20 GB): ~$2/month
- **Total: ~$15/month when deployed**

### What Should Be IaC
RDS instance, subnet group, security group, Secrets Manager for DB password, parameter group.

---

## Section 6: Authentication — Auth0

### Your Proposed Plan
Replace custom auth with Auth0. JWT flow: login → get token → send token → API verifies.

### Where All 3 Agents Agreed — UNANIMOUS RECOMMENDATION

**All three agents recommend DEFERRING Auth0 to post-beta and hardening the existing custom auth instead.**

| Agent | Key Quote |
|-------|-----------|
| Agent 1 | "For now, defer Auth0 and harden custom auth first. Once Postgres + rate limiting are stable, plan Auth0." |
| Agent 2 | "Deploy initial MVP without Auth0; add it post-launch when usage patterns stabilize." |
| Agent 3 | "Auth0 doesn't fit beta timeline. Setup time 2-3 days, CLI flow requires new device code flow, tenant derivation requires Premium tier (~$100+/month)." |

### Why Auth0 is Wrong for Beta

| Concern | Detail |
|---------|--------|
| **CLI flow change** | Current: `kinnoo login` → prompt email/password → POST to `/api/auth/token` → get JWT. With Auth0: device authorization code flow (browser redirect), much more complex. |
| **Tenant derivation** | Current: `tenant_slug` derived from email domain (e.g., `jerry@gmail.com` → `jerry`). Auth0 requires "Organizations" feature for tenant isolation = paid tier. |
| **Breaking change** | Old JWT tokens (signed with your secret) won't validate against Auth0 keys. Requires migration window. |
| **External dependency** | Auth0 outage = users can't log in. Custom auth = you control uptime. |
| **Migration risk** | Switching auth providers is dangerous. If migration has a bug, users get locked out. |

### What to Do Instead (Harden Custom Auth)

All agents agree on these hardening steps for the existing auth system:

1. **Account lockout after N failed login attempts** (NOT currently implemented)
2. **Session revocation on password change** (NOT currently implemented)
3. **Password policy enforcement** (minimum length, complexity — currently any password is accepted)
4. **Auth event audit logging** (part of Feature89 structured logging)
5. **Token denylist for logout** (currently `kinnoo logout` just clears local config; server-side token remains valid until expiry)

### Auth0 Migration Path (Post-Beta, If Needed)

When/if you migrate to Auth0 later:
1. Set up Auth0 tenant + application configuration
2. Add Auth0 login alongside custom login (feature flag: `USE_AUTH0=false`)
3. Migrate existing users to Auth0 (Auth0 Management API bulk import)
4. Run dual auth for 60-90 days (accept both old JWT and Auth0 JWT)
5. Deprecate custom login
6. Remove custom auth code

### Tech Lead Assessment

**I strongly agree with all three agents: defer Auth0.** The existing auth system is functional and secure (Argon2 hashing, CSRF protection, rate limiting). The hardening items above are 1-2 days of work, not 2-3 weeks of Auth0 integration.

Auth0 makes sense when you need: SSO, MFA, compliance certifications, or you want to outsource auth security entirely. None of these are beta requirements.

**Action items (for beta):**
1. Add account lockout (5 failed attempts → 15-minute lockout)
2. Add password policy enforcement (min 10 chars)
3. Add session revocation on password change
4. Structured logging for auth events (part of Feature89)

---

## Section 7: Identity and Access Control (IAM)

### Minimum IAM Roles Needed

All agents agreed on the core roles. Here's the consolidated list:

| Role | Purpose | Permissions |
|------|---------|-------------|
| **ECS Task Execution Role** | Allows ECS to pull images and get secrets | ECR pull, Secrets Manager read, CloudWatch Logs write |
| **ECS Task Role** | Application runtime permissions | S3 read/write (registry bucket), RDS connect (when migrated) |
| **GitHub Actions OIDC Role** | CI/CD pipeline creates deployments | ECR push, ECS update-service |
| **S3 Replication Role** (optional) | Cross-region backup | S3 replicate operations |

### Human IAM Users/Roles

| Role | Who | Permissions | MFA |
|------|-----|-------------|-----|
| **Root Account** | You (Jerry) | Full access (emergency only) | **Required (hardware key)** |
| **Admin** | You (Jerry) | Most AWS services except KMS key deletion | Required |
| **Deployment Engineer** | CI/CD or trusted human | ECR push, ECS deploy, Secrets Manager read | Required for console |

### Tech Lead Assessment

Agent 1 had the most detailed IAM analysis with per-role Terraform code. The key principles:
1. **Least privilege**: Each role gets only the permissions it needs
2. **MFA enforcement**: All human users must have MFA before any actions
3. **Short-lived credentials**: Use IAM roles (not access keys) wherever possible
4. **GitHub Actions OIDC**: Use OIDC federation instead of long-lived AWS access keys in GitHub Secrets

**Action items:**
1. Enable MFA on root account (hardware key)
2. Create IAM roles via Terraform (all 4 roles above)
3. Set up GitHub Actions OIDC provider in AWS (Terraform: `aws_iam_openid_connect_provider`)
4. Never create long-lived access keys — use OIDC for CI/CD, instance roles for Fargate

### What Should Be IaC
**Everything.** All IAM roles, policies, and OIDC providers should be in Terraform.

---

## Section 8: CLI ↔ API Mapping

### Current State (All Commands Mapped)

Agent 3 performed a thorough audit. All critical CLI commands are already mapped to API endpoints:

| CLI Command | API Endpoint | Status |
|-------------|-------------|--------|
| `kinnoo publish <agent>` | `POST /api/publish` | ✅ Implemented |
| `kinnoo install <agent>` | `GET /api/agents/{tenant}/{name}/{version}/download` | ✅ Implemented |
| `kinnoo search <query>` | `GET /api/search?q={query}` | ✅ Implemented |
| `kinnoo login` | `POST /api/auth/token` | ✅ Implemented |
| `kinnoo logout` | (local config clear only) | ✅ Implemented |
| `kinnoo list --remote` | `GET /api/agents` | ✅ Implemented |

### Missing Endpoints (Post-Beta)

| Endpoint | Use Case | Priority |
|----------|----------|----------|
| `DELETE /api/agents/{tenant}/{name}/{version}` | Unpublish an agent | Post-beta |
| `PATCH /api/agents/{tenant}/{name}/{version}` | Update visibility/metadata | Post-beta |
| `GET /api/agents/{tenant}/{name}/{version}/manifest` | Inspect without downloading | Post-beta |

### Tech Lead Assessment

**No gaps for beta.** All critical user workflows (sign up → login → pack → publish → search → install → run) have working CLI-to-API mappings. The missing endpoints are enhancements, not blockers.

---

## Section 9: CI/CD Pipeline (Not in Your Original Plan — Added by Agent 2)

Agent 2 identified that **CI/CD was not mentioned** in your infrastructure plan but is essential. They recommended three GitHub Actions pipelines:

| Pipeline | Trigger | Does What |
|----------|---------|-----------|
| **Deploy Frontend** | Push to `main` with `web/**` changes | Build Next.js → Deploy to Cloudflare Pages |
| **Deploy Backend** | Push to `main` with `server/**` changes | Build Docker → Push to ECR → Update ECS service |
| **Deploy Infrastructure** | Push to `main` with `terraform/**` changes | Terraform plan → apply (on main), plan-only on PRs |

### Tech Lead Assessment

This is a critical addition to the plan. You need CI/CD before production — manual deployments are error-prone and don't create an audit trail.

**Key design decisions:**
- Use **GitHub Actions OIDC** for AWS credentials (no long-lived secrets)
- Use **Cloudflare API token** for frontend deploys (store as GitHub Secret)
- Run **Trivy vulnerability scan** on Docker images before deployment
- Run **Terraform plan** as a PR comment for review before applying

**Action items:**
1. Create `.github/workflows/deploy-frontend.yml`
2. Create `.github/workflows/deploy-backend.yml`
3. Create `.github/workflows/deploy-infrastructure.yml`
4. Set up GitHub OIDC provider in AWS
5. Store Cloudflare API token and AWS account ID as GitHub Secrets

---

## Section 10: Terraform Project Structure

### Recommended Layout

```
terraform/
├── versions.tf              # Required providers (aws, cloudflare)
├── providers.tf             # Provider configuration
├── variables.tf             # Root-level input variables
├── outputs.tf               # Root-level outputs
├── locals.tf                # Common locals (tags, naming)
├── main.tf                  # Root module instantiation
│
├── state/                   # Bootstrap (run once manually)
│   └── main.tf              # S3 bucket + DynamoDB for TF state locking
│
├── modules/
│   ├── vpc/                 # VPC, subnets, NAT, route tables
│   ├── ecr/                 # ECR repository
│   ├── ecs-fargate/         # ECS cluster, task def, service, auto-scaling
│   ├── s3-registry/         # S3 bucket with encryption, versioning, Object Lock
│   ├── alb/                 # ALB, listeners, target groups
│   ├── rds/                 # RDS PostgreSQL (Phase 2)
│   ├── iam/                 # All IAM roles and policies
│   ├── cloudflare/          # DNS records, Pages project, SSL settings
│   └── secrets/             # Secrets Manager secrets
│
├── environments/
│   ├── dev/
│   │   └── terraform.tfvars
│   ├── staging/
│   │   └── terraform.tfvars
│   └── prod/
│       └── terraform.tfvars
│
└── .terraformignore
```

### State Management
- **Backend**: S3 bucket + DynamoDB table for state locking
- **One state file per environment** (separate `terraform.tfstate` for dev/staging/prod)
- **State bucket must be created manually first** (bootstrap step)

---

## Section 11: Cost Summary (Beta)

| Resource | Monthly Cost |
|----------|-------------|
| **Cloudflare Pages** (frontend) | Free |
| **ALB** (load balancer) | ~$25 |
| **Fargate** (1 task, 0.5 vCPU, 1 GB) | ~$37 |
| **S3** (registry storage) | ~$5 |
| **EFS** (persistent storage for auth/file stores) | ~$1 |
| **CloudWatch** (logs, metrics) | ~$5 |
| **ECR** (Docker images) | ~$1 |
| **NAT Gateway** (if needed — see note) | ~$32 |
| **ACM** (SSL certificate) | Free |
| **Route 53** (if used) | ~$0.50 |
| **Secrets Manager** (6 secrets) | ~$3 |
| **RDS** (Postgres, Phase 2) | ~$15 |
| **Auth0** | Deferred |
| **Total (beta, Phase 1)** | **~$110-125/month** |
| **Total (beta + Postgres, Phase 2)** | **~$125-140/month** |

**NAT Gateway note**: If your Fargate tasks need to reach the internet (for email sending, external API calls), you'll need a NAT Gateway (~$32/month). If all traffic stays internal (S3 via VPC Endpoint, RDS in VPC), you may be able to avoid it. **This is the sneakiest cost in AWS.**

---

## Section 12: Remaining Gaps — Full Inventory

### Your Final Question: What's Left Between Current State and Production?

Here's the full gap analysis organized by your categories:

---

### 12.1 Kinnoo CLI

| Gap | Severity | Status |
|-----|----------|--------|
| CLI is functional for all core workflows | N/A | ✅ Done |
| 19 features at `needs-review` status | Medium | Needs Tech Lead review (Phase 10) |
| `kinnoo test` foundation | Low | At needs-review; not blocking beta |
| No `kinnoo unpublish` or `kinnoo update-metadata` | Low | Post-beta |

**Assessment**: CLI is ready for beta. The `needs-review` features should be reviewed but aren't blocking.

---

### 12.2 Security Hardening / Trust Model

| Gap | Severity | Feature | Effort |
|-----|----------|---------|--------|
| **Server config hardening** (fail-fast on dev secrets in production) | CRITICAL | Feature89 | 1 day |
| **Structured JSON logging** with request IDs | HIGH | Feature89 | 1 day |
| **CORS configuration** for production origins | MEDIUM | Feature89 | 0.5 day |
| **Health check** (readiness probe with S3 connectivity) | MEDIUM | Feature89 | 0.5 day |
| **Upload validation hardening** (zip bomb protection, path traversal, file count limits) | HIGH | Feature90 | 1-2 days |
| **Embedded integrity manifest** (META-INF/integrity.json in .kno archives) | MEDIUM | Feature86 | 1-2 days |
| **Embedded signature** (META-INF/signature.json) | MEDIUM | Feature87 | 1 day |
| **Install-time integrity verification** | MEDIUM | Feature88 | 1 day |
| **Configurable rate limits** via env vars | LOW | Feature91 | 0.5 day |
| **Account lockout** after failed login attempts | MEDIUM | New | 0.5 day |
| **Password policy enforcement** | MEDIUM | New | 0.5 day |
| **Registry index signing** (packages.json with TUF-like trust chain) | HIGH | Post-beta | 1-2 weeks |

**Assessment**: Feature89 and Feature90 are the critical blockers. Features 86-88 (embedded integrity) are nice-to-have for beta but not blocking. Registry index signing is post-beta.

---

### 12.3 Infrastructure

| Gap | Severity | Effort |
|-----|----------|--------|
| **Dockerfile** (does not exist) | CRITICAL | 0.5 day |
| **Terraform modules** (do not exist) | CRITICAL | 3-5 days |
| **CI/CD pipelines** (do not exist) | HIGH | 1-2 days |
| **AWS account setup** (VPC, subnets, security groups) | CRITICAL | 1-2 days |
| **S3 bucket creation** with security config | HIGH | 0.5 day (Terraform) |
| **ECR repository** | HIGH | 0.5 day (Terraform) |
| **ECS/Fargate service** | HIGH | 1-2 days (Terraform) |
| **ALB + ACM cert** | HIGH | 0.5 day (Terraform) |
| **Cloudflare DNS + Pages** setup | MEDIUM | 0.5 day |
| **Secrets Manager** (all 6+ secrets) | HIGH | 0.5 day (Terraform) |
| **EFS volume** (for file-based stores) | MEDIUM | 0.5 day (Terraform) |
| **CloudWatch** monitoring + alarms | MEDIUM | 0.5 day (Terraform) |
| **PostgreSQL / RDS** | Medium | 1-2 days (Terraform + migration code) – Phase 2 |

**Assessment**: Infrastructure is the biggest work item. Terraform modules are ~3-5 days of focused work. The Dockerfile is the first thing to build.

---

### 12.4 Documentation

| Gap | Severity | Feature |
|-----|----------|---------|
| **kinnoo.yaml specification** (public-facing) | HIGH | Feature92 |
| **CLI command reference** (all 21 commands) | HIGH | Feature93 |
| **Security model document** | MEDIUM | Feature94 |
| **Getting started guide** | CRITICAL | Feature95 |
| **Registry guide** (publish/install from registry) | HIGH | Feature95 |
| **README rewrite** (beta-ready) | HIGH | Feature96 |

**Assessment**: Feature95 (getting started guide) and Feature96 (README) are the minimum for beta. Features 92-94 are important but can ship in the first week after beta launch.

---

### 12.5 Testing

| Gap | Severity | Status |
|-----|----------|--------|
| Existing unit tests | N/A | ✅ Extensive test suite in `tests/` |
| End-to-end test (init → pack → publish → install → run) | HIGH | Needs creation |
| Server integration tests (API endpoint tests) | MEDIUM | Unclear status |
| Load testing / stress testing | LOW | Post-beta |
| Docker smoke test | MEDIUM | Create after Dockerfile |

**Assessment**: An end-to-end smoke test is important before beta. Create a script that walks through the full workflow against the staging registry.

---

### 12.6 Administrative / Cleanup

| Gap | Severity |
|-----|----------|
| **Public GitHub repo** setup (separate from private dev repo) | HIGH |
| **PyPI package** publishing setup | HIGH |
| **.gitignore audit** (no secrets, no build artifacts) | MEDIUM |
| **CONTRIBUTING.md** | LOW |
| **CODE_OF_CONDUCT.md** | LOW |
| **Feature/task manifest cleanup** (FEATURES.txt, TASKS.txt, TESTS.txt) | LOW |

---

## Section 13: Proposed Implementation Order

Based on all analysis, here's the recommended implementation sequence:

### Sprint 1: Foundation (Week 1-2)
1. **Feature89**: Server production config + structured logging + CORS + health checks
2. **Feature90**: Upload validation hardening
3. **Dockerfile** creation + local Docker testing
4. **docker-compose.yml** for local dev

### Sprint 2: Infrastructure (Week 2-3)
5. **Terraform state bootstrap** (S3 + DynamoDB for state locking)
6. **Terraform modules**: VPC, S3, ECR, ECS, ALB, IAM, Secrets Manager, EFS
7. **CI/CD pipelines**: GitHub Actions for frontend, backend, and infrastructure

### Sprint 3: Deployment + Validation (Week 3-4)
8. **Deploy to staging** (if separate env) or directly to production
9. **Cloudflare Pages** setup for frontend
10. **DNS + SSL** configuration (api.kinnoo.ai)
11. **End-to-end smoke test** against production

### Sprint 4: Documentation + Launch (Week 4-5)
12. **Feature95**: Getting started guide
13. **Feature96**: README rewrite
14. **Feature92**: kinnoo.yaml spec (can overlap with launch)
15. **Public repo** setup + PyPI publishing
16. **Beta launch announcement**

### Post-Beta Sprint 1: Hardening (Week 5-7)
17. **PostgreSQL migration** (Phase 1: auth, Phase 2: metadata)
18. **Feature91**: Configurable rate limiting
19. **Features 86-88**: Embedded integrity manifest + verification
20. **Features 92-94**: Complete documentation (CLI reference, security model)
21. **Review needs-review features** (Phase 10)

---

## Open Questions for Jerry

Before solidifying the plan, I need your input on these decisions:

### Q1: Static Export vs SSR for Cloudflare Pages
Does your Next.js frontend use any server-side features (data fetching at request time, middleware, cookies reading in `page.tsx`)? If all pages are client-rendered, static export is simpler. If you need SSR, we'll need the `@cloudflare/next-on-pages` adapter.

### Q2: NAT Gateway Decision
Does your Fargate server need to reach the public internet? Specifically:
- Do you send emails (for registration/password reset)? If so, via what service? (SES, SendGrid, etc.)
- Do any API routes call external services?
If no → we can avoid the NAT Gateway ($32/month savings).
If yes → we need a NAT Gateway or could use a public subnet with a static IP.

### Q3: EFS vs Immediate Postgres
Are you comfortable with the EFS approach for beta (file-based stores persist across task restarts), with Postgres migration planned for 2-3 weeks post-launch? Or would you prefer to do the Postgres migration before beta?

### Q4: Object Lock Mode
GOVERNANCE (admins can override, good for fixing bugs in published packages) vs COMPLIANCE (nobody can delete, good for trust story). My recommendation is GOVERNANCE for beta.

### Q5: Staging Environment
Do you want a separate staging environment, or deploy directly to production and test there? A staging environment roughly doubles the infrastructure cost.

### Q6: Domain
The plan references both `kinnoo.ai` and `kinnoo.dev` in various places. Which domain are you using for production? If `kinnoo.ai`, then the API subdomain would be `api.kinnoo.ai`.
