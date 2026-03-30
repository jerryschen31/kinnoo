# kinnoo.yaml Manifest Schema Reference

This document explains the fields in the `kinnoo.yaml` manifest — the heart of every Kinnoo agent package. It covers what each field specifies and provides concrete examples.

Archive note: Kinnoo package files use the `.kno` extension and are stored as ZIP archives.

---

## Field Definitions

### `entrypoint`

This is the file the `kinnoo` runtime executes when someone runs your agent. It's the "front door" of your agent — the single file that receives the input, runs the agent logic, and emits the output.

Think of it exactly like:
- `main.py` in a Python script
- `index.js` in a Node app
- `CMD` in a Dockerfile

Unlike a web server that stays alive, an agent entrypoint typically runs once per invocation: receive input → do agentic work → return output → exit.

**The MVP runtime contract is:** `python <entrypoint> "<input string>"`

So if `entrypoint: run.py`, the CLI executes:
```bash
python run.py "Help me refund an order"
```

---

### `dependencies`

This is the list of Python packages required to run the agent — equivalent to `requirements.txt` but declared inline in the manifest so the CLI can read and display them without inspecting the filesystem.

These are the same pip package names you'd write in `requirements.txt`:
- `openai` — to call GPT-4
- `langchain` — the orchestration framework
- `requests` — HTTP calls to external APIs

The CLI uses this list for two things: showing users what they're about to install (security warning), and driving `pip install` into the managed virtual environment.

---

### `inputs.type`

This describes the **shape of data the agent expects to receive**. For the MVP, only `text` is supported — meaning the agent receives a plain string as its only input (passed as a command-line argument).

Supported values now include:
- `text` / `string` for plain CLI input
- `json` for structured payload input
- `file` for path-oriented workflows

This exists as a field because in future versions it will expand to:
- `json` — structured data object
- `file` — a file path
- `image` — multimodal input
- `conversation` — a chat history array

Declaring this upfront makes agents self-describing and enables the CLI to validate input before invoking the agent, and enables future composition (chaining agents together).

---

### `outputs.type`

Same idea, but for what the agent **produces**. For the MVP, `text` means the agent prints a plain string to stdout and exits.

Supported values now include:
- `text` / `string`
- `json`
- `file`

Future values would include `json`, `file`, `stream` (for streaming token output), etc.

Declaring output type is what makes agents composable — if agent A outputs `json` and agent B accepts `json` as input, the CLI can eventually wire them together automatically.

Feature42 runtime contract note:
- when `outputs.type` includes `json` (for one-shot runtimes), stdout must be valid JSON;
- malformed JSON output fails deterministically with parse context (line/column).

Feature42 run modes:
- `kinnoo run <agent-dir> --json-input '<json>'`
- `kinnoo run <agent-dir> --json-file <json-file>`

---

### `runtime.type`

Declares the execution model of the agent. For the MVP, the only supported value is `one-shot` — meaning the agent process starts, receives input, produces output, and exits. The CLI will invoke it as `python <entrypoint> "<input>"` and wait for the process to terminate.

This field exists because future versions will support other execution models:
- `server` — a long-running HTTP server (FastAPI, Flask) that handles multiple requests
- `mcp-server` — a long-running Model Context Protocol server, compatible with GitHub Copilot, Claude, Cursor, etc.
- `worker` — a background queue consumer

The CLI's behavior on `kinnoo run` is determined entirely by this field.

---

### Feature62 openclaw-skill schema contract (`type`, `provenance`)

Feature62 adds an explicit OpenClaw package type and provenance object while keeping metadata minimal.

- `type` (optional): string
  - supported values: `agent`, `openclaw-skill`
  - if `type: openclaw-skill`, validator enforces OpenClaw runtime compatibility
- `provenance` (optional): object
  - `source_registry` (required when `provenance` is present): non-empty string
  - `source_version` (required when `provenance` is present): non-empty string
  - at least one of:
    - `source_slug` (non-empty string)
    - `source_url` (non-empty string)

