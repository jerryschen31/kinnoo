# Phase 8+ Accelerated Beta Release Plan (Draft 2)

_Date: April 3, 2026_
_Status: EXPLORATORY — not committed_

This document explores an accelerated path to a kinnoo **public beta** by narrowing scope to security hardening + infrastructure + documentation + registry seeding, and **deferring** complex import support, agent composition, and pressure testing.

---

## 0. Motivation

The current planning-6 roadmap (Phases 6–10) targets ~8-10 weeks to public beta. The bottleneck is breadth: supporting many agent types, framework import adapters, agent composition, and pressure-testing 8 diverse agents. Much of this is important long-term but not essential for a beta launch.

**Core insight:** Kinnoo already has a working end-to-end flow for the most common case — Python/JS/TS one-shot agents with a clear entrypoint and string input. The registry server is built. The signing infrastructure is built. What's needed for beta is:

1. Harden what exists (packaging, registry, install security — client and server)
2. Deploy the registry server on real AWS infrastructure
3. Document everything comprehensively (CLI, manifest spec, security model)
4. Prepare the public open source repo
5. Seed the registry with real agents
6. Ship it

**What this plan cuts:**
- Framework import adapters (feature75) — `kinnoo import` still works generically, just no `--from langchain` etc.
- Agent composition (features 80–83) — powerful but not needed for beta users who run individual agents
- Full pressure testing protocol (features 76–79 as originally scoped) — replaced with targeted validation of your own seed agents
- Trust ecosystem features (GitHub OAuth, verified badges) — post-beta

**What this plan keeps and adds:**
- Security hardening from ubuntu-apt-lessons-learned analysis (client-side AND server-side)
- AWS infrastructure for production registry deployment
- Comprehensive CLI documentation and kinnoo.yaml specification
- Public open source repo preparation (GitHub, PyPI, CI/CD)
- Registry seeding with your own agents as validation
- OpenClaw wrapper support (features 76–85 already at needs-review)

---

## 1. Current State Snapshot

### Completed (59 features)

The core CLI pipeline is fully built and tested:

| Capability | Features | Status |
|-----------|----------|--------|
| Manifest schema + validation | feature1, feature9 | Done |
| Init + framework templates | feature2, feature4, feature21, feature26 | Done (9 frameworks: gemini, chatgpt, claude-chat, pydantic-ai, langgraph, openai-agents, mcp-client, mcp-server, openclaw) |
| Run (local, one-shot, MCP server, no-input, pass-through) | feature3, feature20, feature23 | Done |
| Pack (zip archive, wheels, assets, size reporting) | feature5, feature8, feature17, feature22 | Done |
| Install (from file, from registry, venv, dependencies) | feature6, feature7 | Done |
| Registry (local + remote server + web UI + auth) | feature13, feature28, feature29, feature30, feature43, feature61 | Done |
| Security (signing, checksums, strict mode, input guard, permissions, sandbox, monitoring) | feature15, feature16, feature18, feature39, feature40, feature41, feature71 | Done |
| Import + analyzer | feature19, feature27 | Done |
| Other CLI (inspect, diff, uninstall, preflight, check, lockfile, test foundation) | feature11, feature14, feature69, feature72, feature73, feature74 | Done |

### Needs-Review (19 features)

| Feature | Title | Category |
|---------|-------|----------|
| feature62 | openclaw-skill schema extension | OpenClaw |
| feature69 | kinnoo test foundation | Testing |
| feature70 | Landing page + docs | Docs |
| feature71 | Strict CI enforcement | Security |
| feature72 | Lockfile | Reproducibility |
| feature73 | kinnoo diff | CLI utility |
| feature74 | kinnoo uninstall | CLI utility |
| feature75 | Framework import adapters | Import (defer) |
| feature76–85 | OpenClaw wrapper features | OpenClaw |

### Deprecated (8 features)

features 12, 47, 63–68 — already cut in prior planning rounds.

### Current Version: v0.30.0

### Registry Server Architecture (Already Built)

The registry server (`server/`) is a FastAPI application with the following components:

| Component | File(s) | Status |
|-----------|---------|--------|
| FastAPI app + middleware | `server/app.py`, `server/middleware.py` | Built (dev-ready) |
| Server config (env-driven) | `server/config.py` | Built — reads `REGISTRY_STORAGE_BACKEND`, `REGISTRY_S3_*`, etc. |
| S3 storage backend | `server/storage/s3.py` | Built — uses boto3, supports presigned URLs |
| Local storage backend | `server/storage/local.py` | Built — for dev/test |
| SQLite auth store | `server/storage/sqlite_auth_store.py` | Built — token consumption, tenant slugs, identity mappings |
| User store | `server/storage/user_store.py` | Built — Argon2 password hashing |
| JWT token service | `server/auth/token.py` | Built — HMAC-signed JWT tokens, 60-min TTL |
| Session management | `server/auth/session.py` | Built — cookie-based sessions, 8-hour TTL |
| Publish route | `server/routes/publish.py` | Built — upload validation, SHA-256, metadata indexing |
| Download route | `server/routes/download.py` | Built — presigned URL generation, tenant-scoped access |
| Auth routes (API + web) | `server/routes/auth.py`, `server/routes/web_auth.py` | Built — token issuance, registration, password reset |
| Search + agents routes | `server/routes/search.py`, `server/routes/agents.py` | Built |
| Web UI (SSR templates) | `server/templates/` | Built — Jinja2 templates + static assets |
| Rate limiting | `server/middleware.py` | Built — in-memory, path-based rules |
| Metadata manager | `server/metadata/manager.py` | Built — three-tier JSON index (global → agent → version) |
| Admin bootstrap | `server/bootstrap.py` | Built — env-driven first admin creation |
| Server CLI | `server/cli.py` | Built — `kinnoo-server bootstrap` |
| Server requirements | `server/requirements.txt` | fastapi, uvicorn, boto3, moto[s3], jinja2, argon2-cffi, python-jose |

