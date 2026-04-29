# Secret Scan Sign-Off — 2026-04-29

Tracking issue: [#382 — scan of repo before push to master](https://github.com/jerryschen31/kinnoo/issues/382)
Pre-release item: PRE-RELEASE FEATURE 8 (`notes/PRE-RELEASE-CHECKLIST.md`)

## 1. Scope

Automated secret scan run against:

- Full working tree (current `HEAD`).
- **Full git history**: all branches and all commits reachable from `--all` (899 commits on this clone after `git fetch --unshallow`).
- All required top-level paths: `src/`, `server/`, `tests/`, `scripts/`, `docs/`, `web/`, `iac/`, plus the rest of the repo (`notes/`, `lambda_handler.py`, `Dockerfile*`, etc. — gitleaks scans the whole tree by default).

Two complementary checks were also performed:

- Unsafe deserialization patterns in current code (`pickle.loads`, `yaml.load(...)` without a safe loader, `yaml.unsafe_load`, `marshal.loads`, `shelve.open`).
- Personal identifiers (real names, personal email, machine-specific paths, internal hostnames) in tracked code.

## 2. Scanner

| Tool | Version | Invocation |
| --- | --- | --- |
| gitleaks | `v8.21.2` (linux x64) | `gitleaks detect --source . --no-git` (current files) |
| gitleaks | `v8.21.2` (linux x64) | `gitleaks detect --source . --log-opts="--all"` (full history, 899 commits) |
| ripgrep / `grep` | n/a | manual sweeps for `pickle.loads`, `yaml.load(`, `yaml.unsafe_load`, `marshal.loads`, `shelve.open`, `jerryschen@gmail`, `/Users/jerry`, `/home/jerry`, `MacBook` across `src/`, `server/`, `scripts/`, `iac/`, `web/`, `docs/` |

Reports archived at scan time:

- `/tmp/scan/gitleaks-current.json` — 14 findings, current tree
- `/tmp/scan/gitleaks-history.json` — 41 findings, full history

## 3. Findings summary

### 3.1 Current tree (14 findings — all dummy)

All 14 hits in the current working tree are obvious test fixtures / mock secrets in `tests/`. No production code paths (`src/`, `server/`, `scripts/`, `iac/`, `web/`) contain any matched secret.

| File | Rule | Secret value | Classification |
| --- | --- | --- | --- |
| `tests/client_cli_pack/test_pack_robustness.py:278` | generic-api-key | `ABCDEFGHIJKLMNOPQRSTUVWX1234567890` | Dummy (alphabet placeholder) |
| `tests/client_cli_registry/test_registry.py` (×8) | generic-api-key | `valid-passphrase-123`, `legacy-passphrase-123` | Dummy (test passphrases) |
| `tests/regression/sat/test_regression_v1.py:1021` | github-pat / generic-api-key | `ghp_abcdefghijklmnopqrstuvwxyz0123456789AB` | Dummy (alphabet placeholder) |
| `tests/regression/sat/test_regression_v1.py:1022` | generic-api-key | `sk-abcdefghijklmnopqrstuvwxyz123456` | Dummy (alphabet placeholder) |
| `tests/security_checks/test_trust_baseline.py:512,516` | generic-api-key | `p_abcdefghijklmnopqrstuvwxyz0123456789AB`, `-abcdefghijklmnopqrstuvwxyz123456` | Dummy (alphabet placeholder, partial) |

These exist on purpose: the trust-baseline / regression / pack tests assert that the secret-scan / value-redaction code paths fire on these patterns. They are intentional and per the issue ("Dummy credentials are fine.") are acceptable.

### 3.2 Git history (41 findings)

41 history-only hits across 899 commits. Triage:

- **39 of 41 are dummy fixtures** — earlier (pre-reorg) locations of the same test-fixture secrets listed in §3.1 (e.g. `tests/test_registry.py`, `tests/test_trust_baseline.py`, `tests/test_regression_v1.py`, `tests/test_pack_robustness.py`), plus a copy embedded in a captured agent-chat log at `.specstory/history/2026-02-27_17-28-54Z-implementing-task39-with-error-handling-and-reporting.md` that quotes the same dummy `ghp_…`, `sk-…`, `xoxb-…`, `AKIA…` placeholders.
- **2 of 41 are real-looking values**, both in a single captured agent-chat log that has since been removed from the working tree (commit `c7ed33b`, "modified gitignore", which removed `.specstory/` and added it to `.gitignore`). The captured log file is `.specstory/history/2026-03-16_07-57-48Z-tl-agent-phase-3-plan-and-review.md` (introduced in commit `0ed5ece0`):

  | # | Where in file | Value | Notes |
  | --- | --- | --- | --- |
  | H1 | URL query string from a dev login trace | password `30taIlwRagcCPaUbbQpjwN5HTmr-OcX_` for `jerryschen@gmail.com` against the local dev backend | A real dev-environment password leaked into a captured Next.js access log (`GET /login?email=…&password=…`). Owner-only dev account. |
  | H2 | JSON dump of a user record | `token_id`: `9e4a59ea227e42bcda0c42fcf0281f1d` | Server-side identifier for a one-time / session token issued in the dev environment. Token, not a long-lived API key. |

  Both values pre-date the current Kinde-based auth cutover and pertain to the local dev tenant only. They were never present under `src/`, `server/`, `scripts/`, `iac/`, `web/`, or `docs/` — only inside a captured chat-history transcript under `.specstory/history/`, which is no longer tracked (`.specstory/` is in `.gitignore` since `c7ed33b`) but still reachable via `git log --all`.

### 3.3 Unsafe deserialization patterns

`grep` for `pickle.loads`, `yaml.load(`, `yaml.unsafe_load`, `marshal.loads`, `shelve.open` across `src/`, `server/`, `scripts/`, `lambda_handler.py` returned **zero matches**. No unsafe deserialization is present in the current codebase.

### 3.4 Personal identifiers / machine-specific paths

- No occurrences of `jerryschen@gmail`, `/Users/jerry`, `/home/jerry`, or `MacBook` in `src/`, `server/`, `scripts/`, `iac/`, `web/`, or `docs/`.
- The string `jerryschen` does appear in `server/tests/test_agents_routes.py` (lines 338–366) but exclusively as a `tenant_slug` test fixture name (`tenant_slug="jerryschen"`, `name="jerryschen-public-agent"`). This is a deliberate, recognizable test slug, not a real identifier or credential. Acceptable for public release; can optionally be renamed to `acme` or similar in a follow-up cosmetic pass — out of scope for this audit.

## 4. Remediation actions taken / required

| Item | Status | Action |
| --- | --- | --- |
| Current-tree dummy fixtures (§3.1) | Accepted | Intentional test data; per issue DoD "Dummy credentials are fine." No change required. |
| History-only dummy fixtures (§3.2, 39/41) | Accepted | Same dummy values as §3.1, just at older paths. No change required. |
| H1 — real dev-account password leaked in `.specstory/…2026-03-16…md` (history only) | **Action required: rotate** | Rotate the password for `jerryschen@gmail.com` on the local/dev auth backend (and on any other site where the same password may have been reused). Tracked here as the rotation requirement; rotation itself is a human action. |
| H2 — dev `token_id` `9e4a59ea…` in same captured chat (history only) | **Action required: invalidate** | If the dev token store still holds this `token_id` (one-time / session token in the legacy local auth path), invalidate / delete it. If the underlying store has since been re-initialized as part of the Kinde / Postgres cutover, no further action is required — note the fact in the rotation log. |
| Unsafe deserialization (§3.3) | Pass | None. |
| Personal identifiers (§3.4) | Reviewed | Optional cosmetic rename of `tenant_slug="jerryschen"` test fixture; not required for sign-off. |

History rewrite is **not** required by the issue's definition of done (`#382` says "If any leak found: credential rotated" only). The stricter `notes/PRE-RELEASE-CHECKLIST.md` PRE-RELEASE FEATURE 8 entry additionally calls for "history rewritten or fresh-history approach chosen" — that decision is deferred to the separate `notes/src-history-public-release-checklist.md` decision gate and is out of scope for this sign-off.

## 5. Publish decision

**Conditional GO for public push of the `src/`, `server/`, `scripts/`, `iac/`, `web/`, `docs/` content as it stands today**, contingent on:

1. Owner confirms rotation of the dev password identified as H1 (and any reuse of that password elsewhere).
2. Owner confirms invalidation of the dev session/token `token_id` identified as H2 (or confirms the legacy token store has been replaced as part of the Kinde cutover).
3. Final keep-history-vs-fresh-history decision per `notes/src-history-public-release-checklist.md` is recorded before the actual public push, since H1 and H2 remain reachable in `git log --all` until then.

No production credentials, no production API keys, and no private keys were found anywhere in the scanned scope.

## 6. Sign-off

- Date (UTC): 2026-04-29
- Scanner: gitleaks v8.21.2
- Scope confirmed: §1
- Findings: §3 (14 current, 41 historical; 2 real-looking, both history-only and dev-environment only)
- Remediation owner: repository owner (rotation of H1 / invalidation of H2)
- Publish decision: Conditional GO (see §5)

Signed-off by: automated audit — pending human owner acknowledgement of items §4 H1 and §4 H2.
