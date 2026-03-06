# Task89 — Document pack/publish/archive/registry refactor

## What was implemented
- Updated `README.md` to document Feature13 command semantics and migration guidance:
	- archive-first `pack` destination (`~/.kinnoo/archive/<agent>/<version>/<agent>.kno`)
	- name-based `publish` source (`kinnoo publish <agent-name>`) and mock registry target (`registry-scratch/jerry/...`)
	- untagged rollover behavior for existing tagged publish targets (`untagged-<n>`)
	- source modes for `list` and `search` (`default/--local/--remote`)
	- install selector forms including backward-compatible file-path mode
	- explicit migration notes from Feature12 (`publish <archive.kno>` -> `publish <agent-name>`)
- Updated `docs/manifest-schema-reference.md` with matching Feature13 behavior and migration section for consistency with README.
- Added `tests/test_docs.py::test_feature13_docs_cover_archive_registry_refactor` (test117) to verify required docs coverage.

## Tests added/updated
- Added `test_feature13_docs_cover_archive_registry_refactor` in `tests/test_docs.py` (test117).

## Commands and results
- `python3 -m pytest tests/test_docs.py -q`
	- Result: `4 passed`

## Status updates
- Updated `TASKS.txt`: `task89` status moved to `needs-review`.