**Current gaps for production:** The server works end-to-end in dev mode. It has NOT been deployed or tested on real AWS infrastructure. Environment variables use dev-mode defaults (`dev-secret-change-me`, `dev-k1`). Rate limiting is in-memory (not distributed). SQLite is local filesystem (not shared across instances).

---

## 2. Revised Phase Structure

---

### Phase 8 — Client-Side Security Hardening

**Theme:** "Make the package pipeline tamper-evident end-to-end"

**Goal:** Implement the client-side security improvements identified in `notes/ubuntu-apt-lessons-learned.md`. These are contained CLI-side changes that materially strengthen the trust story before beta.

#### Phase 8 - Part 1: Embedded Integrity Manifest

| Feature | Title | Effort | Source |
|---------|-------|--------|--------|
| feature86 | Embedded integrity manifest (`META-INF/integrity.json`) in .kno archives | 1–2 days | ubuntu-apt-lessons-learned §4.3, TL response |

**What it does:** During `kinnoo pack`, compute SHA-256 of every file in the archive and write a `META-INF/integrity.json` manifest inside the ZIP before closing it.

**Technical detail:**

```json
{
  "schema_version": 1,
  "algorithm": "sha256",
  "created_at": "2026-04-03T12:00:00Z",
  "files": {
    "kinnoo.yaml": "a1b2c3d4e5f6...",
    "run.py": "e5f6a7b8c9d0...",
    "requirements.txt": "c9d0e1f2a3b4..."
  }
}
```

**Files modified:** `pack_command.py` (add META-INF generation step after all files are collected but before ZIP is closed), new `integrity.py` module (hash computation + JSON generation).

**Acceptance criteria:**
- `kinnoo pack` produces archives containing `META-INF/integrity.json`
- Every file in the archive (except `META-INF/*`) has its SHA-256 in the manifest
- Old archives without `META-INF/` still install normally (backward compatible)
- Existing tests continue to pass; new tests verify META-INF presence and correctness

#### Phase 8 - Part 2: Embedded Signature

| Feature | Title | Effort | Source |
|---------|-------|--------|--------|
| feature87 | Embedded signature (`META-INF/signature.json`) in .kno archives | 1 day | ubuntu-apt-lessons-learned TL response |

**What it does:** When `kinnoo pack --sign` is used, after writing `META-INF/integrity.json`, sign its canonical JSON content with the Ed25519 key and write `META-INF/signature.json` inside the archive.

**Files modified:** `pack_command.py` (call signing after integrity generation), `integrity.py` (add signing logic reusing `sign_payload()` from `signing.py`).

**Acceptance criteria:**
- `kinnoo pack --sign` produces archives with both `META-INF/integrity.json` AND `META-INF/signature.json`
- `kinnoo pack` (without `--sign`) produces archives with `META-INF/integrity.json` only
- Detached sidecar `.sig` / `.sig.json` files are STILL produced for backward compatibility
- This deprecates the SHA-256 sidecar as the primary integrity mechanism (sidecar kept for backward compat)

#### Phase 8 - Part 3: Install-Time Integrity Verification

| Feature | Title | Effort | Source |
|---------|-------|--------|--------|
| feature88 | Install-time integrity verification (verify META-INF on extract) | 1 day | ubuntu-apt-lessons-learned §4.3 |

**What it does:** During `kinnoo install`, after extracting the ZIP, read `META-INF/integrity.json` and verify every file's SHA-256 before proceeding with installation.

**Verification logic:**
1. Open ZIP → check for `META-INF/integrity.json`
2. If absent → proceed normally (old archive, backward compat)
3. If present → for every non-META-INF file in the ZIP:
   - Compute SHA-256, compare to manifest entry
   - File in ZIP but not in manifest → abort with "unexpected file detected: `<name>`"
   - File in manifest but not in ZIP → abort with "missing file: `<name>`"
   - Hash mismatch → abort with "integrity check failed for `<name>`"
4. If `META-INF/signature.json` exists → verify Ed25519 signature over `integrity.json` content
5. If `--strict` flag is set and `META-INF/signature.json` is absent → abort

**Files modified:** `install_command.py` (add verification step early in install flow), `integrity.py` (add verification functions).

**Acceptance criteria:**
- Tampered archives are rejected with specific file-level error messages
- Archives with injected files (not in manifest) are rejected
- Archives with removed files (in manifest but missing) are rejected
- Old archives without `META-INF/` install normally
- `--strict` requires both integrity.json AND signature.json

---

### Phase 9 — Registry Infrastructure & Server-Side Security

**Theme:** "Deploy and harden the registry server on real infrastructure"

**Goal:** Stand up the kinnoo registry on AWS infrastructure and harden the server for production use. You (the operator) set up the AWS account, VPC, and core resources. The features here cover the server-side configuration and hardening that code/config changes require.

#### Phase 9 - Part 1: AWS Infrastructure Setup (Operator)

This is operator work (you), not SWE agent work. No feature IDs — this is infrastructure provisioning.

| Step | Resource | Details |
|------|----------|---------|
| 1 | AWS Account + IAM | Create production AWS account. Set up IAM user/role for deployment with least-privilege policies. |
| 2 | VPC + Networking | VPC with public/private subnets across 2+ AZs. NAT gateway for private subnet outbound. Security groups: ALB (443 inbound), EC2 (8000 from ALB only), RDS/SQLite (if migrating to RDS, from EC2 only). |
| 3 | S3 Bucket | `kinnoo-registry-prod` bucket. Block all public access. Enable default encryption (AES-256 or KMS). Enable versioning. Lifecycle rules for cost management. CORS policy for presigned URL downloads if needed. |
| 4 | ACM Certificate | Request cert for `registry.kinnoo.dev` (or chosen domain) in ACM. DNS validation via Route 53. |
| 5 | Application Load Balancer | HTTPS listener (port 443) with ACM cert. HTTP listener (port 80) → redirect to HTTPS. Target group pointing to EC2 ASG on port 8000 (uvicorn). Health check: `GET /health` expecting 200. |
| 6 | EC2 Auto Scaling Group | Launch template: Amazon Linux 2023 or Ubuntu 24.04 LTS. Instance type: t3.small or t3.medium to start. User data script: install Python 3.12+, clone/deploy server code, install `server/requirements.txt`, run uvicorn. Min 1, desired 1, max 2 (beta scale). |
| 7 | Route 53 | Hosted zone for `kinnoo.dev`. A-record alias to ALB. |
| 8 | CloudWatch | Basic monitoring: ALB 5xx rate, target response time, healthy host count. Log group for uvicorn stdout/stderr. |
| 9 | Secrets Manager | Store: `REGISTRY_TOKEN_SIGNING_SECRET`, `REGISTRY_SESSION_SIGNING_SECRET`, `REGISTRY_ADMIN_PASSWORD`, `REGISTRY_REGISTER_TOKEN_SECRET`, `REGISTRY_PASSWORD_RESET_TOKEN_SECRET`. EC2 instance role gets `secretsmanager:GetSecretValue` for these secrets. |

