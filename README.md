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
