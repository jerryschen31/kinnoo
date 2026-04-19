
**PRE-RELEASE FEATURE 1**
[todo]
get Kinde Auth setup in codebase - will replace current Auth in dev

[definition of done]
- Kinde tenant configured with dev and staging environments
- server/ auth routes accept and validate Kinde-issued OIDC/JWT tokens
- `kinnoo login` CLI flow redirects to Kinde-hosted login and receives token back
- `kinnoo logout` clears local auth state and invalidates session
- Web UI login/register flows use Kinde instead of custom auth forms
- Existing SQLite-based user_store.py and session.py auth retired or adapted to Kinde identity
- Server rejects requests with expired or invalid Kinde tokens with clear error messages
- All existing server tests that test auth pass with Kinde-based flow (or are updated)
- Token refresh flow works without requiring re-login within a reasonable window

**PRE-RELEASE FEATURE 2**
[todo]
Replace the server's JSON-file and SQLite data stores with a Postgres database so the agent registry can handle concurrent users, search efficiently, and persist data reliably.

High-level work items:
1. Define Postgres schema — 8 tables (users, tenants, tenant_members, agents, agent_versions, api_keys, audit_log, download_events) using SQLAlchemy 2.0 models and Alembic migrations
2. Build a new data-access layer (repository classes) so server routes never contain SQL — they call repositories instead
3. Create a PostgresMetadataManager that replaces the current JSON-backed MetadataManager while keeping the same interface, so existing API routes work without changes
4. Add a feature flag (json vs postgres backend) for a gradual migration — the old JSON store keeps working until Postgres is validated
5. Add read-only `kinnoo-server db` CLI commands for admin querying (list tables, search agents, inspect versions, view audit logs, etc.)
6. Set up local dev Postgres via Docker Compose and CI Postgres via GitHub Actions service container
7. Write tests against real Postgres with per-test transaction rollback for isolation
8. Add connection management, health checks, and environment-variable-driven configuration
9. UserStore, TenantStore, and SQLite auth-store replacement is gated on Feature 1 Kinde integration readiness.

[definition of done]
- SQLAlchemy 2.0 async models defined for all 8 tables in server/database/models/, following db.rules.md patterns (UUID7 PKs, audit timestamps, JSONB metadata, repository pattern)
- Alembic migration directory created with initial migration that stands up the full schema
- Repository classes exist for every entity (UserRepository, TenantRepository, AgentRepository, AgentVersionRepository, etc.) — no SQL in route handlers
- PostgresMetadataManager implements the same interface as the current MetadataManager and passes the same tests
- Feature flag (REGISTRY_METADATA_BACKEND=json|postgres) controls which backend the server uses; "json" remains the default until switchover
- ~28 read-only `kinnoo-server db` CLI commands work (schema inspection, agent/version/user/tenant/audit queries, stats)
- Docker Compose file for local Postgres dev environment; CI workflow includes Postgres service container
- Server tests run against real Postgres with transaction rollback per test — no leaked state between tests
- Connection pool settings, DB health check on /health, and fail-fast startup behavior are implemented and configurable via env vars
- Audit log captures all registry-modifying actions (publish, yank, user/tenant/key changes, security events)
- Detailed planning and column specs documented in notes/features/postgres-registry-db-planning.md

**PRE-RELEASE FEATURE 3**
[todo]
remove mock-server/. For any tests that previously used this mock server, have the tests use corresponding components in server/ instead.
Some tests that previously used mock-server/ may need to be deprecated as a result of deleting mock-server/. Intelligently determine which tests should be deprecated and which tests need to be migrated to use server/ instead.

[definition of done]
- mock-server/ directory is deleted from the repository
- All tests that imported from or referenced mock-server/ are either migrated to use server/ components or deprecated with explicit skip reasons
- No remaining references to mock-server in any test file, import, or config
- Full pytest suite passes after removal

**PRE-RELEASE FEATURE 4**
[todo]
clearly define which files and folders in the codebase should be mirrored in the public repo

