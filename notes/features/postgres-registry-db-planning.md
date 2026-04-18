# Postgres Agent Registry Database — Build-Out Planning

Date: 2026-04-18
Scope: Planning only. Answers three questions from the human operator before handing off to SWE agent.

---

## Question 1: Is the current spec enough? What else does an agent need?

**Short answer: No, the spec is directionally correct but missing several concrete details an SWE agent would need to produce a working implementation without guesswork.**

### What the current spec covers (sufficient)

- Tech stack: SQLAlchemy 2.0, Alembic, asyncpg (confirmed by `db.rules.md`)
- Target directory: `server/database/`
- Pattern mandates: UUID7 PKs, audit timestamps, async-first, repository pattern, JSONB for flexible metadata
- High-level entities: agents, versions, users, tenants, audit
- kinnoo-server CLI: admin commands for table/row/column CRUD
- That JSON metadata store and SQLite auth store are being replaced

### What the spec is missing (the SWE agent would need these)

#### A. Concrete Entity-Relationship Model

The spec says "agents, versions, users, tenants, audit" but doesn't define:

1. **Which fields on each table** — the SWE agent needs an explicit column list, types, and constraints for every table. Without this, they'll reverse-engineer from the JSON files, which is error-prone because some JSON fields are storage artifacts (e.g., `storage_keys`, `schema_version`) that shouldn't be DB columns, and some missing fields should be added (e.g., `download_count`, `deprecated_at`).

2. **Relationships and foreign keys** — e.g., does `agent_versions.agent_id` FK to `agents.id`? Does `agents.tenant_id` FK to `tenants.id`? Do we want cascade deletes?

3. **Indexes** — `db.rules.md` says "add indexes to frequently searched fields" but doesn't say which. The agent needs to know: search is by `agent_slug`, `tenant_slug`, `description` text; listing is sorted by `updated_at`; downloads filter by `tenant_slug + agent_slug + version`.

4. **The `api_keys` table** — with Kinde handling auth, you still need long-lived API keys for CI/CD headless `kinnoo publish` from pipelines. This table isn't mentioned anywhere.

5. **The `download_events` table** — currently there's no download tracking. A production registry needs this for popularity sorting, abuse detection, and usage analytics.

#### B. The Migration Strategy from Current State to Postgres

The spec says "data migration path documented" but doesn't specify:

- **How to handle the dual-write period** — will there be a feature flag toggling between JSON-backed MetadataManager and Postgres-backed repository? Or is it a hard cutover?
- **Which JSON data needs migrating** — all VersionMetadata documents, all User JSON files, all Tenant JSON files, the SQLite auth tables?
- **Are we preserving the `MetadataManager` interface?** — currently all routes call `metadata_manager.get_version_metadata(...)`. Do we want a Postgres-backed implementation of the same interface, or do we want routes to call new repository classes directly?

**Recommendation:** Keep the `MetadataManager` interface and create a `PostgresMetadataManager` that implements the same public methods. This is the lowest-risk migration path — routes don't change, you just swap the backend. Then deprecate the file-backed manager.

#### C. How `kinnoo-server` CLI Commands Map to the DB

The spec says CLI should "create or delete tables; add, modify, delete rows; add, modify, delete columns." This is extremely broad and essentially describes a general-purpose DB admin tool. The SWE agent needs clarity on:

- **Is this meant to be a raw SQL admin shell?** If so, the agent just needs to write a `connect registry-db` command that drops into a psql-like interface. Simple.
- **Or is it meant to be domain-aware admin commands?** e.g., `kinnoo-server agent list`, `kinnoo-server tenant create`, `kinnoo-server user set-role`. These are more useful but a much larger scope.
- **What does `kinnoo-server connect registry-db` actually do?** Start an interactive psql session? Start a Python REPL with the session pre-connected? Print the connection string?

**Recommendation:** Two modes:
1. `kinnoo-server connect registry-db` — prints the connection string and optionally opens `psql` directly (for raw admin work).
2. Domain-aware commands: `kinnoo-server db migrate` (run Alembic), `kinnoo-server db seed` (insert example data), `kinnoo-server tenant list`, `kinnoo-server tenant create <slug>`, `kinnoo-server user list`, `kinnoo-server user set-role <email> <role>`.

#### D. Testing Strategy

The spec says "all existing server tests pass against Postgres" but doesn't specify:

- **Test isolation method** — transaction rollback per test? Separate test database? Truncate tables between tests?
- **How to run Postgres in CI** — Docker service container in GitHub Actions? Embedded Postgres?
- **Test fixtures** — who owns the factory functions for creating test users, tenants, agents?

**Recommendation:** 
- Use `pytest-asyncio` + transaction rollback per test (each test runs in a transaction that gets rolled back).
- GitHub Actions: `services: postgres:` container with a test database.
- Test fixtures live in `server/tests/conftest.py` using async session factories.

#### E. Connection Management

The spec doesn't cover:

- **Connection pooling** — asyncpg pool size, overflow settings, recycling
- **Health check** — how does the `/health` endpoint verify DB connectivity?
- **Startup behavior** — does the server refuse to start if Postgres is unreachable? Or does it start and return 503s?
- **Environment variables** — what's the connection string env var name? `DATABASE_URL`? `REGISTRY_DATABASE_URL`?

**Recommendation:**
- Env var: `REGISTRY_DATABASE_URL` (follows existing `REGISTRY_*` naming convention in `server/config.py`)
- Pool: `pool_size=5`, `max_overflow=10` (sensible defaults, configurable via env)
- Server refuses to start if initial connection fails (fail-fast); health endpoint includes DB ping.

---

## Question 2: What is currently built? (Current data layer audit)

### Storage Layer 1: Object Storage (S3 / Local filesystem)

**What it stores:** `.kno` archive blobs (the actual agent packages)

**Interface:** `StorageBackend` protocol in `server/storage/base.py`
- `put_object(key, data, content_type)`
- `get_object(key) -> bytes`
- `list_objects(prefix) -> list[str]`
- `delete_object(key)`
- `generate_presigned_url(key, expires_in_seconds) -> str`

**Implementations:** `server/storage/local.py`, `server/storage/mock_s3.py`, `server/storage/s3.py`

**Verdict:** ✅ **Keep as-is.** Archive blobs belong in S3, not Postgres. The `StorageBackend` protocol is clean and should continue to handle blob storage. Only the **metadata about** these objects moves to Postgres.

### Storage Layer 2: JSON Metadata (the "database" being replaced)

**What it stores:** Agent registry metadata — who published what, which versions exist, manifest contents, integrity checksums.

**Interface:** `MetadataManager` in `server/metadata/manager.py`

**Data model** (via `server/metadata/models.py`):

| Dataclass | What it represents | Storage key pattern |
|---|---|---|
| `VersionMetadata` | One tenant/agent/version record | `metadata/tenants/{t}/agents/{a}/versions/{v}.v1.json` |
| `AgentIndex` | All versions of one agent | `metadata/tenants/{t}/agents/{a}/index.v1.json` |
| `GlobalIndex` | All tenants and their agents (search/list) | `metadata/global/index.v1.json` |

**Key fields on `VersionMetadata`:**
- `tenant_slug`, `agent_slug`, `version` (composite natural key)
- `visibility` (public/private)
- `manifest` (full kinnoo.yaml dict — name, version, runtime, entrypoint, description, author, etc.)
- `storage_keys` (S3 key for archive, signature)
- `integrity` (SHA-256 checksums)
- `publisher` (who published it — currently `{user_id, tenant_slug}`)
- `security_status`, `security_report`
- `created_at`, `updated_at` (ISO timestamps)

**Problems with current approach:**
- `GlobalIndex` is a single JSON document that every search/list/publish must read/write → concurrency bottleneck
- `_update_global_index_atomic` does optimistic retry but can still lose writes under concurrent publishes
- No query capability — search loads the entire global index into memory and loops
- No indexes, no pagination at the storage level
- Agent deletion not implemented (no way to remove a version from the index cleanly)

**Verdict:** 🔄 **Replace entirely with Postgres tables.** This is the core of the migration.

### Storage Layer 3: JSON User/Tenant Persistence

**What it stores:** User accounts and tenant (namespace) records

**`UserStore`** (`server/storage/user_store.py`):
- One JSON file per user at `{root}/auth/users/{user_id}.json`
- Fields: id, username/email, password_hash, role, force_password_change, created_at, updated_at, locked_until, failed_login_count, password_changed_at, invite_token, invite_expires_at
- Searching by username requires loading all users and looping

**`TenantStore`** (`server/storage/tenant_store.py`):
- One JSON file per tenant at `{root}/auth/tenants/{slug}.json`
- Fields: tenant_slug, owner_user_id, visibility, created_at

**Verdict:** 🔄 **Replace with Postgres tables**, but scope changes significantly with Kinde (see Question 3).

### Storage Layer 4: SQLite Auth Store

**What it stores:** One-time tokens, tenant reservations, identity mappings, sessions, password history

**`SQLiteAuthStore`** (`server/storage/sqlite_auth_store.py`) backed by `schema_auth.sql`:

| Table | Purpose |
|---|---|
| `users` | Duplicates UserStore? Has id, email, password_hash, role, etc. |
| `tenants` | Duplicates TenantStore? Has tenant_slug, owner_user_id |
| `identities` | Maps provider (e.g., "local") to user_id — for multi-provider auth |
| `sessions` | session_id, user_id, csrf_token, created/expires/invalidated |
| `one_time_tokens` | Registration tokens, password reset tokens |
| `password_history` | Previous password hashes for reuse prevention |

**Verdict:** 🗑️ **Mostly eliminated by Kinde.** Sessions, passwords, tokens, and identity federation are all Kinde's job. Only the `tenants` concept and a slimmed-down `users` reference table survive (see Question 3).

### Storage Layer 5: In-Memory Rate Limiting

**`InMemoryRateLimiter`** in `server/middleware.py` — dict-based, lost on restart.