**Deliverable:** Running `https://registry.kinnoo.dev/health` returns `{"status": "ok"}`.

#### Phase 9 - Part 2: Server Production Configuration

| Feature | Title | Effort |
|---------|-------|--------|
| feature89 | Production server configuration and deployment hardening | 2–3 days |

**What it does:** Update `server/config.py` and `server/app.py` to be production-ready:

| Change | Current State | Production State |
|--------|--------------|-----------------|
| Token signing secret | `dev-secret-change-me` default | **Required** env var, fail-fast if missing in prod |
| Session signing secret | `dev-session-secret-change-me` default | **Required** env var, fail-fast if missing in prod |
| JWT signing key ID | `dev-k1` default | **Required** env var |
| Admin bootstrap | Creates admin on every startup | Only when `REGISTRY_ADMIN_EMAIL` + `REGISTRY_ADMIN_PASSWORD` are set |
| CORS middleware | Not configured | Allow `kinnoo.dev` origins only (plus localhost for dev) |
| HTTPS enforcement | None | Redirect middleware when behind ALB (trust `X-Forwarded-Proto`) |
| Request ID | UUID per request | Propagate `X-Request-Id` from ALB or generate |
| Max upload size | `REGISTRY_MAX_UPLOAD_MB=50` | Keep 50MB, enforce at both app and ALB level |
| Logging | stdout only | Structured JSON logging (timestamp, request_id, status, latency) |
| Health check | `/health` returns `{"status": "ok"}` | Add readiness probe with S3 connectivity check |

**Files modified:** `server/config.py` (add `is_production` flag, fail-fast for missing secrets), `server/app.py` (CORS, HTTPS redirect, structured logging, enhanced health check), new `server/logging.py` module.

**Acceptance criteria:**
- Server refuses to start in production mode without required secrets
- All requests logged with structured JSON (timestamp, request_id, method, path, status, latency_ms)
- CORS restricts to configured origins
- `/health` returns `{"status": "ok"}` with S3 connectivity check in readiness mode
- Dev mode still works with fallback defaults

#### Phase 9 - Part 3: Server-Side Security Hardening

| Feature | Title | Effort |
|---------|-------|--------|
| feature90 | Server-side upload validation and integrity enforcement | 1–2 days |

**What it does:** Harden the publish endpoint to validate uploaded archives server-side:

| Check | Description |
|-------|-------------|
| Archive format | Verify uploaded file is a valid ZIP; reject malformed archives before storing |
| Manifest presence | Verify `kinnoo.yaml` exists inside archive and parses as valid YAML |
| Manifest name/version | Verify name matches `^[a-z0-9][a-z0-9-]*$` pattern, version is valid semver |
| Size limit | Enforce `REGISTRY_MAX_UPLOAD_MB` before parsing (already done, but add explicit content-length header validation) |
| File count limit | Reject archives with >1000 files (zip bomb protection) |
| Path traversal | Reject archives containing paths with `..` or absolute paths (already partially done by zipfile, make explicit) |
| META-INF integrity | If `META-INF/integrity.json` exists in the upload, verify its hashes match the archive contents before storing |
| Duplicate check | 409 Conflict if `tenant/agent/version` already published (already implemented) |

**Files modified:** `server/routes/publish.py` (add validation layer before storage), potentially new `server/validation.py` module.

**Acceptance criteria:**
- Malformed ZIP uploads return 400 with actionable error
- Archives with path traversal are rejected
- Archives exceeding file count threshold are rejected with specific error
- Archives with META-INF integrity mismatches are rejected
- All validation errors include `request_id` for troubleshooting

#### Phase 9 - Part 4: Rate Limiting and Abuse Protection

| Feature | Title | Effort |
|---------|-------|--------|
| feature91 | Production-grade rate limiting and abuse protections | 1 day |

**What it does:** Upgrade rate limiting from in-memory (single-process) to production-viable:

| Current | Production |
|---------|-----------|
| In-memory `InMemoryRateLimiter` | Still in-memory but with configurable per-endpoint limits via env vars |
| Fixed limits (20 req/min publish, 5 req/min register) | Configurable: `REGISTRY_RATE_LIMIT_PUBLISH`, `REGISTRY_RATE_LIMIT_AUTH`, etc. |
| No IP-based tracking | IP-based tracking using `X-Forwarded-For` from ALB (required) |
| No account-level limits | Per-tenant publish rate limit (e.g., 100 publishes/hour) |

**Note:** For beta with 1–2 instances, in-memory rate limiting is acceptable. Distributed rate limiting (Redis/DynamoDB) is deferred to post-beta scaling.

**Files modified:** `server/middleware.py` (configurable limits, IP extraction from X-Forwarded-For, per-tenant tracking).

**Acceptance criteria:**
- Rate limits are configurable via environment variables
- IP is extracted from `X-Forwarded-For` header (trusted proxy mode)
- Per-tenant publish rate limits are tracked
- Rate-limited responses return 429 with `Retry-After` header

---

### Phase 10 — Review and Land In-Flight Features

**Theme:** "Close out what's already built"

