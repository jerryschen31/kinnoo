# Phase 8+ Final Feature Plan — Dev/Beta Release

_Date: April 4, 2026_
_Status: APPROVED — Ready for implementation_

This document is the **final feature plan** for the kinnoo dev/beta release. It synthesizes:
- [phase8-plus-release-plan-1.md](phase8-plus-release-plan-1.md) — original accelerated beta plan
- [../phase8-plus-planning-2.md](../phase8-plus-planning-2.md) — infrastructure planning with 3-agent review
- [phase8-planning-1-2-my-responses.md](phase8-planning-1-2-my-responses.md) — Jerry's decisions and responses

Three independent sub-agents analyzed the planning docs and user responses, then proposed feature lists. This document merges and refines those proposals into the **final, actionable feature set**.

---

## Agent Synthesis Summary

| Agent | Focus | Features Proposed | Key Strengths |
|-------|-------|------------------|---------------|
| **Agent 1** | Security & Infrastructure | 38 features (86-123) | Thorough IaC breakdown, auth hardening detail, deployment validation |
| **Agent 2** | DevOps & IaC | 21 features (86-106) | Detailed Terraform modules, CI/CD pipeline design, cost awareness |
| **Agent 3** | Docs & Launch UX | 25 features (86-110) | Strong UX perspective, anti-spam solution, admin workflows, onboarding templates |

### Where All 3 Agents Agreed
1. **Features 86-99 are correct as-is** — keep the planning-1 definitions unchanged
2. **Dockerfile is a critical blocker** — must exist before any deployment
3. **Auth hardening is needed** — account lockout, password policy, token blacklist
4. **Admin CLI for user management** — Jerry needs `kinnoo-server` commands to create/reset users
5. **Terraform should be in `iac/` folder** with modules and environment-specific tfvars
6. **E2E smoke testing** is essential before launch
7. **No NAT Gateway** for dev/beta
8. **Invite-only** — no open registration form, manual token issuance

### Where Agents Differed
| Topic | Resolution |
|-------|------------|
| **Terraform granularity** | Agent 1 had 11 separate Terraform features; Agent 2 had 6; Agent 3 didn't propose IaC features. **Decision: 5 consolidated Terraform features** (grouped by logical deployment unit) |
| **Admin dashboard** | Agent 3 proposed a web admin dashboard. **Decision: Defer to post-beta.** CLI-based admin is sufficient. |
| **API key management** | Agent 3 proposed API keys for programmatic access. **Decision: Defer.** JWT tokens with auto-refresh are sufficient for beta. |
| **Landing page scope** | Agent 3 proposed a full landing page redesign. **Decision: Minimal update** — update existing web UI with invite-only messaging. |
| **Signing algorithm** | Agent 2 proposed RSA-2048-SHA256. **Decision: Keep Ed25519** — already implemented in `signing.py`, more modern, better performance. |
| **Monitoring scope** | Agent 1 proposed CloudWatch dashboards + custom metrics. Agent 3 proposed CloudWatch + SNS alarms. **Decision: Basic CloudWatch** — log groups, alarms for 5xx and unhealthy targets, SNS for password reset alerts. |

---

## User Decisions (from phase8-planning-1-2-my-responses.md)

| Decision | Choice |
|----------|--------|
| Frontend rendering | Static export (all client-rendered) |
| Dev domain | `dev.kinnoo.ai` (frontend), `dev-api.kinnoo.ai` (API) |
| Backend compute | Single Fargate task + EFS (Option A) |
| S3 encryption | AES-256 |
| S3 Object Lock | GOVERNANCE mode |
| Database | EFS for dev/beta, defer Postgres |
| Auth provider | Harden existing custom auth, defer Auth0 |
| NAT Gateway | Not needed for dev |
| Staging environment | None — dev → prod directly |
| IaC folder name | `iac/` from project root |
| AWS account | kinnoo, ID 386775099533, us-west-2 |
| Registration model | Invite-only, Jerry manually creates users |
| Forgot password | CloudWatch alert → Jerry manually sends temp password |
| Email anti-spam | No form on landing page; "Email us" link only |
| Terraform variables | Modules with variables, `environments/dev/terraform.tfvars` |

---

## Final Feature List (features 86–113)

### Phase 8: Client-Side Security Hardening (3 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature86 | Embedded integrity manifest (META-INF/integrity.json) | swe-agent | 1-2 days |
| feature87 | Embedded signature (META-INF/signature.json) | swe-agent | 1 day |
| feature88 | Install-time integrity verification | swe-agent | 1 day |