**Verdict:** 🔄 Consider moving to Postgres or Redis later, but not in scope for this DB feature. Acceptable for launch.

### Summary: Current Storage Landscape

```
┌─────────────────────────────────────────┐
│           What stores what today        │
├──────────────────┬──────────────────────┤
│ Archive blobs    │ S3 / local FS    ✅  │
│ Agent metadata   │ JSON on S3       🔄  │
│ User records     │ JSON files       🔄  │
│ Tenant records   │ JSON files       🔄  │
│ Auth state       │ SQLite           🗑️  │
│ Rate limits      │ In-memory        (ok)│
│ Sessions         │ SQLite + files   🗑️  │
└──────────────────┴──────────────────────┘

✅ = keep  🔄 = migrate to Postgres  🗑️ = eliminated by Kinde
```

---

## Question 3: With Kinde handling auth, what do you need in your own DB?

### What Kinde owns (you do NOT store)

| Concern | Kinde handles it | Your DB stores it? |
|---|---|---|
| User identity (email, name) | ✅ Kinde user profiles | ❌ No |
| Password storage & hashing | ✅ Kinde manages credentials | ❌ No |
| Password reset flow | ✅ Kinde hosted UI | ❌ No |
| Session management | ✅ Kinde access/refresh tokens | ❌ No |
| Login rate limiting & lockout | ✅ Kinde attack protection | ❌ No |
| Multi-factor auth | ✅ Kinde MFA | ❌ No |
| Social/SSO identity federation | ✅ Kinde connections | ❌ No |
| Registration invites | ✅ Kinde org invitations | ❌ No |
| Password history | ✅ Kinde password policies | ❌ No |
| CSRF tokens for login forms | ✅ Kinde hosted auth pages | ❌ No |

### What you DO need in your own registry DB

Even with Kinde, your server needs local tables for **registry-specific state that Kinde has no concept of**:

#### 1. `users` (thin reference table)

Maps Kinde's `sub` claim to your internal user identity. This is NOT a copy of Kinde user data — it's a join point.

```
users
├── id              UUID7 (PK, your internal user ID)
├── kinde_user_id   TEXT UNIQUE NOT NULL  (the `sub` from Kinde JWT)
├── email           TEXT NOT NULL         (denormalized from Kinde for display/search — updated on each login)
├── display_name    TEXT                  (denormalized from Kinde profile)
├── role            TEXT NOT NULL DEFAULT 'user'  ('admin' | 'user')
├── is_active       BOOLEAN DEFAULT TRUE  (soft-disable without touching Kinde)
├── created_at      TIMESTAMPTZ NOT NULL
└── updated_at      TIMESTAMPTZ NOT NULL
```

**Why you need this:**
- Your server needs to know "is this Kinde user an admin in our system?" Kinde knows about Kinde roles, but your registry has its own admin concept (who can create tenants, moderate agents, etc.)
- You need a stable internal UUID to FK from tenants, agents, audit logs. You can't FK to a Kinde `sub` string reliably across tables.
- You want to soft-disable a user in your system without deleting them from Kinde.

**How it gets populated:** On first successful login, your server receives the Kinde JWT, extracts `sub` + `email` + `name`, and upserts into this table. This is the "JIT provisioning" pattern.

#### 2. `tenants` (registry namespaces)

```
tenants
├── id              UUID7 (PK)
├── tenant_slug     TEXT UNIQUE NOT NULL  (the namespace, e.g., "acme-corp")
├── owner_id        UUID7 FK -> users.id NOT NULL
├── visibility      TEXT NOT NULL DEFAULT 'private'  ('public' | 'private')
├── metadata        JSONB DEFAULT '{}'    (future: billing tier, quotas, etc.)
├── created_at      TIMESTAMPTZ NOT NULL
└── updated_at      TIMESTAMPTZ NOT NULL
```

**Why not use Kinde organizations?** You could map Kinde organizations 1:1 to tenants, but:
- Kinde orgs are about access control groupings. Your tenants are about **agent namespaces** (like npm scopes).
- You need registry-specific fields (visibility, publish quotas, storage usage) that Kinde has no concept of.
- Keeping tenant state in your DB gives you full control over slug reservation, ownership transfer, etc.

**However:** You can (and should) use Kinde's `org_code` claim to validate that a user belongs to a Kinde org that maps to a tenant. This gives you organization-level access control for free.

#### 3. `tenant_members` (who can publish to a tenant)

```
tenant_members
├── id              UUID7 (PK)
├── tenant_id       UUID7 FK -> tenants.id NOT NULL
├── user_id         UUID7 FK -> users.id NOT NULL
├── role            TEXT NOT NULL DEFAULT 'member'  ('owner' | 'admin' | 'member')
├── created_at      TIMESTAMPTZ NOT NULL
└── UNIQUE(tenant_id, user_id)
```

**Why you need this:** Currently a tenant has a single `owner_user_id`. In production, teams need multiple members who can publish to the same tenant namespace.

#### 4. `agents` (replaces the AgentIndex JSON tier)

```
agents
├── id              UUID7 (PK)
├── tenant_id       UUID7 FK -> tenants.id NOT NULL
├── agent_slug      TEXT NOT NULL
├── visibility      TEXT NOT NULL DEFAULT 'public'
├── description     TEXT DEFAULT ''
├── deprecated_at   TIMESTAMPTZ           (soft-deprecation)
├── metadata        JSONB DEFAULT '{}'    (tags, categories, links — future extensibility)
├── created_at      TIMESTAMPTZ NOT NULL
├── updated_at      TIMESTAMPTZ NOT NULL
└── UNIQUE(tenant_id, agent_slug)
```

#### 5. `agent_versions` (replaces the VersionMetadata JSON tier)

```
agent_versions
├── id              UUID7 (PK)
├── agent_id        UUID7 FK -> agents.id NOT NULL
├── version         TEXT NOT NULL
├── manifest        JSONB NOT NULL        (the full kinnoo.yaml content)
├── storage_key     TEXT NOT NULL          (S3 key for the .kno archive)
├── signature_key   TEXT                   (S3 key for the .sig file, nullable)
├── sha256          TEXT NOT NULL          (archive checksum)
├── archive_size    BIGINT                 (bytes)
├── publisher_id    UUID7 FK -> users.id NOT NULL
├── security_status TEXT DEFAULT ''
├── security_report JSONB
├── created_at      TIMESTAMPTZ NOT NULL
├── updated_at      TIMESTAMPTZ NOT NULL
├── yanked_at       TIMESTAMPTZ           (soft-removal without deleting)
└── UNIQUE(agent_id, version)
```

**Design notes:**
- `manifest` as JSONB means you can query by runtime, author, description without denormalizing every field.
- `storage_key` replaces the current `storage_keys` dict. The archive blob stays in S3 — this column is just the pointer.
- `yanked_at` is the standard package registry pattern (npm, crates.io): mark a version as "do not install" without deleting it.

#### 6. `api_keys` (for CI/CD headless auth)

```
api_keys
├── id              UUID7 (PK)
├── user_id         UUID7 FK -> users.id NOT NULL
├── tenant_id       UUID7 FK -> tenants.id NOT NULL  (scoped to a namespace)
├── key_prefix      TEXT NOT NULL          (first 8 chars of key, for display: "kno_a1b2...")
├── key_hash        TEXT NOT NULL          (SHA-256 of the full key)
├── name            TEXT NOT NULL          (user-chosen label, e.g., "GitHub Actions")
├── scopes          TEXT[] NOT NULL        (e.g., ['registry:publish', 'registry:read'])
├── expires_at      TIMESTAMPTZ           (nullable = never expires)
├── last_used_at    TIMESTAMPTZ
├── revoked_at      TIMESTAMPTZ
├── created_at      TIMESTAMPTZ NOT NULL
└── updated_at      TIMESTAMPTZ NOT NULL
```

**Why you need this:** Kinde tokens expire and require browser-based OIDC flows. CI/CD pipelines (GitHub Actions, etc.) need long-lived tokens to run `kinnoo publish`. This is the standard pattern — PyPI has API tokens, npm has access tokens, Docker Hub has PATs.

**How it works:**
- User generates an API key via `kinnoo token create` CLI or web UI
- Server returns the full key once (e.g., `kno_a1b2c3d4...`), stores only the hash
- `kinnoo publish` sends the key in `Authorization: Bearer kno_...` header
- Server checks hash against `api_keys` table, validates scopes and expiry

#### 7. `audit_log` (registry activity ledger)

```
audit_log
├── id              UUID7 (PK)
├── actor_id        UUID7 FK -> users.id  (nullable for anonymous/system events)
├── action          TEXT NOT NULL          ('agent.publish', 'agent.yank', 'agent.download', 'tenant.create', 'user.login', 'apikey.create', etc.)
├── resource_type   TEXT NOT NULL          ('agent_version', 'tenant', 'user', 'api_key')
├── resource_id     UUID7                  (the ID of the affected resource)
├── details         JSONB DEFAULT '{}'     (action-specific payload: version, IP, user-agent, etc.)
├── ip_address      TEXT
├── created_at      TIMESTAMPTZ NOT NULL
```

**Why you need this:** `db.rules.md` says "every record must be treated as audit-grade data." A production registry needs a tamper-evident log of who did what. This is also your future source for download counts, abuse detection, and compliance.

#### 8. `download_events` (lightweight stats — optional but recommended)

```
download_events
├── id              UUID7 (PK)
├── agent_version_id UUID7 FK -> agent_versions.id NOT NULL
├── downloader_id   UUID7 FK -> users.id  (nullable for anonymous downloads if you allow them)
├── ip_address      TEXT
├── user_agent      TEXT
├── created_at      TIMESTAMPTZ NOT NULL
```

**Why separate from audit_log?** Download events are high-volume and have a simpler schema. Keeping them separate means you can aggregate/archive them independently and add materialized views for "weekly downloads" without polluting the audit log.

### What gets deleted from the codebase

With Kinde + Postgres, these are retired:

| Current file/module | Disposition |
|---|---|
| `server/storage/sqlite_auth_store.py` | **Delete.** Kinde handles auth state. |
| `server/storage/sql/schema_auth.sql` | **Delete.** No more SQLite schema. |
| `server/storage/user_store.py` | **Delete.** Replaced by `UserRepository` against Postgres `users` table. |
| `server/storage/tenant_store.py` | **Delete.** Replaced by `TenantRepository` against Postgres `tenants` table. |
| `server/metadata/manager.py` | **Adapt.** Create `PostgresMetadataManager` implementing same interface, backed by `agents` + `agent_versions` tables. |
| `server/metadata/models.py` | **Keep as API DTOs.** These dataclasses are used by routes to serialize responses. They become the "read model" that repositories return. |
| `server/models/user.py` (PasswordManager) | **Delete password code.** Keep `Role` type and slug derivation. |
| `server/auth/session.py` | **Delete.** Kinde manages sessions. |
| `server/auth/token.py` (HMAC TokenService) | **Replace with Kinde JWT validation.** New `KindeTokenVerifier` that fetches JWKS and validates RS256 tokens. |
| `server/auth/tokens.py` (registration/reset token services) | **Delete.** Kinde handles these flows. |

### Entity-Relationship Summary

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  users   │────<│tenant_members│>────│  tenants   │
│ (Kinde   │     └──────────────┘     │ (namespace) │
│  sub →   │                          └──────┬─────┘
│  local)  │                                 │
└────┬─────┘                          ┌──────┴─────┐
     │                                │   agents   │
     │                                └──────┬─────┘
     │                                       │
     │  ┌──────────────┐              ┌──────┴──────────┐
     ├──│  api_keys    │              │ agent_versions   │
     │  └──────────────┘              └─────────────────┘
     │
     ├──< audit_log
     └──< download_events
```

### Recommended Table Count: 8

| # | Table | Replaces |
|---|---|---|
| 1 | `users` | UserStore JSON + SQLite users |
| 2 | `tenants` | TenantStore JSON + SQLite tenants |
| 3 | `tenant_members` | (new — currently single owner only) |
| 4 | `agents` | AgentIndex JSON + GlobalIndex JSON |
| 5 | `agent_versions` | VersionMetadata JSON |
| 6 | `api_keys` | (new — needed for CI/CD auth) |
| 7 | `audit_log` | (new — per db.rules.md audit requirement) |
| 8 | `download_events` | (new — registry analytics) |

---

## Recommended Implementation Order for SWE Agent

### Phase 1: Foundation (no route changes)
1. Create `server/database/` directory structure per `db.rules.md`
2. Define SQLModel models for all 8 tables
3. Create `session.py` with async engine + session factory
4. Set up Alembic with initial migration
5. Write repository classes: `UserRepository`, `TenantRepository`, `AgentRepository`, `AgentVersionRepository`
6. Add `REGISTRY_DATABASE_URL` to `ServerConfig`
7. Docker Compose file for local Postgres

### Phase 2: Data layer swap
8. Create `PostgresMetadataManager` implementing same interface as `MetadataManager`
9. Feature flag in config: `storage_metadata_backend: "json" | "postgres"`
10. Wire `create_app()` to use Postgres manager when flag is set
11. Migrate existing routes one-by-one to use new repositories
12. Data migration script: JSON → Postgres for existing dev data

### Phase 3: Auth swap (depends on Kinde feature)
13. Replace `TokenService` with `KindeTokenVerifier`
14. Replace `UserStore` with `UserRepository` + JIT provisioning
15. Replace `TenantStore` with `TenantRepository`
16. Add `api_keys` table and `kinnoo token create` command
17. Remove SQLite auth store, session service, password manager

### Phase 4: CLI and testing
18. `kinnoo-server connect registry-db` command
19. `kinnoo-server db migrate` (wraps Alembic)
20. `kinnoo-server db seed` (creates example data)
21. Domain commands: `kinnoo-server tenant list/create`, `kinnoo-server user list/set-role`
22. Migrate all server tests to Postgres (conftest fixtures with transaction rollback)
23. CI workflow update: add Postgres service container

---

## Appendix: Key Design Decisions the Operator Should Make Before Implementation

1. **Kinde org_code → tenant mapping**: Should a Kinde organization map 1:1 to a registry tenant? Or should users self-create tenants independent of Kinde orgs?

2. **API key format**: Prefix convention? Suggested: `kno_` + 32 random bytes base62-encoded. (Similar to `sk_live_` for Stripe, `npm_` for npm.)

3. **Download anonymity**: Can unauthenticated users download public agents? Or is auth required for all downloads? (Currently auth is required.)

4. **Version immutability**: Once published, can a version be overwritten? Currently the server returns 409 on duplicate version. The `yanked_at` field allows soft-removal without overwrite.

5. **Tenant creation policy**: Admin-only (current model) or self-service on first publish?

6. **Should Phase 2 and Phase 3 be separate features?** Phase 2 (Postgres for agent metadata) is independent of Phase 3 (Kinde auth swap). They can be done in parallel by separate agents, or sequentially. The `users` table schema depends on whether Kinde is integrated yet.

---

## Follow-Up Q&A: Round 2 (2026-04-18)

### Operator's Questions

**Q1 reply — PostgresMetadataManager:**
> I assume this will be used to put and get agent metadata from the Postgres DB? If so, we will use SQLAlchemy 2.0 for the actual DB queries (NOT raw SQL), correct? If so, YES — create a PostgresMetadataManager that implements the same interface as existing MetadataManager, so routes don't change. If needed, add new methods in the PostgresMetadataManager, as needed.

**Q1 reply — kinnoo-server CLI:**
> I should be able to execute a suite of DB queries (using SQLAlchemy 2.0, NOT raw SQL) using simple kinnoo-server CLI commands. Example workflow:
> 1. `kinnoo-server connect db registry-postgres` to connect to the agent registry DB
> 2. `kinnoo-server db list-tables` to list all tables in the DB
> 3. `kinnoo-server db list-columns agent` to list all column names in table 'agent'
> 4. `kinnoo-server db query agents agent-name 'openclaw'` to query the table 'agents' and search for all agents with agent-name 'openclaw'
>
> Under the hood, these CLI commands would execute SQLAlchemy queries. Does this make sense?
>
> Let's start with kinnoo-server CLI DB commands that can QUERY the database, NO ADD, DELETE, OR MODIFY commands yet. Come up with an initial list of useful DB query commands — list these in detail so an SWE agent knows exactly what to implement.

**Q1 reply — Migration strategy:**
> Hard cutover vs feature flag. What's your recommendation? Do you think, in the interim, it makes sense to keep the filesystem-based database store? If so, then we should lean towards feature flag.

**Q1 reply — Testing strategy:**
> Yes, draft a testing strategy — transaction rollback per test, Postgres service container in CI, async fixtures in conftest, and whatever else we need.

**Q1 reply — Connection management:**
> Yes, we need everything you mentioned.

**Q2:** Agreed with all verdicts.

**Q3 — Table questions:**
> 1. users — list out the columns. Propose column names and types. Consider if there are any other columns we need.
> 2–5. Yes to tenants, tenant_members, agents, agent_versions.
> 6. api_keys — these are GitHub API tokens basically?
> 7. audit_log — EVERY action that queries or modifies the registry should be logged. Consider the full list of actions. Maybe agent "search" queries can be omitted.
> 8. download_events — yes.
>
> Also: I want to "future-proof" this database for "workspaces" (a collection of tenants with a new visibility scope: agents can be private, public, or "workspace-visible"). Do we need another table or will tenants + tenant_members cover this?
>
> Finally, consider ALL columns (name and type) for each table, and consider if we need any additional tables.

---

### Response: Round 2

#### 1. PostgresMetadataManager — Confirmed Design

Yes, exactly right. `PostgresMetadataManager` will:

- Implement the same public interface as the current `MetadataManager` (same method signatures)
- Use **SQLAlchemy 2.0 ORM queries only** — no raw SQL strings anywhere
- Internally use `AsyncSession` from the session factory, executing queries via repository classes
- Route code stays untouched during migration — only the wiring in `create_app()` changes

**Existing methods it must implement (from current `MetadataManager`):**

| Method | What it does today | What PostgresMetadataManager does |
|---|---|---|
| `get_version_metadata(tenant_slug, agent_slug, version)` | Read JSON from S3 | `SELECT FROM agent_versions JOIN agents JOIN tenants WHERE ...` |
| `put_version_metadata(metadata)` | Write JSON to S3 | `INSERT INTO agent_versions ...` |
| `get_agent_index(tenant_slug, agent_slug)` | Read JSON from S3 | `SELECT FROM agent_versions WHERE agent.slug = ... AND tenant.slug = ...` |
| `put_agent_index(index)` | Write JSON to S3 | No-op (index is implicit in the DB, not a separate document) |
| `get_global_index()` | Read JSON from S3 | `SELECT FROM agents JOIN tenants` with aggregation |
| `put_global_index(index)` | Write JSON to S3 | No-op (global view is a query, not a stored document) |
| `upsert_version_metadata(metadata)` | Write version + update agent index + update global index | Single `INSERT ... ON CONFLICT UPDATE` on agent_versions (+ upsert agents if new agent) |

**New methods to add on `PostgresMetadataManager`** (not on the original interface — these take advantage of Postgres query capability):

| New method | Purpose | Used by |
|---|---|---|
| `search_agents(query, tenant_slug?, offset, limit)` | Full-text search on agent_slug + description | search route (replaces in-memory loop over GlobalIndex) |
| `list_agents_paginated(tenant_slug?, visibility?, offset, limit)` | Paginated list with filters | agents route (replaces loading entire GlobalIndex) |
| `get_agent_version_count(agent_id)` | Count versions for an agent | Detail views |
| `get_latest_version(agent_id)` | Get most recent non-yanked version | Download route |
| `delete_version_metadata(tenant_slug, agent_slug, version)` | Soft-yank a version | Future yank command |

The routes can be gradually updated to use these new methods for better performance, while old routes continue working through the original interface.

---

#### 2. kinnoo-server CLI — Read-Only DB Query Commands

Your mental model is exactly right. Here's my thinking on the architecture and the initial command set.

**Architecture:**

Every `kinnoo-server db *` command:
1. Reads `REGISTRY_DATABASE_URL` from env (or `--db-url` flag)
2. Creates a **synchronous** SQLAlchemy engine (CLI is not async — no event loop needed for one-shot queries)
3. Executes SQLAlchemy ORM queries (never raw SQL)
4. Prints results as formatted tables (human-readable) or JSON (`--json` flag)

The `connect` subcommand is the exception — it doesn't query directly but establishes context for the session (or launches psql).

**Initial read-only command set for SWE agent to implement:**

##### Schema Inspection Commands

| Command | Description | SQLAlchemy Implementation | Example Output |
|---|---|---|---|
| `kinnoo-server db list-tables` | List all tables in the registry DB | `inspect(engine).get_table_names()` | `users, tenants, tenant_members, agents, agent_versions, api_keys, audit_log, download_events` |
| `kinnoo-server db list-columns <table>` | List columns, types, and constraints for a table | `inspect(engine).get_columns(table)` | `id: UUID (PK), agent_slug: VARCHAR, ...` |
| `kinnoo-server db row-count <table>` | Count rows in a table | `select(func.count()).select_from(Model)` | `agents: 42 rows` |
| `kinnoo-server db row-count --all` | Count rows in every table | Same, looped over all models | `users: 5, tenants: 3, agents: 42, ...` |

##### Agent Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query agents` | List all agents (paginated, default 25) | `select(Agent).options(joinedload(Agent.tenant)).offset(...).limit(...)` |
| `kinnoo-server db query agents --tenant <slug>` | List agents filtered by tenant | Add `.where(Tenant.tenant_slug == slug)` |
| `kinnoo-server db query agents --name <name>` | Search agents by slug (substring match) | Add `.where(Agent.agent_slug.ilike(f'%{name}%'))` |
| `kinnoo-server db query agents --visibility public` | Filter by visibility | Add `.where(Agent.visibility == 'public')` |
| `kinnoo-server db query agent-detail <tenant>/<slug>` | Show one agent with all versions | `select(Agent).where(...).options(selectinload(Agent.versions))` |