**Goal:** Review and approve the 19 features currently at `needs-review` status. These represent work already done by SWE agents that needs Tech Lead review.

#### Phase 10 - Part 1: Must-Have Features for Beta

| Feature | Title | Priority | Rationale |
|---------|-------|----------|-----------|
| feature71 | Strict CI enforcement | Critical | Enables CI pipelines to reject unsigned packages |
| feature72 | Lockfile | Critical | Reproducible installs are table-stakes |
| feature74 | Uninstall | Critical | Users must be able to cleanly remove installed agents |
| feature70 | Landing page + docs | Critical | Users need a front door to understand what kinnoo is |
| feature73 | Diff | Important | Security review of archive changes between versions |

**Review scope per feature:** Verify implementation matches acceptance criteria, test coverage is adequate, no regressions in existing test suite.

#### Phase 10 - Part 2: OpenClaw Wrapper Features

| Feature | Title | Priority |
|---------|-------|----------|
| feature62 | OpenClaw-skill schema extension | Important |
| feature76 | OpenClaw preflight wrapper | Important |
| feature77 | OpenClaw init wrapper | Important |
| feature78 | OpenClaw import wrapper | Important |
| feature79 | OpenClaw workspace pack | Important |
| feature80 | OpenClaw install wrapper | Important |
| feature81 | OpenClaw run wrapper | Important |
| feature82 | OpenClaw logs wrapper | Important |
| feature83 | OpenClaw skill install | Important |
| feature84 | OpenClaw skill search | Important |
| feature85 | Deprecate OpenClaw bridge features 62–67 | Important |

**Decision:** Review and land if they pass. If significant issues surface, ship beta without OpenClaw wrappers and add in a rapid v1.0.1 follow-up.

#### Phase 10 - Part 3: Deferred Features (Explicitly Not Reviewed for Beta)

| Feature | Title | Decision | Rationale |
|---------|-------|----------|-----------|
| feature75 | Framework import adapters | Skip review | This is the import complexity we want to defer. Code stays, just not tested/reviewed for beta. |
| feature69 | kinnoo test foundation | Skip review | Nice to have but not blocking. Agents can use their own test runners. |

**Note:** These features remain at `needs-review` status. The code stays in the repo. They are not removed, just not promoted to `completed` for beta. Documentation explicitly notes them as "experimental / not fully tested."

---

### Phase 11 — Comprehensive Documentation

**Theme:** "Document everything a user or contributor needs to know"

**Goal:** Write comprehensive documentation that serves as both the user guide and the technical reference. Each CLI command gets its own section. The `kinnoo.yaml` specification becomes a standalone, precise document.

#### Phase 11 - Part 1: kinnoo.yaml Specification

| Feature | Title | Effort |
|---------|-------|--------|
| feature92 | kinnoo.yaml specification document (public-facing) | 1–2 days |

**Deliverable:** `docs/kinnoo-yaml-spec.md` — a clean, standalone specification document. NOT the current `manifest-schema-reference.md` (which is an internal reference with feature notes mixed in).

**Sections:**

| Section | Content |
|---------|---------|
| Overview | What `kinnoo.yaml` is, where it lives, why it exists |
| Required Fields | `name`, `version`, `entrypoint`, `runtime.language`, `runtime.version`, `runtime.type`, `dependencies`, `inputs.type`, `outputs.type` — each with type, constraints, and example |
| Runtime Types | `one-shot` (start → process → exit), `mcp-server` (long-running MCP server), `daemon` (long-running Node.js process) — runtime contract per type |
| Optional Metadata | `description`, `author`, `license`, `framework`, `model` |
| Environment Variables | `env_vars` — declaration, runtime resolution order (process → .env → prompt), security contract (never logged) |
| Input/Output Types | `text`, `string`, `json`, `file` — when to use each, how the CLI interprets them |
| Permissions | `permissions.network`, `permissions.filesystem_scope`, `permissions.shell`, `permissions.browser`, `permissions.env_access` — each value explained with examples |
| Assets | `assets.paths`, `assets.bundle`, `assets.max_bundle_size_mb` — bundling behavior, size thresholds |
| State Dirs | `state_dirs` — mutable state snapshots, exclude patterns, install overwrite behavior |
| Services | `services` — external service declarations for health checks (MCP server, database, API, local process) |
| Provenance | `provenance.source_registry`, `provenance.source_slug`, `provenance.source_url`, `provenance.source_version` — lineage tracking |
| Tests Integration | `tests_file`, `tests_version`, `tests` — how to declare tests inline or reference external test file |
| OpenClaw Fields | `type: openclaw-skill`, `framework: openclaw`, `channels`, `skills`, `state_dirs` — when and how to use them |
| Complete Examples | 5+ annotated examples: Python one-shot, MCP server, JS/TS agent, OpenClaw daemon, agent with assets + permissions |
| Full Reference Table | All fields in one table: field name, required/optional, type, constraints, default value |
| Validation Rules | Which combinations are enforced by the validator (e.g., `type: openclaw-skill` requires `framework: openclaw`, `runtime.language: nodejs`, `runtime.type: daemon`) |

**Acceptance criteria:**
- A new user can read this document and write a valid `kinnoo.yaml` for their agent without looking at any other file
- Every field in `schema.py` REQUIRED_FIELDS, OPTIONAL_FIELDS, and PERMISSIONS_KEYS is documented
- Every validation rule in `validator.py` has a corresponding explanation
- Document includes at least 5 complete, working examples

#### Phase 11 - Part 2: CLI Command Reference

| Feature | Title | Effort |
|---------|-------|--------|
| feature93 | Comprehensive CLI command reference document | 2–3 days |

**Deliverable:** `docs/cli-reference.md` — every CLI command documented with synopsis, description, all flags/options, examples, exit codes, and error behavior.

**Commands to document (21 commands total):**

