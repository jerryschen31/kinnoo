# Feature 115 — UAT Part 1: CLI Hardening

## Overview

Comprehensive CLI hardening based on User Acceptance Testing Part 1 findings.
34 tasks (task453–task486), 46 tests (test628–test673).
Source: `notes/phases/phase13-sat-uat-updates.md`

## SWE Handoff

### Implementation Priority / Recommended Order

The tasks are grouped by CLI command. Within each group, some tasks have
dependencies. The recommended implementation order below accounts for
dependencies and groups logically related work for efficient SWE sessions.

---

#### Batch 1 — Quick wins & CLI scaffolding (can be done in a single SWE session)

| Task   | Title                                                    | Tests              | Deps       |
|--------|----------------------------------------------------------|---------------------|------------|
| task453 | CLI top-level help — version, commit hash, 🍊 icon      | test628             | none       |
| task476 | Comment out sync/stop/attach/logs + daemon help section  | test659             | none       |
| task472 | run — replace --sandbox with --enforce-policy            | test655             | none       |

**Notes:**
- task453: Add a git-hash resolution helper. Fallback to `"unknown"` when git is unavailable.
- task476: Comment out, do NOT delete. Add `[agent]` markers. Remove daemon section from main help. Update test that verifies subcommands set to expect these are no longer recognized.
- task472: Rename flag + all internal references. Straightforward find-and-replace.

---

#### Batch 2 — Init refactor (sequential, multiple related tasks)

| Task   | Title                                                   | Tests                          | Deps             |
|--------|---------------------------------------------------------|--------------------------------|------------------|
| task454 | init — framework as positional arg + no-framework      | test629, test630               | none             |
| task455 | init — interactive wizard                              | test631                        | task454          |
| task456 | init — change default entrypoint to main.py            | test632                        | none             |
| task457 | init — complete template + --minimal flag              | test633, test634, test635      | task454, task456  |
| task458 | init — README.md template improvements                 | test636                        | task456, task457  |
| task459 | init — language-specific .gitignore templates          | test637, test638, test639, test640 | task457      |

**Notes:**
- task454: Change `--framework` from option to positional arg with `nargs="?"`. Add `no-framework` choice. Update init_command.py dispatch.
- task455: Only starts after task454. Implement wizard with numbered menus. Use framework-language support matrix.
- task456: Change `run.py` → `main.py` everywhere in python templates. Update kinnoo.yaml entrypoint.
- task457: Default complete template creates `tools/`, `prompts/`, `evals/`, `tests/`, `data/` + `.gitignore`. `--minimal` creates only essentials. Openclaw complete adds `MEMORY.md`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `skills/`, `memory/`.
- task458: README must reference correct entrypoint, explain kinnoo.yaml, include folder guide table (complete only), include `🍊` footer.
- task459: Four .gitignore templates verbatim from UAT spec (python, javascript, typescript, openclaw). Content is specified exactly in `phase13-sat-uat-updates.md` items 8–11.

**Template matrix (reference):**

| Category          | Minimal files                                              | Complete adds                                               |
|-------------------|------------------------------------------------------------|-------------------------------------------------------------|
| Python            | kinnoo.yaml, README.md, requirements.txt, main.py         | tools/, prompts/, evals/, tests/, data/, .gitignore          |
| JavaScript        | kinnoo.yaml, README.md, package.json, index.js             | tools/, prompts/, evals/, tests/, data/, .gitignore          |
| TypeScript        | kinnoo.yaml, README.md, package.json, index.ts             | tools/, prompts/, evals/, tests/, data/, .gitignore          |
| OpenClaw minimal  | kinnoo.yaml, AGENTS.md, IDENTITY.md, SOUL.md, USER.md, README.md | —                                                 |
| OpenClaw complete | (above) + .gitignore, BOOTSTRAP.md, HEARTBEAT.md, MEMORY.md, skills/, memory/ | —                              |

---

#### Batch 3 — Pack enhancements