##### Version Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query versions --agent <tenant>/<slug>` | List all versions of an agent | `select(AgentVersion).join(Agent).join(Tenant).where(...)` |
| `kinnoo-server db query versions --latest` | List latest version per agent | Window function or subquery with `MAX(created_at)` |
| `kinnoo-server db query versions --yanked` | List yanked versions only | `.where(AgentVersion.yanked_at.is_not(None))` |
| `kinnoo-server db query version-detail <tenant>/<slug>/<version>` | Full detail for one version (manifest, checksums, publisher) | `select(AgentVersion).where(...).options(joinedload(AgentVersion.publisher))` |

##### User Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query users` | List all users | `select(User).order_by(User.created_at)` |
| `kinnoo-server db query users --email <email>` | Find user by email | `.where(User.email.ilike(f'%{email}%'))` |
| `kinnoo-server db query users --role admin` | Filter by role | `.where(User.role == 'admin')` |
| `kinnoo-server db query user-detail <user-id>` | Show one user with their tenants and agents | `select(User).where(...).options(selectinload(User.tenant_memberships))` |

##### Tenant Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query tenants` | List all tenants | `select(Tenant).order_by(Tenant.tenant_slug)` |
| `kinnoo-server db query tenants --owner <email>` | Filter by owner email | `.join(User).where(User.email == ...)` |
| `kinnoo-server db query tenant-detail <slug>` | Show one tenant with members and agent count | `select(Tenant).where(...).options(selectinload(Tenant.members))` |

##### API Key Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query api-keys` | List all API keys (redacted — prefix only) | `select(ApiKey).options(joinedload(ApiKey.user))` |
| `kinnoo-server db query api-keys --user <email>` | Filter by user | `.join(User).where(User.email == ...)` |
| `kinnoo-server db query api-keys --expired` | Show expired keys | `.where(ApiKey.expires_at < func.now())` |
| `kinnoo-server db query api-keys --revoked` | Show revoked keys | `.where(ApiKey.revoked_at.is_not(None))` |

##### Audit Query Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query audit` | List recent audit events (default last 50) | `select(AuditLog).order_by(AuditLog.created_at.desc()).limit(50)` |
| `kinnoo-server db query audit --action <action>` | Filter by action type | `.where(AuditLog.action == action)` |
| `kinnoo-server db query audit --actor <email>` | Filter by actor | `.join(User).where(User.email == ...)` |
| `kinnoo-server db query audit --since <date>` | Filter events after date | `.where(AuditLog.created_at >= date)` |
| `kinnoo-server db query audit --resource <type> <id>` | Filter by affected resource | `.where(AuditLog.resource_type == ..., AuditLog.resource_id == ...)` |

##### Stats / Aggregate Commands

| Command | Description | SQLAlchemy Implementation |
|---|---|---|
| `kinnoo-server db query stats` | Dashboard summary: total users, tenants, agents, versions, downloads | Multiple `func.count()` queries |
| `kinnoo-server db query stats downloads --agent <tenant>/<slug>` | Download count for an agent | `select(func.count()).select_from(DownloadEvent).join(AgentVersion).join(Agent).where(...)` |
| `kinnoo-server db query stats downloads --top 10` | Top 10 agents by download count | Group-by with `ORDER BY count DESC LIMIT 10` |

**Common flags on all query commands:**

| Flag | Purpose |
|---|---|
| `--json` | Output as JSON instead of formatted table |
| `--limit <n>` | Override default page size (default: 25) |
| `--offset <n>` | Pagination offset |
| `--db-url <url>` | Override `REGISTRY_DATABASE_URL` env var |

**Total initial commands: ~28 read-only query commands.** This is a large surface, so SWE agent should implement them in batches:
- Batch 1: Schema inspection (4 commands) + `stats` (1 command) — simplest, proves the plumbing works
- Batch 2: Agent + version queries (9 commands) — core registry read path
- Batch 3: User + tenant + API key queries (10 commands)
- Batch 4: Audit + download queries (4 commands)

---

#### 3. Migration Strategy: Feature Flag

**Recommendation: Feature flag.** Here's why:

- The filesystem-backed store works today and is tested. Ripping it out immediately creates a hard dependency on Postgres being configured, which breaks local dev and all existing tests simultaneously.
- A feature flag lets you:
  1. Build and test `PostgresMetadataManager` in isolation
  2. Run both backends in parallel during development (write to both, read from Postgres)
  3. Flip the flag in staging, validate, then flip in production
  4. Revert to filesystem instantly if Postgres issues arise in early deployment

**Implementation:**

Add to `ServerConfig`:

```python
metadata_backend: Literal["json", "postgres"] = "json"  # env: REGISTRY_METADATA_BACKEND
```

In `create_app()`:

```python
if resolved_config.metadata_backend == "postgres":
    metadata_manager = PostgresMetadataManager(session_factory=db_session_factory)
else:
    metadata_manager = MetadataManager(storage=storage_backend)  # existing JSON-backed
```

**Migration phases:**

| Phase | `REGISTRY_METADATA_BACKEND` | Behavior |
|---|---|---|
| Phase A: Build | `json` (default) | Everything works as today. Postgres code exists but is unused by routes. |
| Phase B: Shadow | `json` | Routes use JSON manager, but a background job also writes to Postgres for validation. Detect drift. |
| Phase C: Switch | `postgres` | Routes use Postgres. JSON manager still available as fallback. |
| Phase D: Cleanup | `postgres` | Remove JSON manager code, feature flag, and S3 metadata key paths. |

Phase B (shadow writes) is optional but recommended for confidence. It can be as simple as a post-request hook that writes to Postgres after every successful JSON write, then a nightly script that compares the two.

---

#### 4. Testing Strategy

##### Test Isolation: Transaction Rollback Per Test

Every test runs inside a database transaction that is rolled back at the end. This means:
- Tests are completely isolated — no leaked state between tests
- No need for teardown/truncation scripts
- Very fast — rollback is cheaper than DROP/CREATE

