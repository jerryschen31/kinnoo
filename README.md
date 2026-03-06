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

## Local registry commands (Feature12)

Kinnoo supports a local agent registry rooted at `~/.kinnoo/registry/`.

### Publish

- `kinnoo publish <archive.kno>`
- `kinnoo publish <archive.kno> --local`

Both commands publish into local registry layout:

- `~/.kinnoo/registry/<name>/<version>/`

If the same `<name>==<version>` is published twice, Kinnoo fails with a clear duplicate error and does not overwrite existing content.

### Install selectors

Kinnoo install supports all of the following:

- `kinnoo install <file.kno>` (direct archive compatibility path)
- `kinnoo install <name>` (resolve latest published version from local registry)
- `kinnoo install <name>==<version>` (resolve an explicit version)

Versioned behavior example:

- if `weather-agent` has versions `1.0.0` and `2.0.0` in local registry:
	- `kinnoo install weather-agent` installs latest (`2.0.0`)
	- `kinnoo install weather-agent==1.0.0` installs that exact version

### List

- `kinnoo list`

Output includes one row per agent with:

- name
- latest version
- description (from published manifest metadata)

### Search

- `kinnoo search <query>`

Search performs case-insensitive substring matching on agent name and description metadata.

Example:

- `kinnoo search weather`
- `kinnoo search forecasting`
