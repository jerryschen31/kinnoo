# README

## Kinnoo is a developer platform for sharing agents.

## Packaging format

- `kinnoo pack` creates `.kno` artifacts as ZIP archives.
- `kinnoo install` expects `.kno` files in this ZIP-based format.

## OpenClaw Delegated Install (Feature65)

`kinnoo install` routes manifests declaring `type: openclaw-skill` through a delegated OpenClaw CLI install path.

Behavior:

- Kinnoo trust checks still run first (integrity/signature checks, manifest validation, install summary diagnostics).
- After validation, Kinnoo runs OpenClaw prechecks and delegates dependency install using:
	- `openclaw skills install .`
- Minimum CLI version gate is configurable:
	- `kinnoo install <archive.kno> --openclaw-min-version 0.2.0`

Deterministic delegated failure categories:

- `openclaw_cli_missing`: OpenClaw CLI executable is missing from `PATH`.
- `openclaw_cli_version_unsupported`: detected OpenClaw CLI version is below required minimum.
- `openclaw_cli_delegated_nonzero_exit`: delegated OpenClaw command exited non-zero.

Install trace behavior:

- Delegated outcomes are written to `.kinnoo/install-trace.json` under the installed target directory.
- Trace includes delegated backend metadata, minimum version, invoked command, category, and decision outcome.

## Manifest optional metadata (Feature9)

`kinnoo.yaml` supports these optional fields:

- `description` (string)
- `author` (string)
- `license` (string)
- `env_vars` (list of non-empty strings)

Notes:

- Existing V1 manifests remain valid when these fields are omitted.
- If `env_vars` is present, each entry must be a non-empty string.

## env_vars security contract (Feature10)

When an agent declares `env_vars`, `kinnoo run` resolves values in this order:

1. current process environment
2. agent-local `.env` file
3. masked interactive prompt for unresolved names

Security invariants:

- Secret values must never be printed, logged, or persisted by Kinnoo runtime flows.
- User-facing diagnostics reference variable names only.

Safe troubleshooting guidance:

- Verify required variable names are declared in `kinnoo.yaml` under `env_vars`.
- Check whether each required name exists in your shell environment or agent-local `.env`.
- If prompted, provide the value interactively; do not paste or print secret values into logs.

## kinnoo inspect (Feature11)

`kinnoo inspect` reads manifest metadata from either an agent directory or a `.kno` archive.

Usage:

- `kinnoo inspect <agent-dir>`
- `kinnoo inspect <archive.kno>`

Examples:

- `kinnoo inspect ./my-agent`
- `kinnoo inspect ./my-agent.kno`

Output semantics:

- Output is human-readable formatted text (not a raw YAML dump).
- Missing optional fields are omitted (not shown as `None` or empty placeholders).
- `env_vars` are displayed as variable names only; values are never shown.

Directory guidance behavior:

- Missing `kinnoo.yaml`: prints guidance plus a minimal manifest example and exits non-zero.
- Missing `requirements.txt`: prints guidance and robust generation commands:
	- `pip install uv`
	- `uv export --format requirements-txt > requirements.txt`

Common failure cases:

- Missing target argument: `Usage: kinnoo inspect <target>`
- Invalid archive: archive is not a valid zip-based `.kno` file
- Invalid manifest: prints `Error: Manifest validation failed.` with validator field-level errors

## kinnoo run --preflight (Feature14)

`kinnoo run --preflight` performs readiness validation only and does not execute agent logic.

Usage:

- `kinnoo run <agent-dir> --preflight`
- `kinnoo run ./my-agent --preflight`

Checklist behavior:

- Preflight always prints a deterministic checklist with pass/fail lines.
- Checklist sections include runtime version, env vars, entrypoint, and dependencies.
- If every check passes, output includes `Ready to run`.
- If any check fails, output includes `Not ready to run` and a remediation summary.
- Preflight confirms that entrypoint execution is skipped in preflight mode.

Security contract:

- Preflight output is names-only for environment variables.
- Preflight may list unresolved env var names, but it never prints env var values.