[definition of done]
- A documented manifest (e.g., PUBLIC-REPO-MANIFEST.md or a script) that lists every included and excluded directory/file
- Excluded: notes/, scratch/, internal scripts, .github agent files, internal planning docs, env/ config with secrets
- Included: src/, tests/, server/, web/, docs/, iac/, scripts/ (public subset), pyproject.toml, requirements.txt, README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md
- A reproducible script or CI step that can build the public repo from the private repo using the manifest
- Running the script produces a clean repo with no internal-only content

**PRE-RELEASE FEATURE 5**
[todo]
update public documentation - improve readibility and comprehensiveness

[definition of done]
- docs/getting-started.md walks a new user from `pip install kinnoo` through init, run, pack, publish, install in under 10 minutes
- docs/cli-reference.md covers every CLI subcommand with usage, flags, and examples — current with latest CLI behavior
- docs/kinnoo-yaml-spec.md covers every manifest field (required and optional) with examples and constraints
- docs/registry-guide.md covers publishing, searching, installing from registry, and authentication
- docs/security-model.md covers signing, checksums, permissions, sandbox model, and trust baseline
- README.md is polished for public consumption: clear value prop, quickstart, link to full docs
- No broken internal links, no references to internal notes or scratch files
- All code examples in docs are tested or verified to work with current CLI version

**PRE-RELEASE FEATURE 6**
[todo]
Harden `kinnoo import` for production-quality robustness. The import command already exists and works for basic cases — this is a HARDENING pass, not a greenfield build. The goal is to make existing import paths robust, error-free, and well-tested for a focused set of AI agent frameworks.

High-level work items:
1. Error hardening — graceful handling of edge-case inputs (empty directories, unsupported languages, ambiguous project structures); ensure every generated manifest passes kinnoo's own validation; standardize all error messages to a consistent, actionable format
2. LangChain adapter hardening — detect sub-package imports (langchain-openai, langchain-anthropic, etc.), infer framework-specific dependencies and environment variables, validate project structure has actual chain/agent construction
3. LangGraph adapter hardening — detect graph construction patterns (StateGraph, compile()), infer dependencies from both langgraph and langchain sub-packages, support Python and Node.js projects
4. OpenAI adapter hardening — distinguish OpenAI base SDK from OpenAI Agents SDK, infer correct dependencies and env vars for each, validate Agent() instantiation for Agents SDK
5. OpenClaw agent import — new `--from openclaw` flow that imports an OpenClaw agent workspace (copies SOUL.md, IDENTITY.md, memory/, skills/ etc. to a target directory, excluding .git/.openclaw/.clawhub, and generates kinnoo.yaml). NOTE: kinnoo now supports OpenClaw workspace-based agents, NOT individual skills from ClawHub
6. Dependency detection improvements — add Poetry pyproject.toml support, framework sub-package dependency inference
7. Generic LLM agent support — basic Python or JS/TS agents that use LLM libraries directly (not a specific framework) should import cleanly with detected env vars and dependencies
8. Tests — edge-case integration tests, framework-specific adapter tests, manifest validation regression tests; use real open-source agents from GitHub as test fixtures where possible, or create realistic example agents that match real-world project structures

[definition of done]
- `kinnoo import` produces no crash or traceback on any directory input (empty, unsupported language, ambiguous structure, large projects)
- Every generated kinnoo.yaml passes kinnoo's own validation
- LangChain adapter detects sub-package imports (langchain-openai, langchain-anthropic, etc.) and infers correct dependencies
- LangGraph adapter detects graph construction patterns and infers langgraph + langchain dependencies
- OpenAI adapter correctly distinguishes base SDK from Agents SDK and sets appropriate framework value
- `kinnoo import --from openclaw <target> <workspace-path>` copies OpenClaw agent workspace files (excluding .git, .openclaw, .clawhub) and generates valid kinnoo.yaml with framework: openclaw
- Poetry pyproject.toml dependencies are parsed during import
- All error messages follow consistent format with actionable guidance
- Integration tests cover: empty directory, unsupported language, Python happy path, Node.js happy path, each framework adapter, OpenClaw agent import, existing kinnoo.yaml collision
- Framework detection is accurate — detected LangGraph agent is truly LangGraph, not misidentified LangChain, etc.
- At least 30 import-related tests pass across test files
- Test fixtures include real open-source agent structures or realistic synthetic agents that match real-world project layouts