**Implementation pattern in `server/tests/conftest.py`:**

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from server.database.session import Base  # all models registered here

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://kinnoo_test:kinnoo_test@localhost:5432/kinnoo_test"
)

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create engine once for the entire test session; create all tables."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    """Per-test session with automatic rollback."""
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def user_repo(db_session):
    """Pre-wired UserRepository for tests."""
    from server.database.repository import UserRepository
    return UserRepository(session=db_session)

@pytest_asyncio.fixture
async def tenant_repo(db_session):
    from server.database.repository import TenantRepository
    return TenantRepository(session=db_session)

@pytest_asyncio.fixture
async def agent_repo(db_session):
    from server.database.repository import AgentRepository
    return AgentRepository(session=db_session)
# ... etc. for each repository
```

##### Factory Fixtures

Tests need to quickly create valid test data. Provide factory fixtures:

```python
@pytest_asyncio.fixture
async def make_user(db_session):
    """Factory that creates a user and returns it."""
    async def _make(*, email="test@example.com", role="user", kinde_user_id=None):
        from server.database.models.user import User
        user = User(
            kinde_user_id=kinde_user_id or f"kinde_{uuid7()}",
            email=email,
            display_name=email.split("@")[0],
            role=role,
        )
        db_session.add(user)
        await db_session.flush()
        return user
    return _make

@pytest_asyncio.fixture
async def make_tenant(db_session, make_user):
    async def _make(*, slug="test-tenant", owner=None):
        from server.database.models.tenant import Tenant
        if owner is None:
            owner = await make_user()
        tenant = Tenant(tenant_slug=slug, owner_id=owner.id)
        db_session.add(tenant)
        await db_session.flush()
        return tenant
    return _make

@pytest_asyncio.fixture
async def make_agent(db_session, make_tenant):
    async def _make(*, slug="test-agent", tenant=None, visibility="public"):
        from server.database.models.agent import Agent
        if tenant is None:
            tenant = await make_tenant()
        agent = Agent(tenant_id=tenant.id, agent_slug=slug, visibility=visibility)
        db_session.add(agent)
        await db_session.flush()
        return agent
    return _make
```

##### Postgres in CI: GitHub Actions Service Container

```yaml
# .github/workflows/ci.yml (addition to existing)
services:
  postgres:
    image: postgres:16
    env:
      POSTGRES_USER: kinnoo_test
      POSTGRES_PASSWORD: kinnoo_test
      POSTGRES_DB: kinnoo_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

env:
  TEST_DATABASE_URL: postgresql+asyncpg://kinnoo_test:kinnoo_test@localhost:5432/kinnoo_test
```

##### Local Dev: Docker Compose for Postgres

```yaml
# docker-compose.yml (at repo root)
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: kinnoo_dev
      POSTGRES_PASSWORD: kinnoo_dev
      POSTGRES_DB: kinnoo_registry
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

##### Required Test Dependencies (add to `server/requirements.txt`)

```
pytest-asyncio>=0.23.0
asyncpg>=0.29.0
sqlalchemy[asyncio]>=2.0.0
sqlmodel>=0.0.14
```

##### Test Organization

| Test file | What it covers |
|---|---|
| `server/tests/test_db_models.py` | Model validation, constraints, defaults |
| `server/tests/test_db_repositories.py` | Repository CRUD operations against real Postgres |
| `server/tests/test_postgres_metadata_manager.py` | PostgresMetadataManager interface compliance (mirrors existing MetadataManager tests) |
| `server/tests/test_db_cli.py` | kinnoo-server db query commands (invoke CLI, check output) |
| `server/tests/test_db_migration.py` | Alembic migration up/down works cleanly |

---

#### 5. Connection Management

##### Environment Variables

| Env var | Purpose | Default |
|---|---|---|
| `REGISTRY_DATABASE_URL` | Async connection string | `postgresql+asyncpg://localhost:5432/kinnoo_registry` |
| `REGISTRY_DB_POOL_SIZE` | Core pool connections | `5` |
| `REGISTRY_DB_MAX_OVERFLOW` | Extra connections beyond pool | `10` |
| `REGISTRY_DB_POOL_RECYCLE_SECONDS` | Connection max age | `3600` |
| `REGISTRY_DB_ECHO` | Log all SQL (dev only) | `false` |

##### Session Factory (`server/database/session.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

def create_engine_from_config(config: ServerConfig):
    return create_async_engine(
        config.database_url,
        pool_size=config.db_pool_size,
        max_overflow=config.db_max_overflow,
        pool_recycle=config.db_pool_recycle_seconds,
        echo=config.db_echo,
        pool_pre_ping=True,  # detect stale connections
    )

def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

##### Startup Behavior

- **Fail-fast:** `create_app()` attempts a connection on startup. If Postgres is unreachable and `metadata_backend == "postgres"`, the server refuses to start with a clear error message.
- **If `metadata_backend == "json"`**, Postgres is not required (backward compatible).

##### Health Check

Extend the existing `/health` endpoint:

```python
@app.get("/health")
async def health():
    checks = {"storage": _is_s3_ready(...)}
    if config.metadata_backend == "postgres":
        checks["database"] = await _is_db_ready(session_factory)
    all_ok = all(checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ok" if all_ok else "degraded", "checks": checks}
    )
```

Where `_is_db_ready` does:

```python
async def _is_db_ready(session_factory):
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

---

#### 6. api_keys — Clarification

Not GitHub API tokens. These are **kinnoo registry API tokens** — similar in concept to:

| Service | Their token | Our equivalent |
|---|---|---|
| GitHub | Personal Access Tokens (PATs) | kinnoo API keys |
| PyPI | API tokens (`pypi-...`) | `kno_...` |
| npm | Access tokens (`npm_...`) | `kno_...` |
| Docker Hub | PATs | `kno_...` |

The use case: when you run `kinnoo publish` from a CI/CD pipeline (GitHub Actions, Jenkins, etc.), you can't do a browser-based Kinde login. Instead, you create a kinnoo API key through the web UI or CLI, store it as a GitHub Actions secret, and pass it as `KINNOO_API_TOKEN` in your pipeline. The `kinnoo` CLI sends it in the `Authorization: Bearer kno_...` header.

The server checks the hash of the incoming key against the `api_keys` table, validates that the key has the required scope (`registry:publish`), hasn't expired, and hasn't been revoked.

---

#### 7. audit_log — Comprehensive Action List

Here is the full list of auditable actions for the registry, organized by domain:

##### Actions to Log

| Action string | Trigger | resource_type | details (JSONB) |
|---|---|---|---|
| **Authentication** | | | |
| `user.login` | User authenticates via Kinde | `user` | `{method: "kinde", ip, user_agent}` |
| `user.login.api_key` | Request authenticated via API key | `api_key` | `{key_prefix, ip, user_agent}` |
| `user.jit_provision` | First-time user auto-created from Kinde JWT | `user` | `{kinde_user_id, email}` |
| **User Management** | | | |
| `user.role_change` | Admin changes a user's role | `user` | `{old_role, new_role, changed_by}` |
| `user.deactivate` | Admin deactivates a user | `user` | `{reason, deactivated_by}` |
| `user.reactivate` | Admin reactivates a user | `user` | `{reactivated_by}` |
| **Tenant Management** | | | |
| `tenant.create` | New tenant namespace created | `tenant` | `{tenant_slug, owner_email}` |
| `tenant.member_add` | User added to tenant | `tenant` | `{member_email, role}` |
| `tenant.member_remove` | User removed from tenant | `tenant` | `{member_email, removed_by}` |
| `tenant.member_role_change` | Tenant member role changed | `tenant` | `{member_email, old_role, new_role}` |
| `tenant.visibility_change` | Tenant visibility changed | `tenant` | `{old_visibility, new_visibility}` |
| **Agent Lifecycle** | | | |
| `agent.create` | New agent first published (agent record created) | `agent` | `{agent_slug, tenant_slug}` |
| `agent.publish` | New version published | `agent_version` | `{agent_slug, version, tenant_slug, sha256, archive_size}` |
| `agent.yank` | Version yanked (soft-removed) | `agent_version` | `{agent_slug, version, reason}` |
| `agent.unyank` | Yanked version restored | `agent_version` | `{agent_slug, version}` |
| `agent.deprecate` | Agent marked deprecated | `agent` | `{agent_slug, reason}` |
| `agent.visibility_change` | Agent visibility toggled | `agent` | `{agent_slug, old_visibility, new_visibility}` |
| `agent.download` | Agent archive downloaded | `agent_version` | `{agent_slug, version, tenant_slug}` |
| **API Key Management** | | | |
| `apikey.create` | New API key generated | `api_key` | `{key_prefix, name, scopes, tenant_slug}` |
| `apikey.revoke` | API key revoked | `api_key` | `{key_prefix, revoked_by}` |
| **Security Events** | | | |
| `security.scan_complete` | Post-publish security scan finished | `agent_version` | `{agent_slug, version, status, findings_count}` |
| `security.failed_auth` | Failed authentication attempt (bad API key) | `api_key` | `{key_prefix, ip, reason}` |

##### Actions Deliberately NOT Logged

| Action | Why skip |
|---|---|
| `agent.search` | High volume, low audit value. Search analytics can go to a separate analytics pipeline if needed later. |
| `agent.list` | Same — read-only listing is noise in an audit log. |
| Health check pings | Infrastructure noise. |
| Schema migrations | These are tracked by Alembic's own version history. |

##### audit_log Table — Final Column Spec

```
audit_log
├── id              UUID7 (PK)
├── actor_id        UUID7 FK -> users.id  (nullable — system events have no actor)
├── action          TEXT NOT NULL          (e.g., 'agent.publish')
├── resource_type   TEXT NOT NULL          ('user' | 'tenant' | 'agent' | 'agent_version' | 'api_key')
├── resource_id     UUID7                  (nullable — some events don't target a single resource)
├── tenant_id       UUID7 FK -> tenants.id (nullable — for tenant-scoped events, enables per-tenant audit queries)
├── details         JSONB DEFAULT '{}'     (action-specific payload, structured per action table above)
├── ip_address      INET                   (Postgres native INET type for proper IP handling)
├── user_agent      TEXT                   (HTTP User-Agent header)
├── created_at      TIMESTAMPTZ NOT NULL   (event timestamp, never updated)
```

**Changes from Round 1:**
- Added `tenant_id` column — enables fast per-tenant audit filtering without parsing JSONB
- Added `user_agent` column — useful for distinguishing CLI vs web UI vs API key access
- Changed `ip_address` from TEXT to INET — Postgres native type with validation and indexing support
- `created_at` is the only timestamp — audit logs are append-only, no `updated_at`

**Indexes:**

```sql
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_actor_id ON audit_log(actor_id);
CREATE INDEX idx_audit_tenant_id ON audit_log(tenant_id);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);
```

---

#### 8. Workspace Future-Proofing

**Question: Do we need a separate `workspaces` table, or do tenants + tenant_members cover this?**

**Answer: You need two new tables.** Tenants and tenant_members handle the "who can publish to a namespace" concern. Workspaces are a different concept — they group tenants together and introduce a new visibility scope. Trying to overload tenant_members to also mean "workspace membership" would conflate two distinct relationships.

**What a workspace represents:**

A workspace is like a GitHub Organization or an npm Org — it's a group of tenants (namespaces) that share a visibility scope. Agents can be:
- **public** — visible to everyone
- **workspace-visible** — visible to all members of the workspace, across all tenants in that workspace
- **private** — visible only to members of the owning tenant

**Tables needed for workspace support:**

```
workspaces
├── id              UUID7 (PK)
├── workspace_slug  TEXT UNIQUE NOT NULL
├── display_name    TEXT NOT NULL
├── owner_id        UUID7 FK -> users.id NOT NULL
├── metadata        JSONB DEFAULT '{}'
├── created_at      TIMESTAMPTZ NOT NULL
└── updated_at      TIMESTAMPTZ NOT NULL
```

```
workspace_members
├── id              UUID7 (PK)
├── workspace_id    UUID7 FK -> workspaces.id NOT NULL
├── user_id         UUID7 FK -> users.id NOT NULL
├── role            TEXT NOT NULL DEFAULT 'member'  ('owner' | 'admin' | 'member')
├── created_at      TIMESTAMPTZ NOT NULL
└── UNIQUE(workspace_id, user_id)
```

Plus a FK on `tenants`:

```
tenants
├── ...existing columns...
├── workspace_id    UUID7 FK -> workspaces.id  (nullable — a tenant can exist outside a workspace)
```

And extend `agents.visibility`:

```
agents.visibility: 'public' | 'workspace' | 'private'  (extend from current 'public' | 'private')
```

**However — do NOT build these tables now.** Here's why:

1. Workspaces are a "nice to have" post-launch feature, not a launch requirement
2. Adding nullable `workspace_id` to `tenants` later is a trivial Alembic migration
3. Adding `workspaces` and `workspace_members` tables later is zero-risk (new tables, no schema changes to existing tables)
4. The visibility enum extension (`'workspace'`) is a one-line migration

**What to do now for future-proofing:**

- Use `TEXT` (not a Postgres ENUM) for `visibility` on `agents` and `tenants`. TEXT is easier to extend than an ENUM.
- Use `JSONB metadata` columns on `tenants` and `agents` — if workspace-related metadata is needed before the full workspace feature, it can go here temporarily.
- Document the workspace ER design in this planning doc (done above) so the future SWE agent has the schema ready.

This approach gives you **zero schema debt now** and **zero migration pain later**.

---

#### 9. Complete Table Specifications — All Columns, All Types

Here are the final, complete table definitions with every column, type, constraint, default, and index. This is the authoritative spec for the SWE agent.

##### Table 1: `users`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | Internal user ID |
| `kinde_user_id` | `TEXT` | UNIQUE, NOT NULL | — | Kinde `sub` claim; JIT-provisioned on first login |
| `email` | `TEXT` | NOT NULL | — | Denormalized from Kinde; updated on each login |
| `display_name` | `TEXT` | | `''` | Denormalized from Kinde profile |
| `avatar_url` | `TEXT` | | `NULL` | Denormalized from Kinde profile picture |
| `role` | `TEXT` | NOT NULL | `'user'` | `'admin'` or `'user'` |
| `is_active` | `BOOLEAN` | NOT NULL | `TRUE` | Soft-disable without touching Kinde |
| `last_login_at` | `TIMESTAMPTZ` | | `NULL` | Updated on each successful auth |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | Auto-updated on change |

**Indexes:**
- `UNIQUE(kinde_user_id)`
- `idx_users_email ON users(email)`
- `idx_users_role ON users(role)` (for admin lookups)

##### Table 2: `tenants`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `tenant_slug` | `TEXT` | UNIQUE, NOT NULL | — | Namespace identifier, e.g. "acme-corp" |
| `owner_id` | `UUID` | FK → users.id, NOT NULL | — | |
| `visibility` | `TEXT` | NOT NULL | `'private'` | `'public'` or `'private'` (TEXT not ENUM for extensibility) |
| `workspace_id` | `UUID` | FK → workspaces.id | `NULL` | Reserved for future workspace feature |
| `metadata` | `JSONB` | NOT NULL | `'{}'` | Billing tier, quotas, etc. |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes:**
- `UNIQUE(tenant_slug)`
- `idx_tenants_owner ON tenants(owner_id)`
- `idx_tenants_workspace ON tenants(workspace_id)` (sparse; useful when workspaces are active)

**Note:** `workspace_id` is nullable and has no FK constraint yet (the `workspaces` table doesn't exist). When the workspace feature ships, add the table and the FK in the same Alembic migration.

##### Table 3: `tenant_members`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `tenant_id` | `UUID` | FK → tenants.id, NOT NULL | — | ON DELETE CASCADE |
| `user_id` | `UUID` | FK → users.id, NOT NULL | — | ON DELETE CASCADE |
| `role` | `TEXT` | NOT NULL | `'member'` | `'owner'`, `'admin'`, or `'member'` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes/Constraints:**
- `UNIQUE(tenant_id, user_id)` — a user can only be a member of a tenant once
- `idx_tenant_members_user ON tenant_members(user_id)` — for "what tenants is this user in?" queries

##### Table 4: `agents`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `tenant_id` | `UUID` | FK → tenants.id, NOT NULL | — | ON DELETE RESTRICT (don't delete tenant with published agents) |
| `agent_slug` | `TEXT` | NOT NULL | — | Agent name within the namespace |
| `visibility` | `TEXT` | NOT NULL | `'public'` | `'public'`, `'private'` (future: `'workspace'`) |
| `description` | `TEXT` | NOT NULL | `''` | Short description for search/listing |
| `homepage_url` | `TEXT` | | `NULL` | Link to docs/repo |
| `deprecated_at` | `TIMESTAMPTZ` | | `NULL` | Soft-deprecation timestamp |
| `deprecation_message` | `TEXT` | | `NULL` | Reason for deprecation |
| `metadata` | `JSONB` | NOT NULL | `'{}'` | Tags, categories, links, etc. |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes/Constraints:**
- `UNIQUE(tenant_id, agent_slug)` — agent names unique within a tenant
- `idx_agents_slug ON agents(agent_slug)` — for cross-tenant search by name
- `idx_agents_visibility ON agents(visibility)` — for public agent listing
- `idx_agents_updated ON agents(updated_at DESC)` — for "recently updated" sorting
- Consider: `GIN(to_tsvector('english', description))` for full-text search on description (add when search volume justifies it)

##### Table 5: `agent_versions`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `agent_id` | `UUID` | FK → agents.id, NOT NULL | — | ON DELETE RESTRICT |
| `version` | `TEXT` | NOT NULL | — | Semver string, e.g. "0.3.1" |
| `manifest` | `JSONB` | NOT NULL | — | Full kinnoo.yaml content |
| `storage_key` | `TEXT` | NOT NULL | — | S3 object key for the .kno archive |
| `signature_key` | `TEXT` | | `NULL` | S3 object key for .sig file |
| `sha256` | `TEXT` | NOT NULL | — | Archive checksum |
| `archive_size` | `BIGINT` | | `NULL` | Archive size in bytes |
| `publisher_id` | `UUID` | FK → users.id, NOT NULL | — | Who published this version |
| `security_status` | `TEXT` | NOT NULL | `''` | Post-publish scan result |
| `security_report` | `JSONB` | | `NULL` | Detailed scan findings |
| `download_count` | `BIGINT` | NOT NULL | `0` | Denormalized counter (updated periodically from download_events) |
| `yanked_at` | `TIMESTAMPTZ` | | `NULL` | Soft-removal timestamp |
| `yank_reason` | `TEXT` | | `NULL` | Why this version was yanked |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes/Constraints:**
- `UNIQUE(agent_id, version)` — version strings unique within an agent
- `idx_versions_publisher ON agent_versions(publisher_id)`
- `idx_versions_created ON agent_versions(created_at DESC)` — for "recently published" feed
- `idx_versions_not_yanked ON agent_versions(agent_id) WHERE yanked_at IS NULL` — partial index for active versions only

##### Table 6: `api_keys`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `user_id` | `UUID` | FK → users.id, NOT NULL | — | ON DELETE CASCADE |
| `tenant_id` | `UUID` | FK → tenants.id, NOT NULL | — | Scoped to a namespace |
| `key_prefix` | `TEXT` | NOT NULL | — | First 8 chars, e.g. "kno_a1b2" for display |
| `key_hash` | `TEXT` | UNIQUE, NOT NULL | — | SHA-256 of full key |
| `name` | `TEXT` | NOT NULL | — | User-chosen label, e.g. "GitHub Actions" |
| `scopes` | `TEXT[]` | NOT NULL | — | Postgres array, e.g. `{'registry:publish','registry:read'}` |
| `expires_at` | `TIMESTAMPTZ` | | `NULL` | NULL = never expires |
| `last_used_at` | `TIMESTAMPTZ` | | `NULL` | Updated on each use |
| `revoked_at` | `TIMESTAMPTZ` | | `NULL` | Soft-revocation |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes/Constraints:**
- `UNIQUE(key_hash)` — for O(1) lookup during auth
- `idx_apikeys_user ON api_keys(user_id)`
- `idx_apikeys_tenant ON api_keys(tenant_id)`
- `idx_apikeys_active ON api_keys(key_hash) WHERE revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())` — partial index for active keys

##### Table 7: `audit_log`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `actor_id` | `UUID` | FK → users.id | `NULL` | Nullable for system events |
| `action` | `TEXT` | NOT NULL | — | Dot-namespaced action string (see action table above) |
| `resource_type` | `TEXT` | NOT NULL | — | `'user'`, `'tenant'`, `'agent'`, `'agent_version'`, `'api_key'` |
| `resource_id` | `UUID` | | `NULL` | ID of affected resource |
| `tenant_id` | `UUID` | FK → tenants.id | `NULL` | For tenant-scoped filtering |
| `details` | `JSONB` | NOT NULL | `'{}'` | Action-specific structured data |
| `ip_address` | `INET` | | `NULL` | Postgres INET type |
| `user_agent` | `TEXT` | | `NULL` | HTTP User-Agent |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | Append-only — no updated_at |

**Indexes:**
- `idx_audit_action ON audit_log(action)`
- `idx_audit_actor ON audit_log(actor_id)`
- `idx_audit_tenant ON audit_log(tenant_id)`
- `idx_audit_created ON audit_log(created_at DESC)`
- `idx_audit_resource ON audit_log(resource_type, resource_id)`

**Partitioning consideration (future):** If audit_log grows large, partition by `created_at` month. Not needed at launch.

##### Table 8: `download_events`

| Column | Type | Constraints | Default | Notes |
|---|---|---|---|---|
| `id` | `UUID` | PK | uuid7() | |
| `agent_version_id` | `UUID` | FK → agent_versions.id, NOT NULL | — | |
| `downloader_id` | `UUID` | FK → users.id | `NULL` | Nullable if anonymous downloads are allowed |
| `ip_address` | `INET` | | `NULL` | |
| `user_agent` | `TEXT` | | `NULL` | |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | |

**Indexes:**
- `idx_downloads_version ON download_events(agent_version_id)` — for per-version download count
- `idx_downloads_created ON download_events(created_at DESC)` — for time-range queries
- `idx_downloads_user ON download_events(downloader_id)` — for "what has this user downloaded?" queries

---

#### 10. Additional Tables Considered but Not Included

| Table idea | Decision | Reasoning |
|---|---|---|
| `workspaces` | **Defer** | Future feature. Schema designed above, ready for Alembic migration when needed. |
| `workspace_members` | **Defer** | Same. |
| `tags` / `agent_tags` | **Skip** | Tags can live in `agents.metadata` JSONB for now. If tag-based search becomes critical, extract to a separate table later. |
| `rate_limits` | **Skip** | Keep in-memory for launch. Move to Redis or Postgres if multi-instance rate limiting is needed. |
| `webhooks` | **Skip** | Future feature for "notify me when agent X publishes a new version." Not needed for launch. |
| `notifications` | **Skip** | Future feature. |

---

#### Summary: Final Table Count and Column Count

| # | Table | Columns | New or Replaces |
|---|---|---|---|
| 1 | `users` | 10 | Replaces UserStore JSON + SQLite users |
| 2 | `tenants` | 8 | Replaces TenantStore JSON + SQLite tenants |
| 3 | `tenant_members` | 5 | New (multi-user tenant access) |
| 4 | `agents` | 11 | Replaces AgentIndex + GlobalIndex JSON |
| 5 | `agent_versions` | 16 | Replaces VersionMetadata JSON |
| 6 | `api_keys` | 12 | New (CI/CD headless auth) |
| 7 | `audit_log` | 10 | New (per db.rules.md) |
| 8 | `download_events` | 6 | New (analytics) |
| **Total** | **8 tables** | **78 columns** | |

---

## SWE Agent Implementation Spec — Gap Analysis & Resolutions (Round 3)

*Added 2026-04-18. This section addresses ambiguities an SWE agent would encounter
when translating the planning doc into code. Each item below was unspecified — the
SWE agent would have had to guess.*

---

### Gap 1: UUID7 Library

`db.rules.md` mandates UUID7 primary keys but doesn't say which Python library to use.

**Decision:** Use the `uuid-utils` package (`pip install uuid-utils`). It provides `uuid_utils.uuid7()` and is the most maintained UUID7 library for Python. Add it to `server/requirements.txt`.

```python
# In any model or factory:
from uuid_utils import uuid7
```

---

### Gap 2: `updated_at` Auto-Update Mechanism

`db.rules.md` asks "does the updated_at trigger work?" but doesn't say *how* to implement it.

**Decision:** Use SQLAlchemy's `onupdate` parameter on the column definition. Do NOT use a Postgres trigger (adds schema complexity) or an ORM event listener (easy to forget).

```python
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, func

def utc_now():
    return datetime.now(timezone.utc)

# In every model:
created_at: datetime = Field(
    sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
)
updated_at: datetime = Field(
    sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=utc_now, nullable=False)
)
```

---

### Gap 3: Gold-Standard SQLModel Template

The planning doc lists columns in tables but never shows the actual Python class definition.
An SWE agent unfamiliar with SQLModel + SQLAlchemy 2.0 async patterns will likely get
the UUID type, JSONB column, or relationship syntax wrong. Here is the canonical template
every model must follow:

```python
"""server/database/models/agent.py — Gold-standard model example."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Relationship
from sqlmodel import Field, SQLModel
from uuid_utils import uuid7