| Task   | Title                                                   | Tests                | Deps  |
|--------|---------------------------------------------------------|-----------------------|-------|
| task460 | pack — ignore data/ by default + --include/--exclude   | test641, test642      | none  |
| task461 | pack — --preflight dry-run                             | test643               | none  |
| task462 | pack — help text + default patch bump                  | test644, test645      | none  |
| task463 | pack — merge --signing-key into --sign                 | test646               | none  |
| task464 | pack — --json flag                                     | test647               | none  |

**Notes:**
- task460: Add `data/` to default exclusion set. Add `--include` and `--exclude` as `action="append"` args.
- task461: `--preflight` collects file list, sums sizes, resolves output path, prints report, exits before archive creation.
- task462: Update `--public` help to say "(without the --public flag, default is private)". Change `--bump` nargs to `"?"`, implement default patch increment logic.
- task463: Remove `--signing-key` arg. Change `--sign` to take a positional argument (metavar=`SIGNING_KEY`).
- task464: `--json` suppresses progress output and emits structured JSON with specified keys on completion.

---

#### Batch 4 — Publish, Install, Run command updates

| Task   | Title                                                   | Tests                | Deps    |
|--------|---------------------------------------------------------|-----------------------|---------|
| task465 | publish — --local\|--remote mutual exclusion           | test648               | none    |
| task466 | publish — version history + Agent Versions tab         | test649               | none    |
| task467 | publish — --json flag                                  | test650               | none    |
| task468 | install — remove deprecated openclaw options           | test651               | none    |
| task469 | install — default openclaw path                        | test652               | task468 |
| task470 | install — --json flag                                  | test653               | none    |
| task471 | run — --json structured output                         | test654               | none    |

**Notes:**
- task465: Use `add_mutually_exclusive_group()` for --local/--remote.
- task466: Server-side: ensure all versions stored, API returns latest. Registry UI: add "Agent Versions" tab.
- task468: Remove 5 deprecated options: `--state-overwrite`, `--allow-vulnerable`, `--ignore-scripts`, `--openclaw-min-version`, `--openclaw-skill`. Remove handling code.
- task469: Detect openclaw type → default install to `~/.openclaw/workspace-<name>`.
- task470: `--json` requires `-y`. Error if interactive.
- task471: For non-openclaw: wrap execution in timing, emit JSON envelope. For openclaw: pass `--json` through. See UAT for full JSON schema spec.

---

#### Batch 5 — Inspect improvements

| Task   | Title                                                   | Tests     | Deps    |
|--------|---------------------------------------------------------|-----------|---------|
| task473 | inspect — --json flag                                  | test656   | none    |
| task474 | inspect — --update 2 args + positional flexibility     | test657   | none    |
| task475 | inspect — --update confirmation prompt                 | test658   | task474 |

**Notes:**
- task474: Change `--update` nargs from 3 to 2. Handle `KEY NEW_VALUE` without `OLD_KEY`. Ensure target arg works before or after `--update`.
- task475: Read current value, show `Changing <key> from <old> to <new>. Proceed? (y/N):`, abort on N (default). `--skip-warnings` skips prompt.

---

#### Batch 6 — Search/List JSON + new commands

| Task   | Title                                                   | Tests              | Deps  |
|--------|---------------------------------------------------------|--------------------|-------|
| task477 | search — remove --openclaw-skills + refactor --json    | test660, test661   | none  |
| task478 | list — add --json option                               | test662            | none  |
| task484 | new kinnoo fetch command                               | test668, test669   | none  |
| task485 | new kinnoo uninstall command                           | test670, test671   | none  |
| task486 | hotfix — hide traceback for remote registry failures   | test672, test673   | task484, task485 |

**Notes:**
- task477: Remove `--openclaw-skills` from parser and search_command.py. Refactor `--json` for general structured output.
- task484: New `fetch_command.py`. Download archive via remote_client. Integrity check. `--strict` for signature. Do NOT unpack.
- task485: New `uninstall_command.py`. Parse target format (dir, dir==version, archive.kno==version). Confirmation prompt unless `-y`. `latest` as valid version alias.
- task486: Catch `RemoteRegistryClientError` in list/search/fetch/publish dispatch and print concise `[kinnoo]` lines instead of uncaught traceback output.

