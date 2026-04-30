I read issue #394 (and your 4 follow-up comments) and walked the codebase to inventory the boundary. Below is the plan — no code is moved or modified. I'm writing it the way I'd hand it to a backend-leaning engineer who isn't deep in Next.js, so I spend a little extra time on the web side and the auth/API seam that you (correctly) flagged as the risky part.

<plan>

## 1. What we actually have today (so the split makes sense)

Before deciding what goes where, here's the layout I confirmed by walking the tree:

| Path | Role | Repo target |
|---|---|---|
| `src/kinnoo/` (~23k LOC, ~50 modules) | Python CLI. Talks to server **only** over HTTP via `remote_client.py` (stdlib `urllib`). **No `import server.*` anywhere.** Deps: PyYAML, cryptography. | **Public** |
| `web/` | Next.js 16 + React 19 frontend, OpenNext on Cloudflare, vitest tests in `web/__tests__/`. Deps on backend are HTTP only (`web/lib/registry-client.ts`, `web/lib/auth-client.ts`, `web/app/api/[...path]/route.ts` proxy). | **Public** |
| `server/` | FastAPI app: `api/`, `auth/` (OIDC, sessions, tokens), `routes/`, `services/`, `storage/`, `models/`, `database/`, `bootstrap.py`, `app.py`, plus `server/tests/`. | **Private** |
| `iac/` | Terraform (modules, environments, state, prod state). | **Private** |
| `lambda_handler.py` (root) | AWS Lambda for post-publish archive security checks. Imported by `tests/registry_integration/test_lambda_handler.py`. | **Private** |
| `notes/` (~4.8 MB) | Internal docs, design, handoffs. | **Private** (already convention) |
| `docs/` | User-facing: cli-reference, getting-started, kinnoo-yaml-spec, registry-guide, security-model, supported-agents, CHANGELOG. | **Public** (mostly — see §3) |
| `tests/` (33 subdirs) | Mostly CLI behavior tests, but **8 files cross-import `server.*`** (see §3). | **Split** (most public, some private) |
| `scripts/` | Mixed: CLI release (`pypi-release.sh`, `publish_agent/`), ops/infra (`start_registry_server`, `cloudflared-tunnel-config.sh`, `postgres_backfill.py`, `add-registry-secrets.sh`), and shared dev tooling (`validate_project_manifests.py`, `commit-and-push-task-git.sh`, `next-task-git.sh`). | **Split** |
| Root files: `pyproject.toml`, `requirements.txt`, `Dockerfile`, `Dockerfile.lambda`, `docker-compose.yml`, `lambda_handler.py`, `mvp.md`, `vision.md`, `EPICS.txt`, `FEATURES.txt`, `TASKS.txt`, `TESTS.txt` | Mixed | **Split, with both repos getting a tailored copy of some** |

The good news: **the CLI and web are already cleanly decoupled from `server/` at the import level.** The only coupling is at the HTTP contract. That's why simple file-splits (your stated preference — no API refactor) are realistic.

## 2. The cross-cutting code (the part you were worried about)

I grepped for any code crossing the frontend/backend line. Here's what I found and how I'd handle each.

### 2a. CLI → server
- **Imports:** zero. `src/kinnoo/*.py` never imports `server.*`.
- **Auth code in CLI** (`src/kinnoo/auth_command.py`): this is the *client* side of an OIDC PKCE flow — opens a local callback HTTP server on a few well-known ports, builds the auth URL, exchanges the code for a token, persists it via `config.py`. It hits the server's OIDC endpoints (`/auth/...`) by URL only. **Stays with the CLI in public.**
- **Remote registry client** (`src/kinnoo/remote_client.py`): pure `urllib` HTTP client. **Public.** It is the contract surface. Treat its expected request/response shapes as the API contract.
- **`registry_backend.py` / `registry_backends.py` / `registry.py`**: local + remote registry abstractions used by the CLI. **Public.**