| Command | Category | Synopsis |
|---------|----------|----------|
| `kinnoo init` | Agent Lifecycle | `kinnoo init [agent_name] [--framework FRAMEWORK] [--language LANG]` |
| `kinnoo run` | Agent Lifecycle | `kinnoo run <agent_dir> [input] [--preflight] [--no-guard] [--json-input JSON] [--json-file PATH] [--sandbox] [--dry-run] [--max-seconds N] [--max-cpu-seconds N] [--max-memory-mb N] [--thinking LEVEL] [--json]` |
| `kinnoo test` | Agent Lifecycle | `kinnoo test <agent_dir> [--tests-file PATH] [--validate-only] [--json]` |
| `kinnoo pack` | Packaging | `kinnoo pack <agent_dir> [--bump LEVEL] [--sign] [--signing-key PATH] [--preflight]` |
| `kinnoo inspect` | Packaging | `kinnoo inspect <target> [--full] [--raw] [--update TARGET OLD_KEY NEW_VALUE] [--skip-warnings]` |
| `kinnoo import` | Packaging | `kinnoo import <path> [--from FRAMEWORK] [--source SOURCE]` |
| `kinnoo check` | Packaging | `kinnoo check <target>` |
| `kinnoo diff` | Packaging | `kinnoo diff <archive_a> <archive_b> [--json]` |
| `kinnoo install` | Install | `kinnoo install <agent[==version]> [target_dir] [--yes] [--strict] [--frozen] [--local\|--remote] [--accept-permissions] [--allow-unverified-publisher] [--state-overwrite] [--allow-vulnerable] [--ignore-scripts] [--openclaw-min-version VER] [--openclaw-skill SKILL]` |
| `kinnoo uninstall` | Install | `kinnoo uninstall <agent_name>` |
| `kinnoo publish` | Registry | `kinnoo publish <target> [--local\|--remote] [--pack] [--bump LEVEL] [--strict] [--sign] [--signing-key PATH]` |
| `kinnoo list` | Registry | `kinnoo list [--local\|--remote]` |
| `kinnoo search` | Registry | `kinnoo search <query> [--local\|--remote] [--openclaw-skills] [--json]` |
| `kinnoo sync` | Registry | `kinnoo sync <source> [--full] [--since DATE] [--local\|--remote]` |
| `kinnoo login` | Auth | `kinnoo login [--email EMAIL] [--password PASS] [--registry URL] [--tenant-slug SLUG]` |
| `kinnoo logout` | Auth | `kinnoo logout` |
| `kinnoo keygen` | Security | `kinnoo keygen [--private-key PATH] [--public-key PATH]` |
| `kinnoo stop` | Daemon | `kinnoo stop <agent_dir>` |
| `kinnoo attach` | Daemon | `kinnoo attach <agent_dir>` |
| `kinnoo logs` | Daemon | `kinnoo logs <agent_dir> [--daemon openclaw] [--follow] [--json] [--tail N]` |
| `kinnoo --version` | Meta | Show version number |

**Per-command documentation structure:**
```
### kinnoo <command>

**Synopsis:**   command with all arguments and flags
**Description:** What the command does and when to use it
**Arguments:**  Each positional argument with type and description
**Options:**    Each flag with type, default, and description
**Examples:**   2-4 concrete usage examples with expected output
**Exit Codes:** 0 = success, 1 = error, 2 = usage error
**Errors:**     Common error scenarios and how to resolve them
**See Also:**   Related commands
```

**Acceptance criteria:**
- Every command shown in `kinnoo --help` has a complete reference entry
- Every flag/option matches the argparse definitions in `cli.py`
- At least 2 examples per command
- Common error scenarios documented with resolution guidance

#### Phase 11 - Part 3: Security Model Document

| Feature | Title | Effort |
|---------|-------|--------|
| feature94 | Security model document | 1 day |

**Deliverable:** `docs/security-model.md`

**Sections:**

| Section | Content |
|---------|---------|
| Threat Model | What kinnoo protects against: supply chain attacks, tampered archives, credential leakage, injection |
| Ed25519 Signing | Key generation (`kinnoo keygen`), signing workflow (`kinnoo pack --sign`), verification (`kinnoo install --strict`) |
| Archive Integrity | META-INF/integrity.json (per-file SHA-256), META-INF/signature.json (Ed25519 over integrity manifest), backward compatibility with sidecar `.sha256` files |
| Strict Mode | What `--strict` enforces on install and publish. CI integration pattern. |
| Permission Declarations | `permissions` object in kinnoo.yaml, install-time consent, sandbox enforcement |
| Input Guard | Injection pattern detection, `--no-guard` for CI, what patterns are checked |
| Runtime Sandbox | `--sandbox` mode, permission policy enforcement, violation logging |
| Runtime Monitor | Resource limits (`--max-seconds`, `--max-cpu-seconds`, `--max-memory-mb`), behavioral anomaly detection |
| Lockfile | `kinnoo.lock.yaml` format, `--frozen` install, drift detection |
| Credential Handling | `env_vars` resolution, non-disclosure invariant, `.env` loading, no secrets in logs |
| Comparison | Brief comparison to JAR signing, APT (dpkg/apt), PyPI (PEP 458/TUF), npm (sigstore) — positioning kinnoo's approach |

#### Phase 11 - Part 4: Getting Started & Registry Guide

| Feature | Title | Effort |
|---------|-------|--------|
| feature95 | Getting started guide and registry guide | 1 day |

**Deliverables:**

**`docs/getting-started.md`:**
- Prerequisites (Python 3.10+, Node.js 20+ for JS/TS agents)
- Installation (`pip install kinnoo`)
- Quick-start workflow with a concrete Python agent: `init → run → pack → install → publish`
- Quick-start workflow with a JavaScript agent: `init --language js → run → pack → install`
- Environment setup (API keys, `.env` file)

**`docs/registry-guide.md`:**
- What the registry is and how it works
- Creating an account: `kinnoo login --registry https://registry.kinnoo.dev`
- Publishing your first agent: `kinnoo publish my-agent --remote`
- Installing from the registry: `kinnoo install my-agent --remote`
- Searching for agents: `kinnoo search "keyword" --remote`
- Tenant namespaces and scoping
- Auth state management (where tokens are stored, `kinnoo logout`)
- Environment variables: `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`