if TYPE_CHECKING:
    from server.database.models.agent_version import AgentVersion
    from server.database.models.tenant import Tenant


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: UUID = Field(default_factory=uuid7, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    agent_slug: str = Field(sa_column=Column(Text, nullable=False))
    visibility: str = Field(sa_column=Column(Text, nullable=False, server_default="public"))
    description: str = Field(sa_column=Column(Text, nullable=False, server_default=""))
    homepage_url: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    deprecated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    deprecation_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    metadata_: dict = Field(default_factory=dict, sa_column=Column("metadata", JSONB, nullable=False, server_default="{}"))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False))
    updated_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=utc_now, nullable=False))

    # Relationships — lazy="selectin" per db.rules.md
    tenant: "Tenant" = Relationship(back_populates="agents", sa_relationship_kwargs={"lazy": "selectin"})
    versions: list["AgentVersion"] = Relationship(back_populates="agent", sa_relationship_kwargs={"lazy": "selectin"})

    class Config:
        # Rename "metadata_" back to "metadata" in JSON serialization
        fields = {"metadata_": {"alias": "metadata"}}
```

**Key patterns the SWE agent must replicate for every model:**
- `table=True` on the class
- `__tablename__` explicit
- `default_factory=uuid7` for PK
- `sa_column=Column(...)` for non-trivial types (JSONB, INET, DateTime with timezone)
- `TYPE_CHECKING` guard for relationship type hints to avoid circular imports
- `Relationship(sa_relationship_kwargs={"lazy": "selectin"})` per db.rules.md
- `metadata_` with `Column("metadata", ...)` to avoid collision with SQLAlchemy's internal `.metadata` attribute

---

### Gap 4: Relationship Map

The planning doc shows FK columns but doesn't list which SQLAlchemy `Relationship` attributes
to define on each model or their `back_populates` names. Without this, the SWE agent
will invent inconsistent names.

| Model | Attribute | Type | Related model | back_populates | Notes |
|---|---|---|---|---|---|
| **User** | `owned_tenants` | `list[Tenant]` | Tenant | `owner` | Tenants this user owns |
| **User** | `tenant_memberships` | `list[TenantMember]` | TenantMember | `user` | |
| **User** | `published_versions` | `list[AgentVersion]` | AgentVersion | `publisher` | |
| **User** | `api_keys` | `list[ApiKey]` | ApiKey | `user` | |
| **Tenant** | `owner` | `User` | User | `owned_tenants` | |
| **Tenant** | `members` | `list[TenantMember]` | TenantMember | `tenant` | |
| **Tenant** | `agents` | `list[Agent]` | Agent | `tenant` | |
| **TenantMember** | `tenant` | `Tenant` | Tenant | `members` | |
| **TenantMember** | `user` | `User` | User | `tenant_memberships` | |
| **Agent** | `tenant` | `Tenant` | Tenant | `agents` | |
| **Agent** | `versions` | `list[AgentVersion]` | AgentVersion | `agent` | |
| **AgentVersion** | `agent` | `Agent` | Agent | `versions` | |
| **AgentVersion** | `publisher` | `User` | User | `published_versions` | |
| **ApiKey** | `user` | `User` | User | `api_keys` | |
| **ApiKey** | `tenant` | `Tenant` | Tenant | *(no back_populates)* | Not typically traversed from tenant → keys |

**Models with NO relationships defined:** `AuditLog`, `DownloadEvent`. These reference `users`, `tenants`, and `agent_versions` by FK but do NOT define ORM relationships. They are high-volume append-only tables — adding relationships would cause unintended eager loads.

---

### Gap 5: Exact File Layout for `server/database/`

```
server/database/
├── __init__.py
├── session.py              # create_engine_from_config(), create_session_factory(), Base
├── repository.py           # UserRepository, TenantRepository, AgentRepository,
│                           # AgentVersionRepository, ApiKeyRepository, AuditLogRepository,
│                           # DownloadEventRepository
├── exceptions.py           # RegistryEntryNotFoundError, DuplicateEntryError,
│                           # DatabaseConnectionError
├── models/
│   ├── __init__.py         # Re-exports all models (ensures Alembic sees them)
│   ├── agent.py            # Agent model
│   ├── agent_version.py    # AgentVersion model
│   ├── api_key.py          # ApiKey model
│   ├── audit.py            # AuditLog model
│   ├── download.py         # DownloadEvent model
│   ├── tenant.py           # Tenant model
│   ├── tenant_member.py    # TenantMember model
│   └── user.py             # User model
└── migrations/
    ├── alembic.ini          # Points to env.py, uses async driver
    ├── env.py               # Async Alembic env (see Gap 6)
    ├── script.py.mako       # Default template
    └── versions/
        └── 001_initial_schema.py  # Creates all 8 tables
