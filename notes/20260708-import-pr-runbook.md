# Import PR Runbook — Merge Private Backend into Public Monorepo

**Date:** 2026-07-08
**Context:** Reverse-merge (Option 3 from `notes/20260706-revert-back-to-monorepo-best-path.md`): import the private-only code (`server/`, `iac/`, deploy files, server/iac tests) into the existing public repo `kinnoo-project/kinnoo` (`~/gh/public/kinnoo`) as one reviewed PR. History is **not** published — only a reviewed diff.
**This file stays private** (lives under `notes/`, which is excluded from the import).

---

## Key findings that shaped this plan

- **No real secrets in tracked files.** Terraform references secret *values* by name/ARN (injected from Secrets Manager); `AKIA`/`PRIVATE KEY` hits are scanner-pattern docs; `realpass@db.prod` is a dummy test fixture.
- **`notes/` is the hazard.** 745 tracked files; the `blocked-notes.md` denylist (45 files) was scoped to the first split's subset and misses 19+ other notes still leaking account IDs/ARNs/DB creds. → **Exclude `notes/` wholesale.**
- **Account-ID / zone-ID leakage in the *code* set is tiny** — 4 files (2 tfvars, 1 module variables default, 1 test) + zone in 2 tfvars.
- **Public repo already has** `.github/`, `tests/`, and `EPICS/FEATURES/TASKS/TESTS.txt` → reconcile, do NOT overwrite.
- **Public repo `server/` and `iac/` = 0 files** → clean wholesale add.
- **Publishing now is the safest moment** — AWS infra is already torn down, so leaked identifiers point at nothing.
- **Sequencing:** do this import **before** generating Cloudflare R2 keys / tunnel credentials, so secret hygiene is proven before any live secret exists. Keep all Cloudflare secrets out of the repo tree.

---

## 1. Exclusion set

**Recommendation: exclude `notes/` entirely** (internal dev journal; product docs already live in `docs/`).

Save as `~/kinnoo-import.excludes`:

```
notes/
code-backup/
mock-public/
commit_message.txt
*.pem
*env/
.env
*scratch*
*.bak
outputs/
dist/
build/
**/__pycache__/
*.tfstate
*.tfstate.*
*tfplan*
**/.terraform/
.registry-storage/
kinnoo-config.txt
.DS_Store
```

### Fallback only — augmented notes denylist (if you insist on bringing some notes)
Union of `blocked-notes.md` (45) + 19 additional leaking files. Still just pattern-matched — prefer excluding `notes/` wholesale and cherry-picking an explicit allowlist by hand instead.

Additional 19 not in `blocked-notes.md`:
```
notes/dev-complete-teardown-and-redeploy-instructions-2.md
notes/dev-to-prod-steps.md
notes/features/feature103-swe-handoff.md
notes/features/feature104-swe-handoff.md
notes/features/postgres-registry-db-planning.md
notes/phases/phase14-auth-and-db-fixes.md
notes/phases/phase3-registry-planning.notes
notes/phases/phase8-planning-1-2-my-responses.md
notes/phases/phase8-planning-3.md
notes/postgres-admin-password-rotation-database-url-sync-issues.md
notes/postgres-operations.md
notes/pre-production-check-addressing-blockers.md
notes/prod-deployment-instructions.md
notes/tasks/task448-human-handoff.md
notes/tasks/task451-notes.md
notes/tasks/task452-notes.md
notes/tasks/task487-notes.md
notes/tasks/task506-swe-handoff.md
notes/tasks/task525-notes.md
```
(The 45 blocked paths are enumerated in `notes/blocked-notes.md`.)

---

## 2. .gitignore additions for the public repo

Public `.gitignore` already has `.env`, `*env/`, `*.pem`, `*scratch*`, `outputs/`, but is **missing Terraform ignores** — critical once `iac/` lands.

```bash
PUB=~/gh/public/kinnoo
cat >> "$PUB/.gitignore" <<'EOF'

# Terraform (added with iac/ import)
*.tfstate
*.tfstate.*
*tfplan*
**/.terraform/
iac/tfplan*
kinnoo-config.txt
.registry-storage/
code-backup/
EOF
```

---

## 3. Account-ID + zone-ID scrub (precise — 4 files)

Run **after** copying into the public branch, **before** `git add`. `000000000000` keeps HCL/tests valid. `sed -i ''` is the macOS/BSD form.