---

#### Batch 7 — Registry UI & server-side security (larger scope)

| Task   | Title                                                   | Tests     | Deps         |
|--------|---------------------------------------------------------|-----------|--------------|
| task479 | Registry UI — inline security icons in Name column     | test663   | none         |
| task480 | Registry — server-side security check script           | test664   | none         |
| task481 | Registry — security column update + report             | test665   | task480      |
| task482 | Registry — containerized Lambda                        | test666   | task481      |
| task483 | Registry UI — Security tab in modal                    | test667   | task481      |

**Notes:**
- task479: Render icons inline in Name cells for both My Agents and Search tables (two spaces before icons, for example: "s3-seed-agent  ✅📦"). Do not add a separate Security column. Icons: ✅ 📦 ❌ where 📦 represents integrity verification (archive and/or per-file).
- task480: Create `server/services/security_check.py` with signature, archive integrity, and per-file integrity checks.
- task481: Wire checks into publish route. Persist report. API endpoint for retrieving report.
- task482: Lambda/container infra should be implemented via Terraform in `iac/` (function, IAM, wiring/config) when possible. Async invocation from publish. Write-back to metadata store.
- task483: New tab in agent modal. Fetch and render per-check [PASS]/[FAIL] lines.

---

### Design Constraints

1. **No Vitest needed** — all tests are Python integration tests invoking the CLI via `python src/kinnoo/cli.py`. JS/TS template file tests only check file existence and content via Python.
2. **Do not delete commented-out code** (task476) — use Python `#` comments with `[agent]` markers.
3. **Entrypoint rename** (task456) — must update templates.py constants, init_command.py, and kinnoo.yaml template. Existing agents are not migrated.
4. **--json flags** — all `--json` implementations should suppress progress/interactive output and emit a single JSON blob to stdout on completion.
5. **Manifest validator** — run `python3 src/validate_project_manifests.py` after all manifest file changes.
6. **Template content** — .gitignore content for each language is specified verbatim in `notes/phases/phase13-sat-uat-updates.md` items 8–11. Use exact content.
7. **Terraform-first infra workflow** — for any task in task453–task485 that changes infrastructure, update Terraform under `iac/` (root/module/env files) and validate with `terraform plan` (and apply in target env when authorized) instead of relying on manual console-only edits.

### Files Likely Modified

- `src/kinnoo/cli.py` — nearly every task touches this
- `src/kinnoo/init_command.py` — task454–459
- `src/kinnoo/templates.py` — task456–459
- `src/kinnoo/pack_command.py` — task460–464
- `src/kinnoo/publish_command.py` — task465–467
- `src/kinnoo/install_command.py` — task468–470
- `src/kinnoo/run_command.py` — task471–472
- `src/kinnoo/sandbox.py` — task472
- `src/kinnoo/inspect_command.py` — task473–475
- `src/kinnoo/search_command.py` — task477
- `src/kinnoo/list_command.py` — task478
- `src/kinnoo/fetch_command.py` — task484 (new file)
- `src/kinnoo/uninstall_command.py` — task485 (may already exist)
- `server/templates/registry.html` — task479, task483
- `server/services/security_check.py` — task480–482 (new file)
- `server/routes/publish.py` — task481–482
- `server/metadata/manager.py` — task479, task481
- `tests/test_init.py` — task454–459
- `tests/test_pack.py` — task460–464
- `tests/test_publish_refactor.py` — task465, task467
- `tests/test_cli_registry.py` — task466, task477, task478
- `tests/test_cli_install.py` — task468–470
- `tests/test_cli_inspect.py` — task473–475
- `tests/test_cli.py` — task453, task471–472, task476, task484–485
- `server/tests/test_security_check.py` — task480–482 (new file)
- `iac/main.tf` — task482 infra wiring (when implemented)
- `iac/variables.tf` — task482 infra inputs (when implemented)
- `iac/modules/*` — task482 infra modules/resources (when implemented)
- `iac/environments/dev/terraform.tfvars` — env overrides for task482 infra (when implemented)