## Trust Baseline (Feature15)

Feature15 adds trust-focused behavior to install/run/inspect/pack workflows.

Install-time transparency and consent:

- `kinnoo install` shows a summary before installation, including:
	- agent name and version,
	- runtime type,
	- dependency names,
	- env var names (never values).
- Install prompt:
	- `Continue with install? [y/N]:`
	- default is No when user presses enter.
- `--yes` / `-y`:
	- keeps summary output,
	- skips confirmation prompt for CI and unattended workflows.

Feature39 install permission disclosure and consent:

- when manifest `permissions` is declared, install summary includes a deterministic permissions section:
	- network
	- filesystem scope
	- shell
	- browser
	- env access (names only)
- interactive installs require explicit permission consent:
	- `This agent declares explicit permissions. Allow requested permissions? [y/N]:`
	- default is deny
- non-interactive installs must use explicit override:
	- `kinnoo install ... --yes --accept-permissions`
	- using `--yes` without `--accept-permissions` aborts safely with guidance

Feature40 unsigned publisher warning and confirmation:

- when archive integrity is verified (checksum present) but no signature metadata is present, install emits:
	- `Warning: UNVERIFIED PUBLISHER - no signature metadata found for this archive.`
- interactive installs require explicit confirmation:
	- `UNVERIFIED PUBLISHER: no signature metadata found. Continue? [y/N]:`
	- default is deny
- non-interactive installs must use explicit override:
	- `kinnoo install ... --yes --allow-unverified-publisher`
	- using `--yes` without `--allow-unverified-publisher` aborts safely with guidance

Feature72 lockfile frozen mode:

- `kinnoo install --frozen` enforces lockfile-only reproducibility checks before extraction.
- Frozen mode validates lockfile entry presence, pinned version, and archive checksum.
- When lockfile drift is detected, install fails with deterministic remediation guidance:
	- `Re-run install without --frozen to regenerate lockfile, then retry --frozen.`
- Successful frozen installs leave lockfile content unchanged.

Unverified source warning:

- If `<archive>.sha256` is missing, install prints:
	- `This agent is from an unverified source.`
- Without `--yes`, install asks:
	- `This agent is from an unverified source. Continue? (y/n):`
- If checksum sidecar exists, unverified warning is skipped.

Run trace logging:

- After `kinnoo run` completes (success or failure), Kinnoo writes:
	- `~/.kinnoo/logs/run.<TIMESTAMP>.log`
- Timestamp in filename and JSON is UTC-only.
- Trace log JSON fields are safe-only:
	- `timestamp`, `agent_name`, `agent-version`, `runtime_type`, `exit_code`
- Trace logs never include:
	- user input content,
	- env var values,
	- secret values,
	- stdout/stderr payloads.

Heuristic security sweep (`inspect` and `pack`):

- `kinnoo inspect <agent-dir>` includes a `Security sweep:` section.
- Clean scan output:
	- `Security sweep: no env var exposure patterns detected (heuristic)`
- Dirty scan output includes warning lines with file and line details.
- `kinnoo pack <agent-dir>` runs the same sweep and prints warnings as non-blocking output.
- Disclaimer always applies:
	- `(heuristic scan — may produce false positives; not a substitute for code review)`

Project-wide security invariant:

- No env var or secret values are ever printed, logged, or persisted by Kinnoo trust paths.
- Diagnostics and trust output are names-only for env vars.

## Publisher key generation (Feature40)

Use `kinnoo keygen` to generate an Ed25519 keypair for archive signing and publisher verification.

Usage:

- `kinnoo keygen`
- `kinnoo keygen --private-key ./keys/publisher-private.pem --public-key ./keys/publisher-public.pem`

Behavior:

- Writes deterministic default filenames in the current working directory when paths are not provided:
	- `kinnoo-ed25519-private.pem`
	- `kinnoo-ed25519-public.pem`
- Enforces secure permissions for generated keys:
	- private key: `0600`
	- public key: `0644`
- Prints a public-key SHA256 fingerprint summary for operator verification.