```

`models/__init__.py` must import every model so Alembic's `--autogenerate` can discover them:

```python
from server.database.models.agent import Agent
from server.database.models.agent_version import AgentVersion
from server.database.models.api_key import ApiKey
from server.database.models.audit import AuditLog
from server.database.models.download import DownloadEvent
from server.database.models.tenant import Tenant
from server.database.models.tenant_member import TenantMember
from server.database.models.user import User

__all__ = [
    "Agent", "AgentVersion", "ApiKey", "AuditLog",
    "DownloadEvent", "Tenant", "TenantMember", "User",
]
```

---

### Gap 6: Alembic Async Configuration

Alembic does not natively support async engines. The SWE agent needs the exact `env.py`
pattern or it will write a sync env that fails at runtime.

```python
"""server/database/migrations/env.py"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from server.database.session import get_database_url
from server.database.models import *  # noqa: F401, F403 — register all models
from sqlmodel import SQLModel

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline():
    url = get_database_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    engine = create_async_engine(get_database_url())
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

**`alembic.ini` key settings:**

```ini
[alembic]
script_location = server/database/migrations
sqlalchemy.url = postgresql+asyncpg://localhost:5432/kinnoo_registry

# Naming convention for constraints (db.rules.md compliance)
[alembic:naming_convention]
ix = ix_%(column_0_label)s
uq = uq_%(table_name)s_%(column_0_name)s
ck = ck_%(table_name)s_%(constraint_name)s
fk = fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
pk = pk_%(table_name)s
```

---

### Gap 7: Repository Method Signatures

`db.rules.md` says "repository pattern" but the planning doc doesn't define what
methods each repository should expose. Here are the minimum required methods:

**`UserRepository`:**
```
get_by_id(id: UUID) -> User | None
get_by_kinde_id(kinde_user_id: str) -> User | None
get_by_email(email: str) -> User | None
list_all(offset: int, limit: int) -> list[User]
upsert_from_kinde(kinde_user_id: str, email: str, display_name: str) -> User  # JIT provision
update_role(id: UUID, role: str) -> User
deactivate(id: UUID) -> User
reactivate(id: UUID) -> User
```

**`TenantRepository`:**
```
get_by_id(id: UUID) -> Tenant | None
get_by_slug(slug: str) -> Tenant | None
list_all(offset: int, limit: int) -> list[Tenant]
create(slug: str, owner_id: UUID) -> Tenant
add_member(tenant_id: UUID, user_id: UUID, role: str) -> TenantMember
remove_member(tenant_id: UUID, user_id: UUID) -> None
list_members(tenant_id: UUID) -> list[TenantMember]
is_member(tenant_id: UUID, user_id: UUID) -> bool
```

**`AgentRepository`:**
```
get_by_id(id: UUID) -> Agent | None
get_by_slug(tenant_id: UUID, agent_slug: str) -> Agent | None
list_by_tenant(tenant_id: UUID, offset: int, limit: int) -> list[Agent]
list_public(offset: int, limit: int) -> list[Agent]
search(query: str, tenant_id: UUID | None, offset: int, limit: int) -> list[Agent]
create(tenant_id: UUID, agent_slug: str, visibility: str, description: str) -> Agent
update_visibility(id: UUID, visibility: str) -> Agent
deprecate(id: UUID, message: str) -> Agent
```

**`AgentVersionRepository`:**
```
get_by_id(id: UUID) -> AgentVersion | None
get(agent_id: UUID, version: str) -> AgentVersion | None
list_by_agent(agent_id: UUID, offset: int, limit: int) -> list[AgentVersion]
get_latest(agent_id: UUID) -> AgentVersion | None  # most recent non-yanked
create(agent_id: UUID, version: str, manifest: dict, storage_key: str, sha256: str, publisher_id: UUID, archive_size: int | None, signature_key: str | None) -> AgentVersion
yank(id: UUID, reason: str) -> AgentVersion
unyank(id: UUID) -> AgentVersion
```

**`ApiKeyRepository`:**
```
get_by_key_hash(key_hash: str) -> ApiKey | None
list_by_user(user_id: UUID) -> list[ApiKey]
create(user_id: UUID, tenant_id: UUID, key_prefix: str, key_hash: str, name: str, scopes: list[str], expires_at: datetime | None) -> ApiKey
revoke(id: UUID) -> ApiKey
update_last_used(id: UUID) -> None
```

**`AuditLogRepository`:**
```
create(actor_id: UUID | None, action: str, resource_type: str, resource_id: UUID | None, tenant_id: UUID | None, details: dict, ip_address: str | None, user_agent: str | None) -> AuditLog
list_recent(limit: int, offset: int, action: str | None, actor_id: UUID | None, tenant_id: UUID | None, since: datetime | None) -> list[AuditLog]
```

**`DownloadEventRepository`:**
```
create(agent_version_id: UUID, downloader_id: UUID | None, ip_address: str | None, user_agent: str | None) -> DownloadEvent
count_by_version(agent_version_id: UUID) -> int
count_by_agent(agent_id: UUID) -> int
top_downloaded(limit: int) -> list[tuple[UUID, int]]  # (agent_id, count)
```

---

### Gap 8: Custom Exceptions

`db.rules.md` says "define custom DB exceptions." Here is the list:

```python
"""server/database/exceptions.py"""

class DatabaseError(Exception):
    """Base for all registry DB errors."""

class RegistryEntryNotFoundError(DatabaseError):
    """Raised when a queried entity does not exist."""
    def __init__(self, entity: str, identifier: str):
        super().__init__(f"{entity} not found: {identifier}")
        self.entity = entity
        self.identifier = identifier

class DuplicateEntryError(DatabaseError):
    """Raised when a unique constraint would be violated."""
    def __init__(self, entity: str, field: str, value: str):
        super().__init__(f"{entity} with {field}={value} already exists")
        self.entity = entity
        self.field = field
        self.value = value

class DatabaseConnectionError(DatabaseError):
    """Raised when the database is unreachable."""
```

Repositories raise these instead of letting raw `IntegrityError` or `NoResultFound`
propagate. Route handlers catch them and return appropriate HTTP status codes
(404, 409, 503).

---

### Gap 9: Appendix Open Questions — Default Answers for SWE Agent

The Appendix (Round 1) listed 6 open questions for the operator. If these remain
unanswered when the SWE agent starts, it will guess. Here are safe defaults the SWE
agent should use unless the operator overrides:

| # | Question | Default for SWE agent |
|---|---|---|
| 1 | Kinde org_code → tenant mapping | **Independent.** Users self-create tenants. Kinde org_code is stored on the user's JWT but is NOT automatically mapped to a tenant. Mapping can be added later. |
| 2 | API key format | `kno_` prefix + 32 bytes base62-encoded. Example: `kno_a1B2c3D4e5F6g7H8j9K0m1N2p3Q4r5S6`. SHA-256 hash stored in DB. |
| 3 | Download anonymity | **Auth required for all downloads** (current behavior). Unauthenticated download of public agents can be added later by making `downloader_id` nullable. |
| 4 | Version immutability | **Immutable.** Server returns 409 on duplicate version. `yanked_at` is the only way to soft-remove. |
| 5 | Tenant creation policy | **Admin-only** (current behavior). Self-service can be added later via a config flag. |
| 6 | Separate features for Phase 2 vs Phase 3? | **Yes, separate.** Phase 2 (Postgres data layer) does NOT depend on Phase 3 (Kinde auth swap). The `users` table should be built with the `kinde_user_id` column from day one (nullable until Kinde ships), but the JIT provisioning logic belongs to Phase 3. |

---

### Gap 10: How `create_app()` Wiring Changes

The planning doc describes the feature flag but doesn't show how the session factory
and repositories integrate into `create_app()`. This is where most "glue" bugs happen.

**Current pattern (from `server/app.py`):**

```python
# Today — everything wired directly:
metadata_manager = MetadataManager(storage=storage_backend)
user_store = UserStore(root=local_storage_root)
tenant_store = TenantStore(root=local_storage_root)
```

**New pattern with feature flag:**

```python
from server.database.session import create_engine_from_config, create_session_factory

# Postgres setup (always create engine if URL is configured — needed for CLI commands too)
db_engine = None
db_session_factory = None
if config.database_url:
    db_engine = create_engine_from_config(config)
    db_session_factory = create_session_factory(db_engine)

# Metadata manager: feature flag
if config.metadata_backend == "postgres":
    if db_session_factory is None:
        raise RuntimeError("REGISTRY_DATABASE_URL is required when metadata_backend=postgres")
    metadata_manager = PostgresMetadataManager(session_factory=db_session_factory)
else:
    metadata_manager = MetadataManager(storage=storage_backend)

# User/tenant stores: always keep JSON stores for now (until Kinde feature ships)
user_store = UserStore(root=local_storage_root)
tenant_store = TenantStore(root=local_storage_root)

# Inject session factory into app state for routes that need direct DB access
app.state.db_session_factory = db_session_factory
```

The SWE agent should NOT replace `UserStore` or `TenantStore` in this feature — that
happens in the Kinde auth feature (PRE-RELEASE FEATURE 1). Phase 2 only replaces the
metadata layer.

---

### Gap 11: `server/database/session.py` — Full Implementation

The session.py code was sketched in Round 2 but incomplete. Here is the full file
the SWE agent should create:

```python
"""server/database/session.py — Async engine and session factory."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