**Phase scope:** Pure client-side changes to `pack_command.py` and `install_command.py`. New module `integrity.py`. No server changes. Existing signing infrastructure in `signing.py` is reused for feature87.

**Dependencies:** None — independent of server work.

---

### Phase 9: Server Hardening & Containerization (6 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature89 | Production server configuration and deployment hardening | swe-agent | 2-3 days |
| feature90 | Server-side upload validation and integrity enforcement | swe-agent | 1-2 days |
| feature91 | Production-grade rate limiting and abuse protections | swe-agent | 1 day |
| feature100 | Auth hardening — lockout, password policy, token blacklist | swe-agent | 2 days |
| feature101 | Production Dockerfile and docker-compose | swe-agent | 1 day |
| feature102 | Admin CLI for user management | swe-agent | 1 day |

**Phase scope:** All server-side code changes. SWE agent works in `server/` directory. Features 89-91 harden existing code. Feature 100 adds new security controls. Feature 101 creates Dockerfile. Feature 102 extends `server/cli.py`.

**Dependencies:** None — independent of client work.

---

### Phase 10: In-Flight Feature Review (No new features)

Tech Lead reviews features 69-85 currently at `needs-review` status. Critical for beta: feature70 (landing page + docs), feature71 (strict CI), feature72 (lockfile), feature74 (uninstall). OpenClaw wrappers (76-85) reviewed but not blocking.

---

### Phase 11: Documentation (5 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature92 | kinnoo.yaml specification document | swe-agent | 1-2 days |
| feature93 | CLI command reference document | swe-agent | 2-3 days |
| feature94 | Security model document | swe-agent | 1 day |
| feature95 | Getting started guide and registry guide | swe-agent | 1 day |
| feature96 | README rewrite and supported agents document | swe-agent | 0.5 day |

**Phase scope:** Pure documentation. No code changes. SWE agent creates files in `docs/` and updates `README.md`.

**Dependencies:** Phase 8 (features 86-88) should be completed so security docs are accurate.

---

### Phase 12: Infrastructure as Code (5 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature103 | Terraform project setup, state bootstrap, and VPC networking | swe-agent + operator | 2 days |
| feature104 | Terraform storage and security (S3, IAM, Secrets Manager) | swe-agent | 1-2 days |
| feature105 | Terraform compute stack (ECR, ALB, ACM, ECS/Fargate, EFS) | swe-agent | 2-3 days |
| feature106 | Terraform Cloudflare DNS and Pages | swe-agent | 1 day |
| feature107 | Terraform monitoring (CloudWatch, alarms, SNS) | swe-agent | 1 day |

**Phase scope:** All IaC work. SWE agent creates `iac/` directory structure with Terraform modules. Operator (Jerry) runs `terraform apply` for state bootstrap and provides AWS/Cloudflare credentials.

**Dependencies:** Phase 9 (Dockerfile must exist before ECS task definition references it).

**Terraform project structure:**
```
iac/
├── versions.tf              # Required providers (aws, cloudflare)
├── providers.tf             # Provider config + S3 backend
├── variables.tf             # Root-level input variables
├── outputs.tf               # Root-level outputs
├── locals.tf                # Common locals (tags, naming)
├── main.tf                  # Module instantiation
├── state/
│   └── main.tf              # Bootstrap: S3 backend + native lockfile locking
├── modules/
│   ├── vpc/                 # VPC, subnets, SGs, VPC endpoints
│   ├── s3-registry/         # S3 bucket with encryption, Object Lock
│   ├── iam/                 # IAM roles and policies
│   ├── secrets/             # Secrets Manager secrets
│   ├── ecr/                 # ECR repository
│   ├── alb/                 # ALB, listeners, target groups, ACM
│   ├── ecs-fargate/         # ECS cluster, task def, service, EFS
│   ├── cloudflare/          # DNS records, Pages project
│   └── monitoring/          # CloudWatch log groups, alarms, SNS
└── environments/
    └── dev/
        └── terraform.tfvars # Dev environment values
```

---

### Phase 13: CI/CD & Open Source Preparation (3 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature97 | Public GitHub repository preparation | swe-agent + operator | 1-2 days |
| feature98 | GitHub Actions CI/CD pipeline | swe-agent | 1 day |
| feature99 | PyPI package publishing configuration | swe-agent | 0.5 day |

**Phase scope:** Repository hygiene, GitHub Actions workflows, PyPI setup. Feature 97 involves audit, templates, and CONTRIBUTING.md. Feature 98 creates deployment workflows. Feature 99 validates pyproject.toml and publishing.