**PRE-RELEASE FEATURE 7**
[todo]
create staging environment and associated codebase changes and deliverables for staging environment
this staging environment and deliverables should be easily configured to become the latest production environment with minimal configuration toggle

[definition of done]
- Staging infra deployed on AWS (ECS/Fargate or equivalent) with Postgres, S3, and Kinde staging tenant
- Server runs against staging Postgres and S3 (not SQLite and local filesystem)
- Environment-specific config driven by env vars or a single config toggle (e.g., KINNOO_ENV=staging vs production)
- staging.kinnoo.ai resolves and serves the registry web UI and API
- Cloudflare Worker for deploying staging.kinnoo.ai brought under IAC, if possible 
- CLI can target staging registry via `KINNOO_REGISTRY_URL` or config file
- Smoke tests (init, pack, publish, search, install, run) pass end-to-end against staging
- Deployment runbook documented: how to deploy, how to promote staging to production
- Dev secrets and placeholder values (dev-secret-change-me, dev-k1) replaced with env-injected production-grade secrets

**PRE-RELEASE FEATURE 8**
[todo]
secret scan and git history sanitization before public repo push
Run automated secret scanning on full git history (not just current files). Remove or rotate any credentials found. Decide keep-history vs fresh-history per the decision gate in notes/src-history-public-release-checklist.md.

[definition of done]
- Automated secret scan run against full git history for src/, server/, tests/, scripts/, docs/, web/, iac/ (e.g., using gitleaks, trufflehog, or git log grep)
- Zero real credentials, API keys, private keys, or tokens found in any historical commit
- If any leak found: credential rotated AND history rewritten or fresh-history approach chosen
- Personal identifiers (names, machine-specific paths, internal hostnames) reviewed and removed from code defaults
- No unsafe deserialization patterns (pickle.loads on untrusted data, unsafe YAML loading) in current codebase
- Audit record completed with date, scanner used, findings summary, and publish decision
- Sign-off recorded in docs/public-release-signoff.md

**PRE-RELEASE FEATURE 9**
[todo]
PyPI package publication pipeline
Set up trusted publisher (OIDC) on PyPI so `pip install kinnoo` works. Create a release workflow that builds, tests, and publishes the package on tagged releases.

[definition of done]
- PyPI trusted publisher configured for the kinnoo GitHub repository (OIDC, no static API token)
- GitHub Actions release workflow (.github/workflows/pypi-publish.yml) triggers on version tags (e.g., v0.8.0)
- Release workflow builds sdist + wheel, runs full pytest, and publishes to PyPI only on success
- `pip install kinnoo` installs the CLI with the `kinnoo` entry point working correctly
- `kinnoo --version` prints the correct version after pip install
- pyproject.toml metadata (description, URLs, classifiers, license) is complete and accurate for PyPI listing
- At least one successful test publish to TestPyPI before going live

**PRE-RELEASE FEATURE 10**
[todo]
CI/CD pipeline hardening for public repo confidence
Expand CI to cover the full test surface (client tests, server tests, web tests) and ensure reliability for external contributors.

[definition of done]
- CI runs full client pytest suite (tests/) on Ubuntu and macOS
- CI runs server pytest suite (server/tests/) with test Postgres (e.g., service container)
- CI runs web frontend tests (web/__tests__/) with Node.js
- CI runs the manifest validator script (scripts/validate_project_manifests.py)
- CI blocks PR merge on any test failure
- CI workflow completes in under 15 minutes for a typical PR
- CONTRIBUTING.md documents how to run tests locally and what CI checks

**PRE-RELEASE FEATURE 11**
[todo]
registry seeding with starter agents
Publish a small set of real, working example agents to the registry so new users have something to discover, install, and learn from on day one.

[definition of done]
- At least 3 agents published to the registry, spanning different frameworks (e.g., one OpenAI, one Gemini, one PydanticAI or LangGraph)
- At least 1 agent is signed with a keypair
- Each seeded agent: installs cleanly via `kinnoo install`, runs successfully with a sample input, has a clear README
- `kinnoo search` returns seeded agents
- Evidence of successful search/install/run captured (output logs or screenshots)
- Agent source available in a public examples/ directory or separate repo for reference
