# Public/Private split cutover runbook (Stage 5 dry run)

This runbook defines the exact dry-run and real-cutover sequence for splitting current repo contents into:
- public repo: `kinnoo-project/kinnoo`
- private repo: retained `jerryschen31/kinnoo`

## Preconditions

1. Stage 0/1/2 completed and committed (visibility tags + `mock-public/` scaffold + public manifest slice).
2. Stage 3 private-only validation completed via git worktree:
   - Worktree path used: `/tmp/kinnoo-private-only`
   - Command result summary:
     - `pytest server/tests tests/iac -q` -> pass (`54 passed, 2 skipped`)
     - private cross tests excluding `test_registry.py` -> pass (`8 passed`)
     - `tests/client_cli_registry/test_registry.py` fails in private-only view because it imports public `kinnoo` package; tracked for refactor.
3. Backup map current at `code-backup/MAP.md`.
4. Secrets scan completed on candidate public tree prior to publication.

## Dry-run sequence (no irreversible changes)

### A. Create isolated dry-run branch

```bash
git checkout -b dryrun/public-private-cutover
```

### B. Build export candidate from `mock-public/`

```bash
rm -rf /tmp/kinnoo-public-export
mkdir -p /tmp/kinnoo-public-export
cp -R mock-public/. /tmp/kinnoo-public-export/
```

### C. Validate exported public candidate

```bash
cd /tmp/kinnoo-public-export
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python3 -m pytest tests -q
cd web
npm ci
npm test
npm run build
```

### D. Validate private-only view with git worktree

```bash
cd /home/runner/work/kinnoo/kinnoo
git worktree add /tmp/kinnoo-private-dryrun -b dryrun/private-only
cd /tmp/kinnoo-private-dryrun
rm -rf src web docs mock-public
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r server/requirements.txt
pytest server/tests tests/iac -q
pytest tests/registry_integration/test_web_auth_oidc_logout.py tests/registry_integration/test_oidc_error_handling.py tests/registry_integration/test_lambda_handler.py -q
```

### E. Remove dry-run worktrees/branch artifacts

```bash
cd /home/runner/work/kinnoo/kinnoo
git worktree remove --force /tmp/kinnoo-private-dryrun
git branch -D dryrun/private-only
```

## Real cutover sequence (single coordinated change window)

1. Freeze merges on both repos for cutover window.
2. Create **new public repo** with clean initial squashed commit from `mock-public/` contents.
3. In private repo branch:
   - Remove `mock-public/` once public repo is initialized.
   - Keep private scopes (`server/`, `iac/`, private tests/scripts/workflows, internal notes).
   - Keep migration docs under `notes/migration/`.
4. Reconfigure CI:
   - Public repo: only public CI workflows.
   - Private repo: private CI/deploy workflows remain.
5. Open coordinated PRs (public init + private cleanup), merge with same cutover timestamp.

## Proposed `git mv` / `git rm` command list (private repo cleanup after public init)

```bash
# executed on private-repo cutover branch after public repo bootstrap is complete
git rm -r mock-public
# (optional) if duplicate public-only docs are moved out later, remove them with targeted git rm paths
```

## Rollback procedure

If any cutover gate fails before merge:

```bash
git reset --hard HEAD
git clean -fd
```

If post-cutover regression appears in private repo:

1. Revert cutover PR commit in private repo.
2. Restore any in-place files from `code-backup/MAP.md` restore commands.
3. Re-run private validation suite.

If post-cutover regression appears in public repo:

1. Revert public initial migration commit.
2. Rebuild public tree from latest known-good `mock-public/` snapshot.
3. Re-run public validation suite before re-cutting.

## Open blocker tracked from Stage 3

- `tests/client_cli_registry/test_registry.py` is tagged private but currently imports the public `kinnoo` package; this is an intentional tracked blocker for refactor into:
  - private integration tests (server-coupled), and
  - public contract tests (CLI behavior against fake server).
