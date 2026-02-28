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
