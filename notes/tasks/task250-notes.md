# Task250 - feature44 published agents framework column with N/A fallback

## Summary
- Extended agents row view-model generation in `server/routes/web_agents.py` to include a `framework` value.
- Implemented deterministic fallback to `N/A` when `framework` is missing or blank in the latest manifest metadata.
- Added a new Framework column in `server/templates/agents.html` while preserving existing column order and behavior otherwise.
- Added mapped integration test `server/tests/test_web_agents.py::test_agents_table_framework_column_and_na_fallback`.

## Files changed
- `server/routes/web_agents.py`
- `server/templates/agents.html`
- `server/tests/test_web_agents.py`
- `TASKS.txt` (task250 status moved to `needs-review`)

## Tests run (targeted only)
- `python3 -m pytest server/tests/test_web_agents.py::test_agents_table_framework_column_and_na_fallback server/tests/test_web_agents.py::test_listing_and_search -q`
- Result: `2 passed`

## Bug/error notes
- Bug class: brittle HTML regex assertion in new framework-column test.
- Attempts for this bug class: `1` (cap: `5`).
- Resolution: made regex assertions whitespace-tolerant to match server-rendered HTML formatting reliably.

## Teaching notes
- For server-rendered HTML tests, assert semantic structure with whitespace-tolerant patterns to avoid false negatives from template formatting changes.
- Keep additive UI changes backward-safe by extending row view-models with defaults (`N/A`) rather than changing existing fields in place.
- A focused regression pair (new test + nearest baseline test) is a pragmatic strategy for feature-level validation without full-suite runtime.

# Task229 - feature28 registry backend protocol + local backend refactor

## Summary
- Added a dedicated protocol module at `src/kinnoo/registry_backend.py` and moved protocol ownership out of `registry.py`.
- Added `LocalRegistryBackend` in `src/kinnoo/registry_backends.py` as the canonical local implementation for feature28.
- Preserved backward compatibility by keeping `LocalFilesystemRegistryBackend` as an alias subclass.
- Added tenant-compatible `list_agents(...)` method in local backend while preserving single-tenant local semantics.
- Added mapped test327 in `tests/test_registry.py`: `test_registry_backend_protocol`.

## Tests and results
- `python3 -m pytest tests/test_registry.py::test_registry_backend_protocol` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes for task229.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- Protocol-first design keeps higher-level command/service code decoupled from storage implementation details.
- Backward-compatible aliases are an effective migration strategy during incremental architecture refactors.
- Forward-compatible method signatures (for example tenant-aware hooks) reduce churn when adding remote multi-tenant backends.