```bash
PUB=~/gh/public/kinnoo
ACCT=<AWS_ACCOUNT_ID>
ZONE=<CLOUDFLARE_ZONE_ID>

# AWS account ID -> 000000000000 (only migrating files)
for f in \
  iac/environments/dev/terraform.tfvars \
  iac/environments/prod/terraform.tfvars \
  iac/modules/lambda-security-check/variables.tf \
  tests/registry_integration/test_lambda_handler.py ; do
  sed -i '' "s/$ACCT/000000000000/g" "$PUB/$f"
done

# Cloudflare zone ID -> placeholder (dev + prod tfvars)
for f in iac/environments/dev/terraform.tfvars iac/environments/prod/terraform.tfvars ; do
  sed -i '' "s/$ZONE/REPLACE_WITH_CLOUDFLARE_ZONE_ID/g" "$PUB/$f"
done

# Rename scary-but-fake test fixture so scanners don't flag it
sed -i '' 's#realuser:realpass@db\.prod#dummy:dummy@db.example#g' \
  "$PUB/tests/iac/test_feature121_db_url_stub_secret.py"

# Verify nothing survived
grep -rn "$ACCT\|$ZONE\|realpass@db.prod" "$PUB" && echo "!!! STILL PRESENT" || echo "clean"
```

---

## 4. Import PR — step by step

```bash
PRIV=~/gh/kinnoo
PUB=~/gh/public/kinnoo

# --- 0. Start clean in the public repo ---
cd "$PUB"
git checkout main && git pull
git checkout -b import-private-backend

# --- 1. Export ONLY tracked, curated paths from private ---
# Private-only trees + deployment files (none exist in public yet).
git -C "$PRIV" archive HEAD \
  server iac scripts Dockerfile Dockerfile.lambda docker-compose.yml \
  .dockerignore lambda_handler.py \
  | tar -x -C "$PUB"

# tests/: only private-only subdirs (avoid clobbering public tests/)
git -C "$PRIV" archive HEAD tests/iac tests/registry_integration \
  | tar -x -C "$PUB"

# --- 2. Apply .gitignore additions (section 2) and scrub (section 3) NOW ---

# --- 3. Drop cruft that slipped in ---
rm -rf "$PUB/scripts/archive" "$PUB/code-backup"

# --- 4. Secret-scan staged result BEFORE committing ---
cd "$PUB"
git add -A
gitleaks protect --staged --verbose   # or: trufflehog filesystem --results=verified .
```

### Reconcile these by hand (do NOT bulk copy — public already has them)
- **`.github/` workflows** — copy in only server/iac CI + deploy workflows missing publicly; repoint triggers/branches.
  `diff <(git -C "$PRIV" ls-files .github) <(git -C "$PUB" ls-files .github)`
- **`FEATURES/TASKS/TESTS/EPICS.txt`** — diverged + remapped IDs; simplest is to **leave the public versions as-is** and not import the private ones (they carry account IDs / stale infra refs).
- **`requirements.txt`** — keep public root (CLI) separate; server deps live in `server/requirements.txt` (already exported). Don't overwrite the public root file.
- **`docs/`** — if publishing a self-hosting/Cloudflare runbook, write a fresh `docs/self-hosting.md` with placeholders; do NOT copy `notes/phases/phase5-cloudflare-tunnel-runbook.md` raw.

### Commit and open PR
```bash
cd "$PUB"
git status                          # eyeball every added path
git add -A
git commit -m "Import private backend (server, iac, deploy) into monorepo

Scrubbed AWS account ID and Cloudflare zone ID; excludes internal notes/
and backup artifacts. Terraform history starts at import by design."
git push -u origin import-private-backend
gh pr create --repo kinnoo-project/kinnoo --base main \
  --title "Import private backend into monorepo" \
  --body "Brings server/, iac/, deploy files, and server/iac tests into the public monorepo. Sensitive identifiers scrubbed; internal notes/ and code-backup/ excluded. See PR diff — reviewed as a single import per the monorepo consolidation plan."
```

---

## 5. Final gate before merge (one-way door)

Read the PR's **Files changed** in full on GitHub. Confirm:
- [ ] No `iac/environments/**/*.tfvars` with a real account ID or zone ID
- [ ] No `.tfstate`, `*tfplan*`, or `.terraform/`
- [ ] No `.pem` / `.env` / `*env/`
- [ ] `notes/` absent
- [ ] `code-backup/` absent
- [ ] `gitleaks`/`trufflehog` clean
- [ ] `.github/` and the four `*.txt` reconciled, not clobbered

---

## 6. After the import (post-merge)
- Archive the private repo on GitHub (keep private, permanently); add a README line pointing at the public monorepo. Local checkout remains home for `.pem` keys, tfstate scratch, and `notes/`.
- Only then generate Cloudflare R2 keys + tunnel credentials for the demo (see `notes/20260708-cloudflare-demo-migration-plan.md`). Keep every credential in an untracked `.env` / host env / Cloudflare dashboard — never in the now-public tree.
</content>