OpenClaw compatibility checks:

- `framework: openclaw` requires:
  - `runtime.language: nodejs`
  - `runtime.type: daemon`
- `type: openclaw-skill` requires:
  - `framework: openclaw`
  - `runtime.language: nodejs`
  - `runtime.type: daemon`

Minimal metadata policy for Phase 6:

- `channels`, `skills`, and `state_dirs` are intentionally not part of this schema version.
- If present, validation fails with deterministic guidance to remove them.

Canonical examples:

```yaml
# Example 1: mirrored ClawHub skill
name: weather-skill
version: 1.2.3
framework: openclaw
type: openclaw-skill
runtime:
  language: nodejs
  version: ">=20"
  type: daemon
entrypoint: index.js
dependencies: []
inputs:
  type: string
outputs:
  type: string
provenance:
  source_registry: clawhub
  source_slug: weather/weather-skill
  source_url: https://clawhub.ai/skills/weather/weather-skill
  source_version: 1.2.3
```

```yaml
# Example 2: GitHub-origin agent (not skill)
name: repo-triage-agent
version: 0.4.0
framework: langgraph
type: agent
runtime:
  language: python
  version: ">=3.11"
  type: one-shot
entrypoint: run.py
dependencies:
  - langgraph>=0.2
  - openai>=1.0
inputs:
  type: string
outputs:
  type: string
provenance:
  source_registry: github
  source_url: https://github.com/acme/repo-triage-agent
  source_version: v0.4.0
```

```yaml
# Example 3: locally authored OpenClaw project
name: local-notes-skill
version: 0.1.0
framework: openclaw
type: openclaw-skill
runtime:
  language: nodejs
  version: ">=20"
  type: daemon
entrypoint: src/index.ts
dependencies: []
inputs:
  type: string
outputs:
  type: string
# provenance intentionally omitted for local authored project
```

Migration guidance:

- Replace flat source fields with a single `provenance` object.
- Remove `channels`, `skills`, and `state_dirs` from manifests.
- For local projects without external source lineage, omit `provenance`.

### Feature64 ClawHub import guidance (`kinnoo import --source clawhub`)

When importing mirrored skills from ClawHub:

- command shape:
  - `kinnoo import --source clawhub <owner>/<slug> [destination]`
- generated manifests use:
  - `type: openclaw-skill`
  - `framework: openclaw`
  - `provenance.source_registry: clawhub`
  - `provenance.source_version`
  - `provenance.source_slug` (and `source_url` when available)

Import report artifact:

- file: `kinnoo-import-report.json`
- requirement hints are grouped in deterministic sections:
  - `requirements.env`
  - `requirements.config`
  - `requirements.bin`
- unresolved next steps are listed in deterministic order under:
  - `unresolved`

Deterministic missing-slug behavior:

- if mirror metadata for `<owner>/<slug>` is missing, import fails with actionable guidance to run:
  - `kinnoo sync clawhub`

### Feature68 CI publish workflow contract

Reference workflow:

- `.github/workflows/kinnoo-publish.yml`

Required CI secrets/environment values:

- `KINNOO_REGISTRY_URL`
- `KINNOO_REGISTRY_TOKEN`
- `KINNOO_TENANT_SLUG`

Reference stage ordering:

- install dependencies
- preflight compatibility (`kinnoo check`)
- pack (`kinnoo pack`)
- publish (`kinnoo publish --remote`)

Strict-mode compatibility control:

- `KINNOO_CI_STRICT_MODE=1` enables strict publish flags in the workflow once strict-mode controls are available.

Failure behavior contract:

- workflow steps are fail-fast and must return non-zero on contract violations (missing secrets, check failures, pack failures, publish failures).

### Feature35 mutable state snapshots (`state_dirs`)