> Recommendation: write down the registry HTTP contract (endpoints, request bodies, response schemas, error codes) in a `docs/api-contract.md` (public) **before** the split. This becomes the source of truth that both repos must respect. It doesn't require an API refactor — you're just *documenting what already exists*. Without this, the public repo loses the ability to break-detect when the private API changes.

### 2b. Web → server
- **Web has no Python imports** of `server/`. All coupling is HTTP, via:
  - `web/lib/registry-client.ts`, `web/lib/auth-client.ts`
  - `web/app/api/[...path]/route.ts` — a generic proxy route to the backend.
  - Server URL is configured (you'll need to confirm exactly how — env var via `wrangler*.jsonc`).
- **Recommendation:** the public repo's web app should reference the backend purely via an env var (e.g. `KINNOO_API_BASE_URL`) and never hardcode a private URL. Audit `wrangler.jsonc` and `wrangler.prod.jsonc` for any leaked private hostnames or AWS account IDs before publishing.

### 2c. Tests → server (the *real* mess)
This is where the split is awkward. These test files **import `server.*`** and live in CLI-flavored test folders:

- `tests/registry_integration/test_web_auth_oidc_logout.py` (web auth router)
- `tests/registry_integration/test_oidc_error_handling.py`
- `tests/registry_integration/test_remote_client.py` — pure CLI, **public**
- `tests/registry_integration/test_lambda_handler.py` — imports root `lambda_handler` → **private**
- `tests/client_cli_registry/test_registry.py` — imports `server.app`, `server.bootstrap`, `server.config`, `server.middleware`, `server.models.user`, `server.routes.publish`, `server.storage.user_store`. This is a CLI integration test that spins up the real backend in-process. It's the trickiest case.
- `tests/e2e_workflows/test_feature_{89,90,91,100,102}.py` — end-to-end tests that boot the server.
- `tests/e2e_workflows/test_web_frontend_setup.py` — spins up the Next.js dev server with `subprocess`. Pure web. **Public.**

**Recommendation for the cross-cutting tests:** for each file, classify it as one of:

1. **CLI-only** (no `server.*` import) → public.
2. **Server-only** (under `server/tests/` or e2e that's really testing the API) → private.
3. **True end-to-end (CLI ↔ server, or web ↔ server)** → keep these in the **private** repo (because that's where both halves exist) and replace them in the public repo with **HTTP-contract tests** that hit a *fake* server (httpx mock, `responses`, or a tiny `http.server` fixture) implementing the documented contract from §2a. This is the safest pattern: the public repo asserts "given this HTTP behavior, the CLI does X"; the private repo asserts "the server actually produces this HTTP behavior."

This is exactly the kind of contract-vs-integration test split that prevents the two repos from drifting silently.

### 2d. Conftest / shared test infra
- `tests/conftest.py` references deprecated nodeids from both `tests/...` and `server/tests/...`. It needs to be split into one for each repo, with the relevant subset of `_DEPRECATED_TEST_NODEIDS` and `_DEPRECATED_TEST_PREFIXES`.
- `tests/helpers.py`, `tests/marker_tools.py` — appear CLI-flavored. Audit and copy what each repo needs.
- `tests/fixtures/` — audit per-fixture; many will be CLI-only.

### 2e. `pyproject.toml` and pytest config
Today `pyproject.toml` is a single CLI package definition (`name = "kinnoo"`, scripts entry `kinnoo = "kinnoo.cli:main"`) **plus** pytest config that references `server/tests`. After the split:
- **Public `pyproject.toml`:** keep package definition, drop `server_api` marker, drop `server/tests` from `testpaths`.
- **Private `pyproject.toml`:** new, separate, declares the server dependencies (FastAPI, etc. — currently in `server/requirements.txt`), `testpaths = ["server/tests", "tests/iac", ...]`.
- `requirements.txt` at root today is mixed; split into a public CLI-dev `requirements.txt` and a private server one (the `server/requirements.txt` already exists).

## 3. Docs, manifests, scripts, root files

### Docs (`docs/`)
- All current `docs/*.md` look user-facing → **public**.
- `vision.md`, `mvp.md`: public unless they mention private infra. **Action:** scan each for AWS account IDs, internal hostnames, secret-management procedures, and either redact or move to `notes/`.
- `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `LICENSE`, `NOTICE`, `README.md`: both repos need a copy; **rewrite the public README** to describe just CLI + web (current README likely mentions server setup).

### Manifests (FEATURES/TASKS/TESTS/EPICS) — the biggest organizational decision
You called this out: ~28k lines, intermingled. Options I'd weigh:

- **Option A — Split by ownership:** create `FEATURES.txt`/`TASKS.txt`/`TESTS.txt` in the public repo containing only entries whose tasks/tests are public-side; private repo keeps the rest. Pros: matches your custom-instruction workflow. Cons: cross-repo features (feature spans both) become very awkward; you'll need a "linked-feature" convention.
- **Option B — Keep all manifests private, add a thin `PUBLIC_FEATURES.md` in the public repo** that lists publicly tracked features by ID with brief descriptions. Pros: single source of truth for status. Cons: contributors to the public repo can't see the full plan; couples the two repos for any feature work.
- **Option C (recommended for this migration):** split (Option A), but introduce an `epic` convention to handle cross-repo work — an epic lives in both repos with the same ID (e.g. `epic42`) and each repo's FEATURES.txt declares only its own slice. Update `scripts/validate_project_manifests.py` so it doesn't fail on cross-repo references (e.g. allow a `external_repo: public` annotation that the validator ignores when resolving links).

Whichever option, **`scripts/validate_project_manifests.py` will need to be updated and present in both repos** (or at least the public one), and the deprecated-test maps in `conftest.py` need to drop entries that no longer exist on each side.

### Scripts (`scripts/`)
- **Public:** `validate_project_manifests.py` (probably both), `pypi-release.sh`, `publish_agent/`, `commit-and-push-task-git.sh`, `next-task-git.sh`, `check-for-python.sh`.
- **Private:** `add-dev-user.sh`, `add-registry-secrets.sh`, `cloudflared-tunnel-config.sh`, `load_kinnoo_auth_env.sh`, `start_registry_server`, `start_server_phase5`, `stop_registry_server`, `start_frontend_phase5`, `stop_frontend_phase5`, `postgres_backfill.py`, `postgres_parity.py`, `pr-merge-to-feature.sh`, `pr-merge-to-phase.sh`, `task496_step6_manual_validation.sh`, `ops/`, `ci-e2e-template.yml` (probably).
- `start_frontend_phase5` / `stop_frontend_phase5` look like they orchestrate the local web dev server — confirm whether they reference any private URLs/env before deciding.

### Root files
- **Public:** `pyproject.toml` (slimmed), `requirements.txt` (slimmed), public `README.md`, `LICENSE`, `NOTICE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.gitignore`, `.dockerignore` (slim), `Dockerfile` *only if* it builds the CLI (audit).
- **Private:** `Dockerfile.lambda`, `docker-compose.yml` (it almost certainly orchestrates the FastAPI server), `lambda_handler.py`, `EPICS.txt` (or split per Option C), `commit_message.txt`.
- `.github/`: split workflows by what they exercise. Anything that runs server tests, deploys IaC, or touches private secrets → private. CLI-build, web-build, vitest, public pytest → public.

## 4. Mock-public rollout (your comment suggestion) — concrete steps

You proposed staging the split inside this private repo via `mock-public/` and `code-backup/`. I think that's exactly right. Here's how I'd structure it:

**Layout to introduce (no code moved yet — this is the plan):**

```
mock-public/                  # the candidate public-repo contents
  src/kinnoo/                 # full copy of CLI
  web/                        # full copy of web
  tests/                      # only the CLI/web tests
  docs/                       # public docs
  scripts/                    # public scripts only
  pyproject.toml              # slimmed version
  requirements.txt            # slimmed version
  README.md                   # public-facing, rewritten
  FEATURES.txt / TASKS.txt / TESTS.txt   # public slice
  .github/workflows/          # public CI only
code-backup/                  # untouched copies of any file we modify-in-place
  MAP.md                      # original_path -> backup_path, with restore steps
```

### Stages
1. **Stage 0 — Documentation pass (no file moves).** Produce three artifacts in `notes/migration/`:
   - `inventory.md` — every path classified public/private/split (the table in §1, expanded to the file level).
   - `api-contract.md` — every CLI ↔ server endpoint and every web ↔ server endpoint, as it exists today. This is the contract the public repo will test against.
   - `cross-cutting-tests.md` — the 8 cross-importing test files from §2c with a per-file disposition (move, duplicate-as-contract-test, retire).

2. **Stage 1 — Build `mock-public/` by *copying* (not moving).** Copying preserves the working private repo while you validate. Use `cp -r` / `git cp`-equivalent so we can iterate without breaking anything.

3. **Stage 2 — Make `mock-public/` standalone-runnable.** From inside `mock-public/`:
   - `pip install -e .` (uses the slim `pyproject.toml`) succeeds.
   - `pytest` from `mock-public/` passes with **no reference to the private `server/`** (this is the critical gate — failing imports here = a hidden coupling we missed).
   - `cd mock-public/web && npm ci && npm run lint && npm test && npm run build` succeeds.
   - The CLI smoke-tests against a *mock* registry server (your existing `tests/client_cli_*` largely already do this via fakes — confirm).

4. **Stage 3 — Validate the *private* side still works without the public-only code.** Temporarily rename `src/`, `web/`, public-only `tests/*` directories at the repo root to e.g. `src.hidden/`, `web.hidden/`, etc. (or use a git worktree to checkout a "private-only" view). Run the private test suite (`server/tests`, `tests/iac`). Anything that fails reveals a hidden private→public coupling. Restore the renames.
   - The cleaner alternative: create `mock-private/` the same way and run its tests in isolation. More work but fewer foot-guns than renaming in place.

5. **Stage 4 — Use `code-backup/` for any file you must modify in place** (e.g., trimming `pyproject.toml`, splitting `conftest.py`). The required `code-backup/MAP.md` format:
   ```
   - original: pyproject.toml
     backup:   code-backup/pyproject.toml
     reason:   slimmed for public split
     restore:  cp code-backup/pyproject.toml pyproject.toml
   ```
   Treat anything that *only* gets moved (not edited) as not needing a backup — git history covers that.

6. **Stage 5 — Diff and dry-run the cutover.** Once both `mock-public/` and the implicit "mock-private" both pass, write a `notes/migration/cutover-runbook.md` with the exact `git mv` / `git rm` sequence, the order to do it in, and the rollback procedure.

7. **Stage 6 — Real cutover (detailed, safe, squashed-commit path)**

You said you prefer the **initial squashed commit** approach. Given that `master` and `build` are currently at the same HEAD in `kinnoo-project/kinnoo`, this is a good time to do it.

### Stage 6A. Preconditions (must be true before touching the public repo)
1. `mock-public/` passes all public gates from Stage 2:
    - Python: `pip install -e .` and `pytest`.
      - update: 244 passed, 188 skipped
    - Web: `npm ci && npm run lint && npm test && npm run build` in `mock-public/web/`.
      - update: 45 passed, 11 skipped.
2. Secret/PII scan is clean for the candidate public tree.
    - update: gitleaks rerun completed; findings reviewed and classified as dummy fixtures. [PASS]
3. You have a maintainer token/SSH access to push branches to `kinnoo-project/kinnoo`.

### Stage 6B. Make a temporary release snapshot from private repo
Run from the private repo root (this repo):

```bash
cd /Users/jerry/gh/kinnoo

# Safety check: ensure mock-public exists and has expected roots.
test -d mock-public/src/kinnoo && test -d mock-public/web && test -f mock-public/pyproject.toml

# Create an immutable snapshot tarball so you can always reproduce exactly what was migrated.
mkdir -p outputs/public-split
tar -czf outputs/public-split/mock-public-$(date +%Y%m%d-%H%M%S).tar.gz mock-public
```

### Stage 6C. Prepare a clean working clone of the public repo
Use a separate checkout so no local state leaks into the migration.

```bash
mkdir -p /tmp/kinnoo-public-cutover
cd /tmp/kinnoo-public-cutover

git clone git@github.com:kinnoo-project/kinnoo.git
cd kinnoo

# Confirm branch state.
git fetch origin --prune
git checkout build
git pull --ff-only origin build
git rev-parse --short HEAD
git rev-parse --short origin/master
```

What each command does:
- `git fetch origin --prune`: updates remote-tracking refs from `origin` and removes stale refs for deleted remote branches.
- `git checkout build`: switches your local working branch to `build`.
- `git pull --ff-only origin build`: updates local `build` from remote `build`, but only if it can fast-forward (prevents accidental merge commits).
- `git rev-parse --short HEAD`: prints the current checked-out commit SHA (short form).
- `git rev-parse --short origin/master`: prints the latest remote `master` SHA (short form) for comparison.

At this point, compare the two SHAs so you know whether `build` and `master` are still aligned before you start.

### Stage 6D. Create a dedicated migration branch in the public repo
```bash
git checkout -b chore/cli-and-web-code-migration-from-private
```

### Stage 6E. Replace public repo working tree with `mock-public/`
From `/tmp/kinnoo-public-cutover/kinnoo`:

```bash
# Copy the candidate public tree into this checkout.
rsync -a --exclude '.git' /Users/jerry/gh/kinnoo/mock-public/ ./

# Optional sanity checks.
test -d src/kinnoo
test -d web
test -f pyproject.toml
```

### Stage 6F. Run verification in the public checkout before committing
```bash
# Python checks
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
pytest

# CLI smoke
python src/kinnoo/cli.py --help
python src/kinnoo/cli.py init --help

# Web checks
cd web
npm ci
npm run lint
npm test
npm run build
cd ..

# Import boundary checks (must return no matches)
rg -n "^\s*(from|import)\s+server\b|import\s+lambda_handler\b" src tests || true
```

If anything fails, fix in private `mock-public/` first, then re-run Stage 6E in this temp checkout.

### Stage 6G. Commit as a single squashed baseline
```bash
git add -A
git status

git commit -m "chore: migrate Kinnoo CLI, web, tests, and docs to public repository"
```

Recommended richer commit message body:

```text
chore: migrate Kinnoo CLI, web, tests, docs, and other supporting docs to public repository

Migrate the Kinnoo open-source surface into the public repository as a
single baseline commit.

Includes:
- CLI code under src/kinnoo
- Web frontend under web/
- Public docs, tests, scripts, manifests, and CI workflows
- Other supporting files such as project files and notes

This is an intentional squashed baseline commit for the public split.
```

### Stage 6H. Push and open PR to public `build`
```bash
git push -u origin chore/cli-and-web-code-migration-from-private
```

Open a PR:
- Base: `build`
- Compare: `chore/cli-and-web-code-migration-from-private`
- Title: `chore: migrate Kinnoo CLI, web, tests, docs and other supporting files to public repository`
- In PR description, link the private migration plan and note this is intentionally squashed.

### Stage 6I. Post-merge branch strategy (build-only first)
Because you want to avoid touching `master` initially, keep this migration isolated to `build`.

```bash
git checkout build
git pull --ff-only origin build
```

Do not merge into `master` until you explicitly approve that next step. When ready later, open a separate PR from `build` to `master`.

### Stage 6J. Rollback procedure (if needed)
If migration PR is not merged: close PR and delete branch.

If merged into `build` and you need to roll back quickly:

```bash
git checkout build
git pull --ff-only origin build
git revert <bootstrap_commit_sha>
git push origin build
```

If you later promote this change to `master`, handle that rollback separately with its own revert PR.

### Notes on alternatives
- This Stage 6 uses the squashed baseline you requested.
- `git filter-repo` is still a valid alternative only if you later decide preserving per-file history is worth the complexity and secret-audit overhead.

## 5. Test plan — how to know the split is actually clean

1. **Per-side test isolation gate** (Stages 2 + 3 above): each side's test suite must pass in a checkout of *only* that side's files. This is the single most important check.
2. **Static import scan:** in `mock-public/`, run a grep for `from server`, `import server`, and `import lambda_handler` — must be empty. Run the inverse in the would-be private set against `from kinnoo`, `import kinnoo` — should also be empty (if not, that's a real coupling we need to either move or document as a contract).
3. **Contract tests:** for each cross-cutting test from §2c that we don't move, write a public-side replacement that exercises `RemoteRegistryClient` (and the web client) against a fixture HTTP server implementing the documented contract. These tests live in the public repo and are the canary for any private-side API change.
4. **Build matrix:**
   - Public: `pip install -e .`, `pytest`, `kinnoo --help`, `cd web && npm ci && npm run lint && npm test && npm run build`.
   - Private: `pytest server/tests`, `pytest tests/iac`, `pytest tests/registry_integration/test_lambda_handler.py`, terraform validate on `iac/`.
   - End-to-end (private only, since it has both halves): the existing `tests/e2e_workflows/test_feature_*.py` that boot the server.
5. **Manifest validator:** run `scripts/validate_project_manifests.py` on each repo independently. It must exit 0 on each side. (Likely needs the cross-repo annotation from §3 / Option C.)
6. **Secret/PII scan before publishing:** run `gitleaks` (or similar) against `mock-public/` and against the would-be initial public commit. Especially check `wrangler*.jsonc`, any `.env*` examples, `notes/` accidentally copied, and Docker files.
7. **Web smoke deploy to a non-prod Cloudflare env** from `mock-public/web/` to confirm that with only public env-vars and no private infra, the build + deploy still works.

## 6. Things to watch out for

1. **Auth flow split is the highest-risk surface.** `src/kinnoo/auth_command.py` (CLI side, public) and `server/auth/oidc.py` + `server/routes/web_auth.py` (server side, private) implement two halves of one OIDC PKCE flow. They must stay in lockstep on: callback path (`/auth/callback`), allowed callback ports `(8765, 8766, 9872, 49527)`, scope (`openid profile email`), token-refresh skew, and error-code semantics. Pin these as **explicit constants in the API contract doc**, and add a public contract test that asserts the CLI's expectations against a fake server.
2. **The `tests/client_cli_registry/test_registry.py` file is a landmine.** It imports half of `server/` to run an in-process integration. Don't try to keep it working on the public side. Move it to private as an integration test, and write a separate public CLI-only test that uses a fake HTTP backend.
3. **`pyproject.toml` `testpaths = ["tests", "server/tests"]`.** If you copy this to `mock-public/` unchanged, pytest will silently look for a `server/tests` dir that isn't there and either error or quietly find nothing — depending on pytest version. Fix early.
4. **`conftest.py` deprecated-test maps** reference both `tests/...` and `server/tests/...` nodeids. After the split, stale entries on either side will cause noise (or, worse, hide that a test is missing). Trim explicitly.
5. **`web/__tests__/wrangler-prod-config.test.ts`** asserts on production wrangler config. If `wrangler.prod.jsonc` references private infra (account ID, route, AI binding names), either redact those values to env-driven references or keep that specific test private. Audit before publishing.
6. **`tests/e2e_workflows/test_web_frontend_setup.py`** is a Python test that boots the Next.js dev server via subprocess. Two issues: (a) it lives in the Python tests folder but exercises web; (b) it has no `server.*` import but might assume the backend is reachable at some URL. Audit and decide whether to keep it on the public side as an isolated web smoke test or rewrite it as a vitest-side integration.
7. **`requirements.txt` at the repo root is mixed**, and `server/requirements.txt` exists separately. Make sure the public `requirements.txt` only contains what `src/kinnoo/` and dev tooling need (PyYAML, cryptography, pytest, the validator's PyYAML). FastAPI/SQLAlchemy/etc. must not leak.
8. **Docker.** `Dockerfile` at the root — read it carefully; if it builds the server, it's private. `Dockerfile.lambda` is private. `docker-compose.yml` almost certainly is private.
9. **GitHub Actions.** Workflows that use private secrets (AWS, Cloudflare prod, registry tokens) must not be copied to the public repo. Public CI should have its own minimal workflow set: lint, pytest CLI, vitest web, build web. No deploys.
10. **Manifest IDs (`featureN`, `taskN`, `testN`) are global counters today.** If you split them naively, both repos will start re-incrementing from different starting points and you'll get ID collisions on any future cross-repo epic. Pick one of: (a) keep monotonic global counter, with each repo "skipping" the other's IDs; (b) namespace IDs (`pub-feature1`, `priv-feature1`); (c) freeze old IDs and use epic-prefixed IDs going forward. (b) is simplest going forward; (a) preserves searchability of historical references.
11. **Public repo URL in `pyproject.toml`** currently points to `jerryjliu/kinnoo`. The actual public repo is `kinnoo-project/kinnoo`. Update `[project.urls]` during the split.
12. **`notes/` is 4.8 MB.** Make sure nothing under `notes/` ends up copied into `mock-public/`. Add `notes/` to a `.publicignore`-style allowlist check that runs as part of Stage 2.
13. **Git history.** If you want public-repo history to start clean, the simplest path is an initial squashed commit. If you want to preserve commit history of public files, use `git filter-repo --path src/kinnoo --path web --path docs --path tests/...` carefully. Either way, **scrub the history for secrets first**; once published, you can't take it back.
14. **CODEOWNERS / branch protection / CONTRIBUTING.md** for the public repo will need to be tailored to a public-contributor workflow (no `notes/` references, no internal Slack mentions, no `agent.md` references that point to private agent files).
15. **Custom-instruction agent workflow.** Your repo has a tech-lead/SWE/git agent workflow that depends on FEATURES/TASKS/TESTS being co-located with the code being changed. Decide before cutover how an agent working in the public repo should: (a) discover work, (b) update manifests, (c) reference cross-repo dependencies. The Option-C epic convention from §3 plus a public copy of `validate_project_manifests.py` is probably the minimum viable answer.

## 7. Suggested deliverable order (short version)

1. `notes/migration/inventory.md` (file-level classification).
2. `docs/api-contract.md` (HTTP contract — written from current code, no behavior change).
3. `notes/migration/cross-cutting-tests.md` (per-file disposition for the 8 bridging tests).
4. Build `mock-public/` by copy.
5. Slim `mock-public/pyproject.toml`, `requirements.txt`, `conftest.py`; record originals in `code-backup/` with `MAP.md`.
6. Stage-2 gate: `mock-public/` tests + builds pass standalone with `server/` invisible.
7. Stage-3 gate: private-only view tests pass with `mock-public/` invisible.
8. Write public-side contract tests to replace cross-cutting integration tests.
9. Decide manifest-ID strategy + update `validate_project_manifests.py`.
10. Secret/PII scan pass.
11. Write `notes/migration/cutover-runbook.md`. Stop. Hand back for human approval before any real `git mv`.

</plan>

Want me to start with deliverable #1 (the file-level `inventory.md`) or #2 (the `api-contract.md`) as a first concrete artifact in `notes/migration/`? Both are pure-documentation outputs and won't move any code.