#### Phase 11 - Part 5: README and Supported Agents

| Feature | Title | Effort |
|---------|-------|--------|
| feature96 | README rewrite and supported agents document | 0.5 day |

**Deliverables:**

**`README.md` rewrite:**
- Clear "Beta — feedback welcome" badge
- One-paragraph description
- Install instructions
- 30-second quick-start (init → run → pack → install)
- Link to full docs
- Supported agent types summary
- Link to contributing guide
- License

**`docs/supported-agents.md`:**
- What agent types kinnoo supports (Python/JS/TS one-shot, MCP server, MCP client, OpenClaw daemon)
- What "supported" means practically (init template, run contract, pack/install works)
- What is NOT supported yet (agent composition, framework-specific import, UI agents)
- Framework compatibility matrix (9 init templates)
- Manual manifest authoring guide for agents without a matching template

---

### Phase 12 — Open Source Repo Preparation

**Theme:** "Get the public repo ready for external contributors and users"

**Goal:** Prepare a public-facing GitHub repository, CI/CD pipeline, PyPI publishing, and contributor documentation.

#### Phase 12 - Part 1: Public Repository Setup

| Feature | Title | Effort |
|---------|-------|--------|
| feature97 | Public GitHub repository preparation | 1–2 days |

**Checklist:**

| Item | Detail |
|------|--------|
| Repository creation | Create `kinnoo/kinnoo` (or `kinnoo-dev/kinnoo`) public repo on GitHub |
| `.gitignore` audit | Ensure no secrets, `.env` files, build artifacts, `__pycache__`, `.registry-storage/` are committed. Verify against current `.gitignore`. |
| License | MIT license already present. Verify `LICENSE` file is complete and correct. |
| `pyproject.toml` audit | Ensure `[project]` metadata is complete: name, version, description, authors, license, classifiers, requires-python, dependencies, project-urls, scripts entry point |
| `CONTRIBUTING.md` | How to set up local dev environment, run tests, coding standards, PR process, code of conduct reference |
| `CODE_OF_CONDUCT.md` | Contributor Covenant or similar |
| Issue templates | Bug report template, feature request template |
| PR template | Checklist: tests pass, docs updated, no secrets committed |
| Branch protection | `main` branch: require PR reviews, require status checks (CI), no force push |
| GitHub Actions CI | See Part 2 below |

**Secrets audit before going public:**
- Grep entire repo for hardcoded secrets, API keys, passwords
- Verify all `dev-secret-change-me` and `dev-k1` defaults are ONLY used when `is_production=False`
- Verify server tests use mock/fake credentials
- Verify `.env` files are in `.gitignore`
- Check git history for accidentally committed secrets (run `trufflehog` or `gitleaks`)

#### Phase 12 - Part 2: CI/CD Pipeline

| Feature | Title | Effort |
|---------|-------|--------|
| feature98 | GitHub Actions CI/CD pipeline | 1 day |

**`.github/workflows/ci.yml`:**

```yaml
# Triggered on: push to main, pull requests
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - checkout
      - setup-python
      - pip install -e ".[dev]"
      - python -m pytest tests/ -v --tb=short
      - python scripts/validate_project_manifests.py

  lint:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-python
      - ruff check src/ tests/
      - ruff format --check src/ tests/
```

**`.github/workflows/publish.yml`:**

```yaml
# Triggered on: release published
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-python
      - pip install build twine
      - python -m build
      - twine upload dist/*
    environment: pypi
    # Uses PYPI_API_TOKEN secret
```

#### Phase 12 - Part 3: PyPI Publishing Setup

| Feature | Title | Effort |
|---------|-------|--------|
| feature99 | PyPI package publishing configuration | 0.5 day |

**Checklist:**

| Item | Detail |
|------|--------|
| PyPI account | Create `kinnoo` project on PyPI. Reserve the name. |
| API token | Create scoped token for `kinnoo` package. Store as `PYPI_API_TOKEN` GitHub secret. |
| `pyproject.toml` review | Verify classifiers, description, project-urls, readme, scripts.kinnoo entry point |
| Test upload | Upload to TestPyPI first. Verify `pip install --index-url https://test.pypi.org/simple/ kinnoo` works. |
| Version strategy | Confirm: beta release will be `1.0.0b1` or `0.30.0`? Decide versioning convention. |

---

### Phase 13 — Registry Seeding + Validation

**Theme:** "Prove it works with real agents, then open the doors"

**Goal:** Use the agents you're currently building as both seed content and validation. Every seed agent goes through the full lifecycle against the production registry: init/import → check → pack → publish → install → run.

| Step | Action | Outcome |
|------|--------|---------|
| 1 | Identify 3–5 agents you're already building | Seed agent list |
| 2 | Run each agent through the full lifecycle against the PRODUCTION registry (`registry.kinnoo.dev`) | Bugs found and fixed |
| 3 | Document each agent with description, README in the registry web UI | Registry has real, discoverable content |
| 4 | Fix any bugs discovered during seeding | Battle-hardened flow |
| 5 | Verify `kinnoo search` and `kinnoo list --remote` show seed agents correctly | Search/discovery works |
| 6 | Verify install from registry works for each seed agent: `kinnoo install <agent> --remote` → extracted agent runs correctly | Full round-trip validated |

**What counts as a "seed agent":**
- Must be a real agent you've built and use, not a synthetic test fixture
- Must cover at least 2 of: Python one-shot, MCP server/client, OpenClaw skill
- Must include at least 1 agent with non-trivial dependencies (proves venv/offline install works)