# Base metadata — all models register against this via SQLModel
Base = SQLModel.metadata


def get_database_url() -> str:
    """Read DB URL from environment. Used by Alembic and CLI."""
    url = os.getenv("REGISTRY_DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "REGISTRY_DATABASE_URL is not set. "
            "Example: postgresql+asyncpg://user:pass@localhost:5432/kinnoo_registry"
        )
    return url


def create_engine_from_url(
    url: str,
    *,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_recycle: int = 3600,
    echo: bool = False,
) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        echo=echo,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

---

### Gap 12: Sync Engine for CLI Commands

The CLI commands (Round 2, section 2) use a **synchronous** engine because CLI scripts
don't run an async event loop. The SWE agent needs to know how to create the sync engine
and avoid mixing it with the async server engine.

```python
"""In server/cli.py or a helper module server/database/cli_session.py"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

def create_sync_engine_for_cli(database_url: str):
    """Convert async URL to sync for CLI use."""
    # asyncpg URL: postgresql+asyncpg://...
    # psycopg2 URL: postgresql+psycopg2://... or just postgresql://...
    sync_url = database_url.replace("+asyncpg", "+psycopg2")
    return create_engine(sync_url)

def create_sync_session(engine) -> Session:
    return Session(engine)
```

This means `psycopg2-binary` (or `psycopg[binary]`) must also be added to
`server/requirements.txt` alongside `asyncpg`.

---

### Summary of New Dependencies

Add to `server/requirements.txt`:

```
# Database
sqlalchemy[asyncio]>=2.0.0
sqlmodel>=0.0.14
alembic>=1.13.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.0
uuid-utils>=0.9.0
```