Feature35 defines `state_dirs` as mutable runtime state snapshot roots. This behavior is intentionally distinct from immutable `assets`.

Behavior summary:

- `assets` are immutable packaged resources and keep their existing bundle semantics.
- `state_dirs` are mutable runtime state and are archived under `state_snapshots/<state-dir>/...`.
- install restores state snapshots back into their declared state roots.

Structured `state_dirs` entries may include `exclude` patterns:

```yaml
state_dirs:
  - path: memory
    exclude:
      - daily/*.md
      - secrets/*
```

Exclude semantics:

- excluded files are omitted during pack snapshot collection,
- omitted files are not restored during install,
- non-excluded files remain part of snapshot/restore flow.

Install overwrite semantics:

- default install path is warning-first and non-destructive for existing state,
- existing state is preserved unless explicit overwrite control is provided,
- `kinnoo install ... --state-overwrite` enables deterministic replacement of existing state roots.

Example layout after pack when `state_dirs: [memory]`:

```text
state_snapshots/
  memory/
    core/profile.json
    sessions/latest.json
```

Example restore behavior:

- archive entry `state_snapshots/memory/core/profile.json`
- restores to `<install-target>/memory/core/profile.json`

Compatibility guarantee:

- manifests without `state_dirs` preserve pre-Feature35 asset-only behavior.

### Feature40 signed pack artifacts (`kinnoo pack --sign`)

Feature40 adds optional authenticity artifacts for packaged archives.

Usage:

- `kinnoo pack <agent-dir> --sign --signing-key <private-key.pem>`

Behavior summary:

- existing checksum behavior remains unchanged (`<archive>.kno.sha256` is still emitted),
- signed pack emits detached signature artifacts alongside the archive:
  - `<archive>.kno.sig`
  - `<archive>.kno.sig.json`

Signature metadata (`.sig.json`) fields:

- `schema_version`: currently `1`
- `algorithm`: currently `ed25519`
- `archive_filename`: archive basename
- `archive_sha256`: SHA256 of archive payload bytes
- `signature_filename`: detached signature basename
- `signature_base64`: base64-encoded detached signature bytes
- `public_key_fingerprint_sha256`: signer public-key fingerprint
- `public_key_pem`: signer public key for verification workflows
- `verification_hint`: operator-facing verification guidance

Security note:

- signing requires explicit private-key path via `--signing-key`; private key material is never written into pack logs.

---

### Feature9 optional fields (`description`, `author`, `license`, `env_vars`)

Feature9 adds optional metadata fields to `kinnoo.yaml`. These fields are optional-only and do not change validity for existing V1 manifests.

- `description` (optional): string
- `author` (optional): string
- `license` (optional): string
- `env_vars` (optional): list[string]

`env_vars` item constraints:
- each item must be a string
- each item must be non-empty (empty or whitespace-only values are invalid)

V1 compatibility note:
- manifests that omit `description`, `author`, `license`, and `env_vars` remain valid
- legacy validation behavior is unchanged when these fields are absent

Valid example:

```yaml
description: "Customer support agent"
author: "Kinnoo Team"
license: "MIT"
env_vars:
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY
```

Invalid `env_vars` example:

```yaml
env_vars:
  - OPENAI_API_KEY
  - ""
  - "   "
```

### Feature10 env_vars runtime security contract

When `env_vars` is declared, runtime resolution order is:

1. process environment
2. agent-local `.env`
3. masked interactive prompt (for unresolved names)

Non-disclosure invariant:

- secret values must never be printed, logged, or persisted
- diagnostics must reference variable names only

Safe troubleshooting:

- verify that required names are present in `env_vars`
- confirm those names are set in process environment or `.env`
- when prompted, enter values interactively without echoing values into logs

### Feature22 assets bundling (`assets`)

Feature22 adds an optional `assets` object to declare static files/directories that should be bundled with the agent archive.

Supported schema:

```yaml
assets:
  paths:
    - data/embeddings.npz
    - data/reference_docs/
    - models/classifier.onnx
  bundle: true
  max_bundle_size_mb: 100
```

Field semantics:

- `assets.paths` (optional): list of relative paths rooted at the agent directory. Each item may be a file or directory path.
- `assets.bundle` (optional): boolean, default `true`. When `false`, declared assets are retained as metadata but are not included in the `.kno` archive.
- `assets.max_bundle_size_mb` (optional): number, default `100`. Overrides the pack warning threshold for total archive size.

How inclusion works:

- directory paths are bundled recursively (for example, `data/` includes all nested files and folders)
- specifying a top-level folder is valid when you have multiple subfolders
- paths must stay within the agent root (path traversal such as `../` is rejected)
- manifests without `assets` remain fully compatible with pre-Feature22 pack/install behavior

What can be included:

- reference documents (for example markdown, txt, pdf)
- embeddings or vector artifacts
- local model files and weights
- runtime lookup tables, prompt libraries, and other static resources needed at runtime

Security sweep behavior for assets:

- pack performs filename-based checks for likely secret-bearing files and emits warnings
- pack performs regex-based checks on size-limited UTF-8 text assets and emits warnings for likely credentials
- binary assets are skipped for regex text scanning
- findings are warning-only during pack (heuristic, may produce false positives)

### Feature39 permissions schema (`permissions`)

Feature39 adds an optional `permissions` object for explicit capability declarations.

Supported fields:

- `permissions.network` (optional): boolean
- `permissions.filesystem_scope` (optional): enum string
  - allowed values: `none`, `read-only`, `workspace-write`, `full`
- `permissions.shell` (optional): boolean
- `permissions.browser` (optional): boolean
- `permissions.env_access` (optional): list[string]
  - each item must be a non-empty string

Validation behavior:

- unknown keys in `permissions` fail validation with allowed-key guidance
- invalid `filesystem_scope` enum values fail validation with supported-values guidance
- invalid `env_access` shape (non-list or non-string entries) fails validation with field-specific errors
- manifests without `permissions` remain valid (backward compatibility)

Example:

```yaml
permissions:
  network: true
  filesystem_scope: workspace-write
  shell: false
  browser: false
  env_access:
    - OPENAI_API_KEY
    - KINNOO_ENV
```

---

## Concrete Examples

### Example 1 — Simple LangChain customer support agent

```yaml
name: customer-support-agent
version: 0.1.0
entrypoint: run.py
runtime:
  language: python
  version: ">=3.10"
  type: one-shot
dependencies:
  - langchain
  - langchain-openai
  - requests
framework: langchain
inputs:
  type: text
outputs:
  type: text
```

**What happens at runtime:**
```bash
kinnoo run customer-support-agent "I need to cancel my order #1234"
# Internally: python run.py "I need to cancel my order #1234"
# Agent uses LangChain + OpenAI to reason and respond
# Prints answer to stdout
```

---

### Example 2 — CrewAI research agent

```yaml
name: research-summarizer
version: 0.2.1
entrypoint: agent.py
runtime:
  language: python
  version: ">=3.11"
  type: one-shot
dependencies:
  - crewai
  - openai
  - duckduckgo-search
framework: crewai
inputs:
  type: text
outputs:
  type: text
```

**What happens at runtime:**
```bash
kinnoo run research-summarizer "Summarize recent advances in fusion energy"
# Internally: python agent.py "Summarize recent advances in fusion energy"
# CrewAI orchestrates multiple sub-agents (researcher, writer)
# Final summary printed to stdout
```

---

### Example 3 — OpenClaw Node.js daemon manifest

```yaml
name: openclaw-agent
version: 1.0.0
entrypoint: run.js
framework: openclaw
runtime:
  language: nodejs
  version: ">=20.0.0"
  type: daemon
  package_manager: pnpm
channels:
  - stdio
  - events
skills:
  - skills/openclaw/core.md
state_dirs:
  - state/openclaw
dependencies: []
inputs:
  type: text
outputs:
  type: text
```