Security notes:

- Kinnoo never prints private key material in command output.
- Keep private keys out of source control and store them in a secure operator-controlled location.
- Public keys may be distributed for verification workflows.

## Archive Integrity (Feature16)

Feature16 adds checksum lifecycle behavior across pack/install/inspect/publish using sidecar files.

Checksum sidecar contract:

- Sidecar naming: `<archive>.kno.sha256` (sibling to archive).
- Sidecar content format: `<sha256>  <archive-filename>`.
- SHA256 digest is lowercase hex and computed from archive bytes.

Pack behavior:

- `kinnoo pack` writes checksum sidecar after archive creation.
- Pack output includes:
	- `[kinnoo pack] Checksum sidecar written: <path>`

Install behavior (`kinnoo install <file.kno>`):

- Sidecar present + checksum match:
	- install proceeds,
	- output includes `[kinnoo install] Archive checksum verified.`
- Sidecar present + mismatch:
	- install aborts with exact error:
	- `Archive integrity check failed — the file may be corrupted or tampered with`
- Sidecar missing:
	- warning-only path continues install,
	- output includes: `No checksum file found — archive integrity not verified`

Inspect behavior:

- `kinnoo inspect <archive.kno>` reads sidecar when valid and displays:
	- `- Checksum (SHA256): <digest>`

Publish behavior:

- `kinnoo publish <agent-name>` copies sidecar to registry when source sidecar exists.
- Publish output includes one of:
	- `Published checksum sidecar: <path>`
	- `Published checksum sidecar: (none found at source)`

## Project Publish Target Toggle

`kinnoo publish` supports a project-level toggle in `kinnoo-config.txt` at your project root.

Example:

```txt
publish_to_authenticated_registry=true
```

Behavior:

- `true`: publish attempts authenticated remote registry publish by requesting a token from
	`KINNOO_REGISTRY_URL/api/auth/token` using:
	- `REGISTRY_ADMIN_EMAIL` (as username)
	- `REGISTRY_ADMIN_PASSWORD`
	- `KINNOO_TENANT_SLUG` (or `global` if unset)
- `false`: publish keeps current behavior (local/scratch default unless `--remote` or registry URL config is already forcing remote).

## Feature68 CI Publish Reference Workflow

Kinnoo includes a reference workflow at `.github/workflows/kinnoo-publish.yml` for automation pipelines.

Pipeline stages:

- install dependencies
- preflight compatibility check (`kinnoo check`)
- pack archive (`kinnoo pack`)
- publish to remote registry (`kinnoo publish --remote`)

Required secrets/environment contract:

- `KINNOO_REGISTRY_URL`
- `KINNOO_REGISTRY_TOKEN`
- `KINNOO_TENANT_SLUG`

Strict-mode compatibility control:

- `KINNOO_CI_STRICT_MODE=1` enables strict publish flags in the reference workflow when strict mode is available.

Security notes:

- Never commit credentials into repository files or workflow YAML.
- Keep registry auth values in GitHub Actions Secrets only.
- The workflow uses fail-fast shell settings (`set -euo pipefail`) so errors terminate with deterministic non-zero exits.

Troubleshooting common CI failures:

- Missing secrets: ensure `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, and `KINNOO_TENANT_SLUG` are configured in repo Actions Secrets.
- Preflight failures: run `python3 src/kinnoo/cli.py check <agent-dir>` locally to reproduce manifest/runtime contract issues.
- Signing failures (if your pipeline enables signing): verify the private signing key path is available to the runner and referenced by your signing step.
- Publish failures: verify token scope and tenant mapping, then retry with explicit remote mode (`kinnoo publish --remote`) for deterministic behavior.

Strict rollout guidance:

- Start with `KINNOO_CI_STRICT_MODE=0` while validating signature coverage for all publish paths.
- Move to required gate mode by setting `KINNOO_CI_STRICT_MODE=1` and enforcing `publish --strict` in protected-branch workflows.
- In strict mode, unsigned artifacts fail closed and must be re-packed with `kinnoo pack --sign`.

## Feature69 kinnoo test command

Kinnoo includes a standardized declarative test runner for agent projects.

Canonical test file:

- `kinnoo.tests.yaml`

CLI usage:

- `kinnoo test ./my-agent`
- `kinnoo test ./my-agent --json`
- `kinnoo test ./my-agent --validate-only`

Minimal Python one-shot example:

```yaml
version: 1
tests:
	- id: smoke-oneshot
		name: one-shot response smoke test
		input: hello
		assertions:
			- contains: hello
		timeout_seconds: 5
		expected_exit_code: 0