**Estimated effort:** 2–3 days (you're already building these agents — this is packaging and publishing them, not new development)

---

### Phase 14 — Production Launch

**Theme:** "Flip the switch"

#### Phase 14 - Part 1: Pre-Launch Checklist

| Step | Action | Effort |
|------|--------|--------|
| 1 | Run full test suite against latest code on CI (all Python versions) | 0.5 day |
| 2 | Run `python scripts/validate_project_manifests.py` — zero errors | 0.5 hour |
| 3 | Verify all must-have features for beta are status `completed` | 0.5 hour |
| 4 | Verify production registry is operational (health check, publish, install round-trip) | 0.5 day |
| 5 | Verify seed agents are discoverable and installable from production registry | 0.5 hour |
| 6 | Verify `pip install kinnoo` from PyPI (or TestPyPI) works | 0.5 hour |
| 7 | Review all documentation one final time | 0.5 day |
| 8 | Verify no secrets in git history (`gitleaks` or `trufflehog` scan) | 0.5 hour |

#### Phase 14 - Part 2: Launch

| Step | Action | Effort |
|------|--------|--------|
| 1 | Create GitHub release with tag `v1.0.0-beta.1` and release notes | 0.5 day |
| 2 | Publish to PyPI: `python -m build && twine upload dist/*` | 0.5 hour |
| 3 | Update README with beta badge and install instructions | 0.5 hour |
| 4 | Announce beta: X/Twitter, Hacker News, relevant Discord/Slack communities, Reddit r/MachineLearning, r/LocalLLaMA | 0.5 day |

---

## 3. What Gets Deferred to Post-Beta

These features are valuable but don't block a useful beta:

| Feature/Area | Why Defer | When |
|-------------|-----------|------|
| **Framework import adapters** (feature75) | Complex, diminishing returns for beta. Generic import works. | Post-beta v1.1 |
| **Agent composition** (features 80–83 in planning-6) | Powerful but users need to adopt single-agent workflows first | Post-beta v1.2 |
| **Full pressure testing** (features 76–79 as originally scoped in planning-6) | Replaced by seed-agent validation | Post-beta ongoing |
| **GitHub OAuth + verified badges** (planning-6 features 84–85) | Trust signals for strangers. Beta is for early adopters who trust you directly. | Post-beta v1.3 |
| **kinnoo update command** | Nice to have, users can `pip install --upgrade kinnoo` | Post-beta |
| **Registry index signing** (root.json, targets.json, TUF alignment) | Server-side infrastructure. Important but not blocking for a small beta registry. | Post-beta v1.3–v2.0 |
| **kinnoo test foundation** (feature69) | Not blocking — agents can use their own test runners | Post-beta v1.1 |
| **Distributed rate limiting** (Redis/DynamoDB) | In-memory is fine for a 1-2 instance beta | Post-beta scaling |
| **Database migration** (SQLite → RDS/Aurora) | SQLite works for a single-instance beta; migrate when scaling demands it | Post-beta |

---

## 4. Timeline Estimate

| Phase | Duration | Parallel? | Owner |
|-------|----------|-----------|-------|
| Phase 8 — Client-side security hardening | 3–4 days | — | SWE agent |
| Phase 9 - Part 1 — AWS infrastructure setup | 2–3 days | Can overlap with Phase 8 | You (operator) |
| Phase 9 - Parts 2–4 — Server hardening | 3–4 days | After Part 1 infra is up | SWE agent |
| Phase 10 — Review in-flight features | 2–3 days | Can overlap with Phase 9 | Tech Lead |
| Phase 11 — Documentation | 4–6 days | Can start during Phase 8/9 | SWE agent |
| Phase 12 — Open source prep | 2–3 days | Can start during Phase 11 | You + SWE agent |
| Phase 13 — Registry seeding | 2–3 days | After Phase 9, 10 | You |
| Phase 14 — Launch | 1–2 days | After Phase 13 | You |

**Total: ~3–5 weeks to beta** (vs ~8-10 weeks in planning-6)

**Critical path:** Phase 9 Part 1 (AWS infra) → Phase 9 Parts 2–4 (server hardening) → Phase 13 (seeding) → Phase 14 (launch).

**Parallelization opportunities:**
- Phase 8 (client security) + Phase 9 Part 1 (AWS infra) run in parallel
- Phase 11 (documentation) can start as soon as Phase 8 is in progress
- Phase 10 (feature review) overlaps with Phase 9 server work
- Phase 12 (open source prep) overlaps with Phase 11

---

## 5. What the Beta User Gets

A beta user who `pip install kinnoo` gets:

**CLI commands (all working):**
- `kinnoo init [agent_name] [--framework FRAMEWORK] [--language LANG]` — scaffold agent (9 frameworks: gemini, chatgpt, claude-chat, pydantic-ai, langgraph, openai-agents, mcp-client, mcp-server, openclaw)
- `kinnoo run <agent_dir> [input] [--preflight] [--sandbox] [--dry-run] [--json-input] [--json-file] [--no-guard] [--max-seconds N]` — execute agent locally
- `kinnoo test <agent_dir> [--validate-only] [--json]` — run declarative tests
- `kinnoo pack <agent_dir> [--sign] [--signing-key PATH] [--bump LEVEL] [--preflight]` — package into .kno with integrity manifest + optional signing
- `kinnoo import <path> [--from FRAMEWORK]` — onboard existing agent (generic analysis)
- `kinnoo check <target>` — combined compatibility checks
- `kinnoo inspect <target> [--full] [--raw]` — view manifest metadata
- `kinnoo diff <archive_a> <archive_b> [--json]` — compare two archives
- `kinnoo install <agent[==version]> [target_dir] [--strict] [--frozen] [--local|--remote] [--yes]` — install from file or registry with integrity verification
- `kinnoo uninstall <agent_name>` — clean removal with lockfile update
- `kinnoo publish <target> [--local|--remote] [--pack] [--bump LEVEL] [--strict] [--sign]` — push to registry
- `kinnoo list [--local|--remote]` / `kinnoo search <query> [--local|--remote]` — discover agents
- `kinnoo login` / `kinnoo logout` — registry auth
- `kinnoo keygen` — generate Ed25519 signing keypair
- `kinnoo sync <source>` — sync external agent sources
- `kinnoo stop` / `kinnoo attach` / `kinnoo logs` — daemon agent management

**Security features (all working):**
- Ed25519 signing + detached AND embedded signature verification
- SHA-256 checksums (sidecar + embedded META-INF/integrity.json)
- Per-file integrity manifest inside archives (self-verifying)
- Strict CI mode (`--strict` rejects unsigned/untampered packages)
- Permission declarations + install-time consent
- Input safety guard (injection pattern detection)
- Runtime sandbox (`--sandbox`) + behavioral monitoring
- Preflight checks
- Lockfile (`kinnoo.lock.yaml`) for reproducible installs (`--frozen`)
- Resource limits (`--max-seconds`, `--max-cpu-seconds`, `--max-memory-mb`)

**Production registry at `registry.kinnoo.dev`:**
- Account creation and authentication
- Publish/install/search/list against remote registry
- Tenant-scoped namespaces
- Web UI for browsing agents
- Pre-seeded with 3–5 real agents

**Comprehensive documentation:**
- `kinnoo.yaml` specification with all fields and validation rules
- CLI command reference for all 21 commands
- Security model document
- Getting started guide with concrete examples
- Registry guide

**Supported agent types:**
- Python one-shot agents (any framework, clear entrypoint, string input)
- JavaScript/TypeScript one-shot agents
- MCP server agents (long-running)
- MCP client agent templates
- OpenClaw daemon agents and skills

**Not supported in beta (clearly documented):**
- Agent composition / dependency chains
- Framework-specific import (`kinnoo import --from langchain` — code exists but not fully tested)
- UI-based agents
- Verified publisher badges / GitHub OAuth
- Distributed rate limiting / horizontal scaling

---

## 6. Risks

| Risk | Mitigation |
|------|-----------|
| Beta users hit import issues with complex agents | Document scope clearly. Generic import still works. Provide manual kinnoo.yaml authoring guide in spec document. |
| Registry is empty / feels dead | Seed with 3–5 real agents before announcement. Quality > quantity. |
| Security hardening introduces regressions in pack/install | Full regression suite runs after each security feature. Backward-compatible META-INF (old archives without META-INF still install fine). |
| Users want agent composition immediately | Document it as "coming in v1.2" with a clear roadmap. Not a beta expectation. |
| OpenClaw wrapper features have issues at review | They're already at needs-review — worst case, ship beta without OpenClaw and add in v1.0.1 rapid follow-up. |
| AWS infrastructure takes longer than expected | VPC/ALB/ASG are well-understood patterns. Start with minimal infra (1 instance). |
| SQLite doesn't scale past beta | Acceptable for initial beta with low traffic. Migrate to RDS when needed. |
| Server security flaws found during hardening | Scope hardening to validation + config + logging. Don't expand scope to distributed infra (post-beta). |
| PyPI name squatting | Reserve the `kinnoo` package name on PyPI early in Phase 12. |
| Git history contains secrets | Run `gitleaks` scan before making repo public. If secrets found, rewrite history or create fresh public repo with squashed history. |

---

## 7. Feature ID Mapping

New features introduced in this plan:

| Feature ID | Title | Phase | Maps to |
|-----------|-------|-------|---------|
| feature86 | Embedded integrity manifest (META-INF/integrity.json) | Phase 8 - Part 1 | ubuntu-apt-lessons-learned §4.3 |
| feature87 | Embedded signature (META-INF/signature.json) | Phase 8 - Part 2 | ubuntu-apt-lessons-learned TL Response |
| feature88 | Install-time integrity verification | Phase 8 - Part 3 | ubuntu-apt-lessons-learned §4.3 |
| feature89 | Production server configuration and deployment hardening | Phase 9 - Part 2 | (new) |
| feature90 | Server-side upload validation and integrity enforcement | Phase 9 - Part 3 | (new) |
| feature91 | Production-grade rate limiting and abuse protections | Phase 9 - Part 4 | (new) |
| feature92 | kinnoo.yaml specification document | Phase 11 - Part 1 | (new) |
| feature93 | Comprehensive CLI command reference document | Phase 11 - Part 2 | (new) |
| feature94 | Security model document | Phase 11 - Part 3 | (new) |
| feature95 | Getting started guide and registry guide | Phase 11 - Part 4 | (new) |
| feature96 | README rewrite and supported agents document | Phase 11 - Part 5 | (new) |
| feature97 | Public GitHub repository preparation | Phase 12 - Part 1 | (new) |
| feature98 | GitHub Actions CI/CD pipeline | Phase 12 - Part 2 | (new) |
| feature99 | PyPI package publishing configuration | Phase 12 - Part 3 | (new) |

> Note: feature86–99 IDs are tentative. Adjust at implementation time if conflicts arise.

---

## 8. Summary: Planning-6 vs. This Plan

| Aspect | Planning-6 | This Plan |
|--------|-----------|-----------|
| Timeline to beta | ~8-10 weeks | ~3-5 weeks |
| Features before launch | ~30 (Phases 6–9) | ~14 new + review 19 in-flight |
| Agent composition | In scope (Phase 8) | Deferred |
| Framework import adapters | In scope (Phase 6) | Deferred (code stays, not reviewed) |
| Pressure testing | 8 agents, formal protocol | Organic via seed agents |
| Client security hardening | Post-launch (Phase 9+) | Pre-launch (Phase 8) |
| Server security hardening | Not explicitly planned | Pre-launch (Phase 9) |
| AWS infrastructure | Not explicitly planned | Pre-launch (Phase 9) |
| Documentation | Landing page only | Comprehensive: manifest spec, CLI ref, security model, guides (Phase 11) |
| Open source repo | Not explicitly planned | Pre-launch (Phase 12) |
| Registry seeding | 10-20 agents (Phase 9) | 3-5 agents (your own) against production registry |
| Trust ecosystem | GitHub OAuth, badges (Phase 9) | Deferred |
| TUF/registry signing | Deferred | Deferred (post-beta) |
| PyPI publishing | Not planned | Pre-launch (Phase 12) |

**The core trade-off:** Ship a focused, comprehensively-documented, security-hardened beta on production infrastructure with real agents in it, rather than waiting for breadth of features that most early adopters won't use on day one.
