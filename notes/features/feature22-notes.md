## Human and TechLead Review 1

Before I make any changes to files, let me present the full updated spec and get your approval.

---

## Proposed Updated Feature22

**Title:** Asset Bundling

**Manifest field:** `assets` (replaces `data`)

**Manifest syntax:**
```yaml
assets:
  paths:
    - data/embeddings.npz
    - data/reference_docs/
    - models/classifier.onnx
  bundle: true              # optional, default: true
```

**Key semantics:**
- `assets.paths`: list of relative paths (files or directories) to include as bundled assets
- `assets.bundle`: optional boolean (default `true`). When `false`, `kinnoo pack` skips asset inclusion in the `.kno` archive — useful when assets are large and distributed separately, or when the agent fetches them at runtime.
- Directories are included recursively — specifying `data/` includes all files under `data/`
- Paths must be relative to the agent root (path traversal rejected)

**Acceptance criteria (revised):**

| AC | Description |
|---|---|
| AC1 | Manifest validator accepts an optional `assets` field as an object with `paths` (list of strings) and optional `bundle` (bool, default `true`). Invalid structure produces clear errors. |
| AC2 | `kinnoo pack` includes all declared asset paths (files and directories recursively) in the archive under their original relative paths when `bundle` is `true` (default). |
| AC3 | `kinnoo pack` skips asset inclusion when `assets.bundle: false`, printing a message: `Assets declared but bundling disabled — assets will not be included in archive.` |
| AC4 | `kinnoo pack` rejects asset paths that use path traversal (e.g., `../secret`) with a clear security error. |
| AC5 | `kinnoo pack` warns if a declared asset path does not exist in the agent directory. |
| AC6 | `kinnoo install` extracts asset files and directories to their correct relative paths in the installed agent directory. |
| AC7 | `kinnoo pack` warns when total archive size exceeds 100 MB (default) or a configurable `max_bundle_size_mb` from manifest. |
| AC8 | `kinnoo inspect` displays declared asset paths and their sizes when inspecting an agent or archive. |
| AC9 | Agents without an `assets` section are unaffected — pack/install behavior is identical to pre-feature22 (regression check). |
| AC10 | `kinnoo pack` runs a filename blocklist check on asset paths, warning on known secret file patterns (`.env`, `.pem`, `.key`, `id_rsa`, `credentials.json`, `*.p12`, `*.pfx`, `token.txt`, etc.). |
| AC11 | `kinnoo pack` runs a regex credential scan on text-based asset files (≤ 1MB, valid UTF-8), warning on common secret patterns (AWS key prefixes, private key headers, bearer tokens, API key prefixes). Binary files are skipped. |
| AC12 | Asset credential scan warnings are non-blocking (pack continues) but clearly visible, with a disclaimer that heuristic scanning is not a substitute for manual review. |

**Notes (revised):**
- REGRESSION RISK: changes pack and install archive handling → SWE agent must run existing pack/install regression tests.
- Reuse existing `files` inclusion logic where possible but keep `assets` semantically separate.
- Path traversal check already exists in `pack_command.py` for extra files — extend it to asset paths.
- Asset credential scanning extends `code_sweep.py` with two new capabilities: filename blocklist and text-file regex scan.
- Filename blocklist patterns: `.env`, `.pem`, `.key`, `id_rsa`, `id_ed25519`, `credentials.json`, `*.p12`, `*.pfx`, `.htpasswd`, `service_account.json`, `token.txt`, `*.keystore`.
- Text-file secret patterns: `AKIA[0-9A-Z]{16}` (AWS), `-----BEGIN.*PRIVATE KEY-----`, `Bearer `, `ghp_`, `gho_`, `sk-`, `sk_live_`, `pk_live_`, `xox[bpras]-`.
- Binary files (non-UTF-8 or > 1MB) are excluded from text scanning for performance.
- The `assets.bundle` field provides a clean opt-out without removing asset declarations from the manifest — useful for `kinnoo inspect` to still show what assets the agent expects.

**Documentation addition:** A new `### assets` section in [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md) explaining:
- What qualifies as an asset
- Supported path types (files and directories, recursive)
- The `bundle` flag
- Secret scanning behavior
- Examples

---

**Do you want me to proceed with updating FEATURES.txt and docs/manifest-schema-reference.md with these changes?** I'm also happy to adjust any of the points above based on your feedback before committing.

A few open questions for you:
1. **`max_bundle_size_mb`** — should this go inside the `assets` block (e.g., `assets.max_size_mb`) or stay top-level? The existing AC6 mentions it as a top-level manifest field.
2. **Severity of credential scan hits** — should finding a known secret pattern (e.g., `-----BEGIN RSA PRIVATE KEY-----` in a data file) be a **blocking error** that aborts pack, or just a **warning** like the code sweep? My current proposal says non-blocking, but a private key header is pretty damning.