### Example 4 — Generic Node.js manifest with optional Feature33 fields

```yaml
name: generic-node-agent
version: 1.0.0
entrypoint: run.js
framework: custom-framework
runtime:
  language: nodejs
  version: ">=20.0.0"
  type: one-shot
  package_manager: npm
channels:
  - events
skills:
  - skills/common/assistant.md
state_dirs:
  - state/cache
dependencies: []
inputs:
  type: text
outputs:
  type: text
```

Compatibility behavior for Example 4:

- valid extension field shape is accepted
- OpenClaw-only constraints are not enforced because `framework` is not `openclaw`

---

## Key Insight: Framework Agnosticism

Notice that both examples look nearly identical from the CLI's perspective — `kinnoo` doesn't know or care that one uses LangChain and the other uses CrewAI. That's the entire point of the `entrypoint` + `inputs/outputs` contract: **the runtime abstraction makes the framework irrelevant to the platform.** The complexity lives inside `run.py` / `agent.py`, not in the manifest.

---

## Full Schema Reference Table

| Field            | Required | Type         | Constraints                                     |
|------------------|----------|--------------|-------------------------------------------------|
| name             | yes      | string       | non-empty, alphanumeric and hyphens             |
| version          | yes      | string       | valid semver (e.g., "0.1.0", "1.2.3")           |
| entrypoint       | yes      | string       | non-empty file path                             |
| runtime.language | yes      | string       | e.g., "python"                                  |
| runtime.version  | yes      | string       | version constraint (e.g., ">=3.10")             |
| runtime.type     | yes      | string       | supported values include `one-shot`, `mcp-server`, `daemon` |
| runtime.package_manager | no | string       | optional; allowed values: `npm`, `pnpm`          |
| dependencies     | yes      | list[string] | can be empty list                               |
| inputs.type      | yes      | string       | e.g., "text"                                    |
| outputs.type     | yes      | string       | e.g., "text"                                    |
| framework        | no       | string       | optional, e.g., "langchain", "crewai"           |
| channels         | no       | list[string] | optional; non-empty string items                |
| skills           | no       | list[string] | optional; relative paths only                   |
| state_dirs       | no       | list[string] | optional; relative paths only                   |
| assets           | no       | object       | optional; keys: `paths` (list[string]), `bundle` (bool, default true), `max_bundle_size_mb` (number, default 100) |
| description      | no       | string       | optional metadata                                 |
| author           | no       | string       | optional metadata                                 |
| license          | no       | string       | optional metadata                                 |
| env_vars         | no       | list[string] | optional; each item must be a non-empty string    |

---

## Manifest Cross-File Rule (TESTS.txt and TASKS.txt)

For project manifest consistency:

- In `TESTS.txt`, each item in `covers` must reference acceptance criteria only, using:
  - `feature: featureX`
  - `ac: ACY`
- Do not place `task: taskX` entries inside `TESTS.txt` `covers`.
- Task-to-test linkage belongs in `TASKS.txt` via each task's `tests: [testA, testB]` list.

This matches the manifest validator behavior in `src/validate_project_manifests.py`.

---

## `kinnoo inspect` command (Feature11)

`kinnoo inspect` displays manifest metadata from either a source directory or a packaged `.kno` archive.

Usage:

- `kinnoo inspect <agent-dir>`
- `kinnoo inspect <archive.kno>`

Examples:

```bash
kinnoo inspect ./my-agent
kinnoo inspect ./my-agent.kno
```

Output semantics:

- human-readable formatted text (not raw YAML)
- missing optional fields are omitted
- `env_vars` are names-only (never values)

Directory guidance behavior:

- if `kinnoo.yaml` is missing, inspect prints guidance with a minimal manifest example and exits non-zero
- if `requirements.txt` is missing, inspect prints guidance with:
  - `pip install uv`
  - `uv export --format requirements-txt > requirements.txt`

Common failure cases:

- missing target argument → `Usage: kinnoo inspect <target>`
- invalid archive format → clear invalid zip-based `.kno` error
- invalid manifest content → `Error: Manifest validation failed.` plus field-level validator messages

---

## `kinnoo run --preflight` command (Feature14)

`kinnoo run --preflight` performs run-readiness checks without executing agent entrypoint logic.

Usage:

- `kinnoo run <agent-dir> --preflight`
- `kinnoo run ./my-agent --preflight`

Preflight checklist semantics:

- output is checklist-style with deterministic pass/fail lines
- required checklist sections include runtime version, env vars, entrypoint, and dependencies
- all checks pass: output includes `Ready to run`
- one or more checks fail: output includes `Not ready to run` and `Remediation summary`
- preflight validates only and does not execute agent entrypoint logic

Preflight env var security semantics:

- output is names-only for env vars
- unresolved env var names may be listed for operator action
- env var values are never printed, logged, or persisted

---

## Trust baseline documentation reference (Feature15)

Feature15 introduces trust and transparency behavior that works alongside manifest-driven execution.

Install trust behavior:

- install summary includes agent/version/runtime/dependencies/env var names
- install confirmation prompt is `Continue with install? [y/N]:`
- `--yes` / `-y` keeps summary but bypasses confirmation
- unverified source warning appears when `<archive>.sha256` is missing

Unverified prompt behavior:

- warning text: `This agent is from an unverified source.`
- prompt (without `--yes`): `This agent is from an unverified source. Continue? (y/n):`

---

## Input Safety Guard reference (Feature18)

Feature18 adds an input safety check stage to `kinnoo run` before entrypoint execution.

Behavior contract:

- The guard evaluates user-provided run input and emits warnings when risky patterns are detected.
- The guard is non-blocking in interactive mode (warn + confirm).
- In non-interactive execution, flagged input aborts run by default.
- `--no-guard` is the explicit override for trusted CI/automation workflows.

Threat categories:

- SQL injection
- shell command injection
- path traversal
- SSRF
- XSS
- template injection

Type-aware model:

- Guard checks are type-aware and can scope detection by input type (`text`, `string`, `file_path`, `url`, `id`).
- Unknown input types fall back to full text-style scanning.

Pluggable architecture:

- Runtime integration depends on the `InputGuard` Protocol, not on a concrete implementation.
- The default implementation is provided via factory (`get_default_guard`).
- This design allows replacing regex heuristics with an ML guard in future versions without changing call sites.

Run trace log behavior:

- output path: `~/.kinnoo/logs/run.<TIMESTAMP>.log`
- filename and JSON timestamp are UTC-only
- log JSON keys are safe-only:
  - `timestamp`
  - `agent_name`
  - `agent-version`
  - `runtime_type`
  - `exit_code`
- trace log never includes input text, secret values, env var values, stdout, or stderr

Inspect/pack heuristic security sweep behavior:

- inspect shows `Security sweep:` output with either clean message or warnings
- clean message: `Security sweep: no env var exposure patterns detected (heuristic)`
- pack prints sweep warnings as non-blocking output
- disclaimer: `(heuristic scan — may produce false positives; not a substitute for code review)`

---

## Pack size reporting and warnings (Feature17)

Feature17 documents package size visibility across pack, inspect, and list flows.

Pack output contract:

- `kinnoo pack` prints final archive size:
  - `[kinnoo pack] Archive size: <human-readable>`
- If final archive size is strictly greater than 100 MB, pack prints:
  - `Warning: archive is large (X MB). Consider whether all dependencies are necessary.`

Inspect output contract:

- `kinnoo inspect <archive.kno>` includes archive size metadata:
  - `- Archive Size: <human-readable>`