```

JS/TS daemon-compatible example:

```yaml
version: 1
tests:
	- id: smoke-daemon
		name: daemon-compatible response smoke test
		input: ping
		assertions:
			- contains: pong
		timeout_seconds: 10
		expected_exit_code: 0
```

Notes:

- one-shot and daemon-compatible runtimes use the same assertion contract, so CI summaries stay consistent.
- prefer deterministic output assertions (`contains`, `equals`, `regex`) over broad semantic checks.

## Feature70 phase6 command matrix and provenance messaging

Phase 6 command matrix (high-signal operational commands):

- `kinnoo login --registry <url> --tenant <slug>`
- `kinnoo logout`
- `kinnoo list --remote`
- `kinnoo search <query> --remote`
- `kinnoo import --source clawhub <owner>/<slug>`
- `kinnoo sync clawhub`
- `kinnoo check <agent-dir>`
- `kinnoo test <agent-dir>`
- `kinnoo pack <agent-dir>`
- `kinnoo publish <agent-name> --remote`

ClawHub mirror attribution model:

- mirrored records are written under tenant slug `clawhub`
- source provenance stays explicit via source registry metadata and mirror attribution fields
- operators can verify that mirrored entries and local sync behavior reference the same `clawhub` tenant model

Phase 6 forward command references (consistency contract):

- strict trust mode: `kinnoo install --strict` and `kinnoo publish --strict`
- lockfile reproducibility: `kinnoo install --frozen`
- archive compare: `kinnoo diff <a.kno> <b.kno>`
- uninstall flow: `kinnoo uninstall <agent-name>`
- framework adapters: `kinnoo import --from langchain|langgraph|openai`

## Registry Login and Logout

`kinnoo login` and `kinnoo logout` manage local registry auth state for CLI registry workflows.

Usage:

- Interactive login:
	- `kinnoo login --registry https://registry.example.com --tenant acme`
- Non-interactive login:
	- `kinnoo login --registry https://registry.example.com --tenant acme --email user@example.com --password '<password>'`
- Logout:
	- `kinnoo logout`

Persistence and precedence:

- Successful login persists `registry_url`, `registry_token`, and `tenant_slug` in `~/.kinnoo/config.yaml`.
- `kinnoo logout` clears persisted auth keys from `~/.kinnoo/config.yaml`.
- Environment variables remain highest precedence over file config:
	- `KINNOO_REGISTRY_URL`
	- `KINNOO_REGISTRY_TOKEN`
	- `KINNOO_TENANT_SLUG`
- After logout, registry operations requiring auth fail unless explicit env-var overrides are provided.

Security notes:

- Kinnoo never prints tokens or passwords in CLI output.
- Prefer environment variables for CI/non-interactive auth flows.

Notes:

- `kinnoo publish --local` and `kinnoo publish --remote` still take precedence when explicitly provided.
- If the toggle is `true`, ensure `KINNOO_REGISTRY_URL`, `REGISTRY_ADMIN_EMAIL`, and `REGISTRY_ADMIN_PASSWORD` are set.

## Pack Size Reporting & Warnings (Feature17)

Feature17 adds package-footprint visibility across pack/inspect/list workflows.

Pack behavior:

- `kinnoo pack` prints final archive size after artifact creation:
	- `[kinnoo pack] Archive size: <human-readable>`
- If archive size is strictly greater than 100 MB, pack prints:
	- `Warning: archive is large (X MB). Consider whether all dependencies are necessary.`

