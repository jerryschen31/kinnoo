## 2026-03-06 — SWE Progress Summary (Feature12 task77 / test104)

- Implemented `task77` by documenting local registry workflows in:
	- `README.md`
	- `docs/manifest-schema-reference.md`
- Added/updated documentation coverage for:
	- `kinnoo publish <archive.kno>` and `kinnoo publish <archive.kno> --local`
	- canonical local registry layout `~/.kinnoo/registry/<name>/<version>/`
	- duplicate publish no-overwrite behavior
	- install selector forms and compatibility:
		- `kinnoo install <file.kno>`
		- `kinnoo install <name>`
		- `kinnoo install <name>==<version>`
	- multi-version latest/exact example for `research-agent`
	- local registry discovery commands:
		- `kinnoo list`
		- `kinnoo search <query>`

### Test coverage (test104)

- Added `tests/test_docs.py::test_feature12_docs_cover_local_registry_flows`.
- Test verifies both docs files include required Feature12 command examples and versioned install examples.

### Validation results

- `python3 -m pytest tests/test_docs.py` → passed (`3 passed`)
- `python3 scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task77` status set to `needs-review`.