List output contract:

- `kinnoo list`
- `kinnoo list --local`
- `kinnoo list --remote`

Each list row includes additive archive size visibility:

- `| size: <human-readable>`

Formatting consistency:

- size output uses stable units (`B`, `KB`, `MB`, `GB`)
- formatting logic is shared across pack, inspect, and list to avoid drift

Project-wide trust invariant:

- no-secret-values contract applies across trust paths
- env var diagnostics must remain names-only

---

## Archive integrity checksums (Feature16)

Feature16 introduces checksum sidecars across pack/install/inspect/publish to improve artifact integrity visibility and verification.

Checksum sidecar contract:

- sidecar path is sibling to archive: `<archive>.kno.sha256`
- sidecar line format is stable: `<sha256>  <archive-filename>`
- digest is lowercase SHA256 over archive bytes

Pack behavior:

- `kinnoo pack <agent-dir>` writes a checksum sidecar beside the stored archive artifact
- pack emits:
  - `[kinnoo pack] Checksum sidecar written: <path>`

Install behavior (`kinnoo install <file.kno>`):

- sidecar exists and checksum matches: install proceeds and prints `[kinnoo install] Archive checksum verified.`
- sidecar exists and checksum mismatches: install aborts with exact error:
  - `Archive integrity check failed — the file may be corrupted or tampered with`
- sidecar is missing: install warns and continues with exact warning:
  - `No checksum file found — archive integrity not verified`

Inspect behavior:

- `kinnoo inspect <archive.kno>` displays checksum metadata when valid sidecar is available:
  - `- Checksum (SHA256): <digest>`

Publish behavior:

- `kinnoo publish <agent-name>` copies `.kno.sha256` to registry destination when present at source
- sidecar absence is non-fatal; publish continues
- publish emits one of:
  - `Published checksum sidecar: <path>`
  - `Published checksum sidecar: (none found at source)`

---

## Pack/Publish Refactor commands (Feature13)

Feature13 refactors command responsibilities to an archive-first packaging source plus mock-registry publishing target.

### Pack destination

- `kinnoo pack <agent-dir>` writes to local archive by default:
  - `~/.kinnoo/archive/<agent>/<version>/<agent>.kno`
- Test/custom override:
  - `KINNOO_ARCHIVE_ROOT`

### Publish semantics

Canonical publish commands:

- `kinnoo publish <agent-name>`
- `kinnoo publish <agent-name> --local`

Behavior:

- source resolves latest local archive artifact for `<agent-name>`
- target path in mock registry:
  - `~/kinnoo-mock-registry-scratch/jerry/<agent>/<version>/<agent>.kno`
- if tagged target exists, prior payload rolls to:
  - `~/kinnoo-mock-registry-scratch/jerry/<agent>/untagged-<n>/`

### Install selectors

Supported forms:

- `kinnoo install <name>` (latest from mock registry)
- `kinnoo install <name>==<version>` (exact from mock registry)
- `kinnoo install <file-path/file.kno>` (backward-compatible direct file install)

### List source modes

- `kinnoo list` (default local archive)
- `kinnoo list --local` (same as default)
- `kinnoo list --remote` (mock registry)

### Search source modes

- `kinnoo search <query>` (default local archive)
- `kinnoo search --local <query>` (same as default)
- `kinnoo search --remote <query>` (mock registry)

Search behavior remains case-insensitive substring matching across name and description fields.

### Migration guidance from Feature12

- Previous publish form:
  - `kinnoo publish <archive.kno>`
- Feature13 canonical form:
  - `kinnoo publish <agent-name>`

- Previous docs centered on `~/.kinnoo/registry/` as primary source/target.
- Feature13 split of responsibilities:
  - packaging source-of-truth: local archive (`~/.kinnoo/archive/...`)
  - publish/install remote target: mock registry (`~/kinnoo-mock-registry-scratch/jerry/...`)