Inspect behavior:

- `kinnoo inspect <archive.kno>` includes archive size metadata:
	- `- Archive Size: <human-readable>`

List behavior:

- `kinnoo list`, `kinnoo list --local`, and `kinnoo list --remote` include additive size visibility per row:
	- `| size: <human-readable>`
- Size formatting is shared across commands and uses stable units (`B`, `KB`, `MB`, `GB`).

## Asset Bundling Compatibility (Feature22)

Feature22 adds optional manifest-driven asset bundling via `assets`.

Compatibility guarantees:

- Agents that do not declare `assets` continue to use the same pack/install behavior as pre-Feature22 flows.
- `assets.paths` accepts file paths and directory paths relative to the agent root.
- Directory paths are bundled recursively; declaring a base folder includes nested files/subfolders.
- `assets.bundle: false` keeps asset metadata but skips asset payload inclusion in the archive.
- `assets.max_bundle_size_mb` overrides the default 100 MB warning threshold when provided.

## Mutable State Snapshots (Feature35)

Feature35 introduces `state_dirs` for mutable runtime state such as memory folders. This is intentionally separate from immutable `assets`.

Behavior summary:

- `assets` remain immutable packaged resources with existing bundle behavior.
- `state_dirs` are packed as mutable snapshots under `state_snapshots/<declared-state-dir>/...`.
- install restores snapshots back into each declared state root.

Structured `state_dirs` entries support exclude patterns:

```yaml
state_dirs:
	- path: memory
		exclude:
			- daily/*.md
			- secrets/*
```

Exclude and restore semantics:

- Excluded files are omitted during pack and therefore never restored.
- Non-excluded files remain part of the snapshot/restore flow.
- Install is warning-first and non-destructive when existing state is present.
- Use `kinnoo install ... --state-overwrite` for explicit deterministic replacement of existing state.

Compatibility guarantee:

- Agents without `state_dirs` keep legacy asset-only pack/install behavior unchanged.

## Input Safety Guard (Feature18)

Feature18 adds an input safety guard to `kinnoo run` before agent execution.

Guard behavior:

- The guard runs automatically for `kinnoo run <agent-dir> "<input>"` before entrypoint execution.
- It evaluates user input for common injection patterns and emits warnings to stderr.
- The guard is non-blocking by design:
	- in interactive terminals, users can acknowledge risk and proceed,
	- in non-interactive mode, execution aborts by default for safety.

Threat categories currently covered:

- SQL injection
- shell command injection
- path traversal
- SSRF
- XSS
- template injection

CLI override for automation:

- `--no-guard` disables the input safety check for trusted CI/automation pipelines.

Type-aware checking model:

- The guard supports typed checks (`text`, `string`, `file_path`, `url`, `id`) so threat-category evaluation can be narrowed by input semantics.
- This supports future parameterized input flags without changing the guard contract.

Architecture note:

- The guard is implemented behind an `InputGuard` Protocol and factory (`get_default_guard()`), enabling future replacement with a model-based or hybrid classifier while preserving runtime integration.

## JSON I/O Contract (Feature42)

Feature42 adds manifest-driven structured I/O support while keeping legacy text workflows unchanged.

Manifest contract:

- `inputs.type` can include `json` for structured request payloads.
- `outputs.type` can include `json` for structured response payloads.
- Text workflows remain additive-compatible: existing `text` agents and commands keep the same behavior.

Run command usage:

- Inline JSON: `kinnoo run <agent-dir> --json-input '{"task":"ping"}'`
- File JSON: `kinnoo run <agent-dir> --json-file ./payload.json`

Output contract enforcement:

- When `outputs.type` includes `json` for one-shot runtimes, stdout must be valid JSON.
- Invalid JSON output fails with parse-context diagnostics (line/column) without echoing secret values.

Inspect and preflight visibility:

- `kinnoo inspect` shows declared input/output types and JSON contract hints.
- Inspect metadata includes `Input Types`, `Output Types`, and `JSON Contract` lines when applicable.
- `kinnoo run <agent-dir> --preflight` prints an explicit manifest I/O contract line, including JSON-mode guidance.

