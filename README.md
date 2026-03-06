# README

## Kinnoo is a developer platform for sharing agents.

## Packaging format

- `kinnoo pack` creates `.kno` artifacts as ZIP archives.
- `kinnoo install` expects `.kno` files in this ZIP-based format.

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