**Dependencies:** Phase 12 (CI/CD deployment workflows reference IaC resources like ECR, ECS).

---

### Phase 14: Beta Operations Setup (3 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature108 | Invite-only registration enforcement | swe-agent | 1-2 days |
| feature109 | Forgot password flow with operator alert | swe-agent | 1 day |
| feature110 | Landing page update for invite-only beta | swe-agent | 0.5 day |

**Phase scope:** Server-side changes for invite-only workflow. Feature 108 adds invite token validation to registration. Feature 109 adds forgot-password endpoint that fires SNS alert. Feature 110 updates the web UI and/or Next.js frontend.

**Dependencies:** Phase 9 (server hardening must be done first).

---

### Phase 15: Deployment, Testing & Launch (3 features)

| ID | Title | Owner | Est. Effort |
|----|-------|-------|-------------|
| feature111 | End-to-end smoke test script | swe-agent | 1-2 days |
| feature112 | Registry seeding and validation | operator | 2-3 days |
| feature113 | Launch readiness checklist | swe-agent + operator | 0.5 day |

**Phase scope:** Final validation before launch. Feature 111 creates an automated test that exercises all 7 key workflows against the production registry. Feature 112 is operator work — Jerry publishes 3-5 real agents. Feature 113 is the go/no-go checklist.

**Dependencies:** All prior phases.

---

## Mock Walkthrough: End-State Validation

After all 28 features are implemented, here is what the deployed system looks like:

### Infrastructure
- ✅ `dev.kinnoo.ai` — Cloudflare Pages static Next.js frontend
- ✅ `dev-api.kinnoo.ai` — CNAME → AWS ALB → Fargate (FastAPI)
- ✅ S3 bucket with AES-256, GOVERNANCE Object Lock, versioning
- ✅ EFS volume for auth data persistence
- ✅ Secrets Manager for all signing/session keys
- ✅ CloudWatch logs + alarms + SNS notifications
- ✅ No NAT Gateway, VPC endpoints for S3

### Security
- ✅ Archives contain `META-INF/integrity.json` with per-file SHA-256
- ✅ Signed archives contain `META-INF/signature.json` (Ed25519)
- ✅ `kinnoo install` verifies integrity before extraction
- ✅ `kinnoo install --strict` requires both integrity + signature
- ✅ Server rejects malformed, tampered, and oversized uploads
- ✅ Rate limiting per IP and per tenant
- ✅ Account lockout after 5 failed logins
- ✅ Password policy (min 12 chars, complexity requirements)
- ✅ Token blacklist on logout
- ✅ ALB restricted to Cloudflare IP ranges
- ✅ Non-root Docker container

### User Workflows (validated by e2e smoke test)
1. **Jerry creates user:** `kinnoo-server user create --email bob@example.com` → gets temp password
2. **Bob logs in:** `kinnoo login --email bob@example.com` → prompted for password → JWT stored in ~/.kinnoo/config.yaml
3. **Bob creates agent:** `kinnoo init my-agent --framework chatgpt` → scaffold generated
4. **Bob runs agent:** `kinnoo run my-agent "hello"` → ChatGPT response
5. **Bob packs agent:** `kinnoo pack my-agent --sign` → my-agent.kno with META-INF/integrity.json + signature.json
6. **Bob publishes:** `kinnoo publish my-agent --remote` → uploaded to S3, validated server-side
7. **Alice searches:** `kinnoo search chatgpt --remote` → finds my-agent
8. **Alice installs:** `kinnoo install my-agent --remote --strict` → verified, extracted, venv created
9. **Alice runs:** `kinnoo run my-agent "test"` → ChatGPT response
10. **Bob forgets password:** clicks "Forgot Password?" → Jerry gets CloudWatch alert → `kinnoo-server user reset-password --email bob@example.com` → Bob uses temp password

### Documentation
- ✅ `docs/kinnoo-yaml-spec.md` — manifest specification
- ✅ `docs/cli-reference.md` — all 21+ CLI commands
- ✅ `docs/security-model.md` — threat model, signing, permissions
- ✅ `docs/getting-started.md` — quick-start tutorial
- ✅ `docs/registry-guide.md` — publish/install from registry
- ✅ `docs/supported-agents.md` — framework matrix
- ✅ `README.md` — beta-ready, links to all docs

### CI/CD
- ✅ GitHub Actions: test on PR, deploy backend on main push, deploy frontend on main push
- ✅ Terraform plan on PR, apply on merge
- ✅ PyPI publishing on release tag

---