## Feature33 manifest extensions for Node/OpenClaw

Feature33 adds optional manifest fields for Node.js-oriented agent metadata:

- `runtime.package_manager`: allowed values are `npm` or `pnpm`
- `channels`: list of non-empty strings
- `skills`: list of non-empty relative paths (no absolute paths or `..` traversal)
- `state_dirs`: list of non-empty relative paths (no absolute paths or `..` traversal)

OpenClaw-targeted behavior (`framework: openclaw`):

- `runtime.language` must be `nodejs`
- `runtime.type` must be `daemon`
- `runtime.package_manager` is required with value `npm` or `pnpm`
- `channels` must include `stdio`

Non-openclaw compatibility:

- Existing manifests that omit Feature33 fields remain valid.
- Non-openclaw manifests may include Feature33 fields in valid shape without OpenClaw-only validation failures.

## Mutable state snapshots (Feature35)

Feature35 defines `state_dirs` as mutable runtime state snapshots, which are distinct from immutable `assets`.

Semantics:

- `assets` are immutable packaged resources intended to be identical across installs.
- `state_dirs` are mutable warm-start runtime state that can change over time.
- During pack, `state_dirs` content is stored under `state_snapshots/<state-dir>/...` to keep state semantics separate from asset paths.

Exclusion support:

- Structured entries support per-directory excludes:

```yaml
state_dirs:
	- path: memory
		exclude:
			- daily/*.md
			- secrets/*
```

- Excluded files are omitted from snapshots and therefore are not restored on install.

Install restore and overwrite behavior:

- By default, install is warning-first and non-destructive when target state already exists.
- Existing state is preserved unless explicit overwrite is requested.
- Use `--state-overwrite` to replace existing state with snapshot content.

Backward compatibility:

- Agents without `state_dirs` preserve legacy asset-only pack/install behavior.

## Pack/Publish Refactor (Feature13)

Feature13 shifts command responsibilities to an archive-first source model and a mock-registry publish target.

### Pack (archive-first)

- `kinnoo pack <agent-dir>` writes by default to:
	- `~/.kinnoo/archive/<agent>/<version>/<agent>.kno`
- For tests and custom environments, archive root can be overridden with:
	- `KINNOO_ARCHIVE_ROOT`

### Publish (name-based source)

- `kinnoo publish <agent-name>`
- `kinnoo publish <agent-name> --local`

Behavior:

- Source artifact resolves from latest local archive version for `<agent-name>`.
- Target publishes to mock registry path:
	- `~/kinnoo-mock-registry-scratch/jerry/<agent>/<version>/<agent>.kno`
- If tagged target already exists, previous payload is preserved under:
	- `~/kinnoo-mock-registry-scratch/jerry/<agent>/untagged-<n>/`

### Install selectors

`kinnoo install` supports all of the following:

- `kinnoo install <name>` (latest from mock registry)
- `kinnoo install <name>==<version>` (exact version from mock registry)
- `kinnoo install <file-path/file.kno>` (backward-compatible direct archive install)

### List source modes

- `kinnoo list` (default local archive)
- `kinnoo list --local` (same as default)
- `kinnoo list --remote` (mock registry inventory)

### Search source modes

- `kinnoo search <query>` (default local archive)
- `kinnoo search --local <query>` (same as default)
- `kinnoo search --remote <query>` (mock registry inventory)

Search and list preserve consistent output shape (`name`, `latest`, `description`) and use case-insensitive matching for search name/description filtering.

### Migration notes from Feature12

- Old publish form:
	- `kinnoo publish <archive.kno>`
- New canonical publish form:
	- `kinnoo publish <agent-name>`

- Old registry docs centered on `~/.kinnoo/registry/` as primary source/target.
- Feature13 split:
	- source of truth for packaged artifacts: local archive (`~/.kinnoo/archive/...`)
	- publish target: mock registry (`~/kinnoo-mock-registry-scratch/jerry/...`)
