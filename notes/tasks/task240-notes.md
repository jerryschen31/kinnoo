# Task240 - feature29 JSON metadata model (3-tier)

## Summary
- Added metadata package and strongly typed models:
  - `server/metadata/models.py`
  - `VersionMetadata` (source-of-truth per tenant/agent/version)
  - `AgentIndex` and `AgentVersionSummary` (per-agent version listing)
  - `GlobalIndex` and `GlobalAgentSummary` (tenant-level discoverability)
  - schema version constant `v1` included in payloads.
- Added metadata manager:
  - `server/metadata/manager.py`
  - JSON read/write helpers through `StorageBackend`
  - canonical metadata keys under `metadata/` prefix
  - upsert flow that writes version metadata then derives/updates agent index and global index
  - retry-based read-modify-write strategy for global index updates.
- Added package exports in `server/metadata/__init__.py`.
- Added mapped test338 in `server/tests/test_metadata.py`:
  - verifies create/read/update behavior for all three metadata document tiers,
  - verifies schema_version presence,
  - verifies adding a new version updates both agent and global indexes.

## Tests and results
- `python3 -m pytest server/tests/test_metadata.py::test_metadata_model` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes for task240.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- Treating version metadata as the source of truth simplifies reconciliation: aggregate indexes can always be rebuilt from immutable version-level docs.
- Index managers should separate path derivation from document mutation to keep storage contracts stable and testable.
- For multi-writer safety, a best-effort retry loop around read-modify-write global aggregates reduces index drift risk without overcomplicating early implementations.