## Anti-Spam Solution (Addressing Jerry's Concern)

**Problem:** Exposing email on landing page → bot spam

**Solution (agreed by all 3 agents):**
1. **No sign-up form on landing page.** Display: "Interested in beta? Email us at contact@kinnoo.ai" — no form = no form spam
2. **Use email obfuscation:** Render the email address via JavaScript (not plain HTML) to prevent bot scraping
3. **Alternative: Use a Cloudflare-protected contact form** that requires basic JS rendering (bots can't submit)
4. **Invite tokens:** Registration requires a valid invite token that Jerry generates via CLI. No open registration.
5. **Rate limit `/register`:** Max 5 attempts per IP per hour

This is effectively **no-cost anti-spam:** bots can't sign up (no form), can't register (no open endpoint), and email crawlers are thwarted by JS rendering.

---

## Manual User Creation Workflow

Jerry's workflow for onboarding a new beta user:

```bash
# 1. User sends email: "I'd like to try kinnoo"

# 2. Generate invite token
kinnoo-server invite create --email user@example.com --days-valid 30
# Output: Invite token: abc123xyz
#         URL: https://dev.kinnoo.ai/register?token=abc123xyz
#         Expires: 2026-05-04

# 3. OR create user directly (skip self-registration)
kinnoo-server user create --email user@example.com
# Output: Created user user@example.com
#         Temporary password: Xk9$mP2qR7!fL4nW
#         Tenant: user

# 4. Send welcome email to user with credentials and getting-started link
```

---

## Forgot Password Workflow

```bash
# 1. User clicks "Forgot Password?" on web login page
# 2. User enters email → POST /forgot-password
# 3. If user exists: CloudWatch log + SNS alert fires
#    Jerry receives email: "Password reset requested for user@example.com"
# 4. Jerry resets password:
kinnoo-server user reset-password --email user@example.com
# Output: Temporary password: Yp3$nQ8wT5!gK2mZ
#         Password expires: 24 hours (user must change on next login)
# 5. Jerry emails user the temporary password
```

---

## Timeline Estimate

| Phase | Duration | Can Overlap With |
|-------|----------|------------------|
| Phase 8 — Client security | 3-4 days | Phase 9 |
| Phase 9 — Server hardening | 5-7 days | Phase 8, Phase 11 |
| Phase 10 — Feature review | 2-3 days | Phase 9, Phase 11 |
| Phase 11 — Documentation | 5-7 days | Phase 8, Phase 9 |
| Phase 12 — IaC | 6-8 days | Phase 11 |
| Phase 13 — CI/CD & open source | 2-3 days | Phase 12 |
| Phase 14 — Beta operations | 2-3 days | Phase 13 |
| Phase 15 — Testing & launch | 3-5 days | — |
| **Total** | **~4-6 weeks** | |

**Critical path:** Phase 9 → Phase 12 → Phase 13 → Phase 14 → Phase 15

---

## Cost Summary (Dev/Beta Monthly)

| Resource | Monthly Cost |
|----------|-------------|
| Cloudflare Pages (frontend) | Free |
| ALB (load balancer) | ~$25 |
| Fargate (1 task, 0.5 vCPU, 1 GB) | ~$37 |
| S3 (registry storage) | ~$5 |
| EFS (persistent storage) | ~$1 |
| CloudWatch (logs, metrics) | ~$5 |
| ECR (Docker images) | ~$1 |
| Secrets Manager (6 secrets) | ~$3 |
| ACM (SSL certificate) | Free |
| SNS (alerts) | ~$0.50 |
| **Total** | **~$78/month** |

No NAT Gateway = $32/month savings vs original estimate.

---

## Post-Beta Roadmap (Deferred Features)

| Feature/Area | When | Rationale |
|-------------|------|-----------|
| PostgreSQL migration | Post-beta sprint 1 | EFS works for single-instance beta |
| Auth0 integration | Post-beta sprint 2+ | Custom auth is secure enough for beta |
| Agent composition | Post-beta v1.2 | Users need single-agent workflows first |
| Framework import adapters | Post-beta v1.1 | Generic import works |
| Verified publisher badges | Post-beta v1.3 | Trust model is signing-based for beta |
| Distributed rate limiting (Redis) | Post-beta scaling | In-memory is fine for 1-2 instances |
| Registry index signing (TUF) | Post-beta v2.0 | Server-side infra, important but not blocking |
| API key management | Post-beta v1.1 | JWT tokens sufficient for beta |
| Admin web dashboard | Post-beta v1.1 | CLI admin is sufficient for beta |
