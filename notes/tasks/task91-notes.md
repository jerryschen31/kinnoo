# Task91 — Use absolute mock registry scratch path

## What was implemented
- Updated default mock registry backend root in `src/kinnoo/registry_backends.py`:
	- from relative `registry-scratch/jerry`
	- to home-absolute `~/kinnoo-mock-registry-scratch/jerry`
- Updated docs path references in:
	- `README.md`
	- `docs/manifest-schema-reference.md`
- Updated docs assertion coverage in `tests/test_docs.py` to assert new absolute mock registry path examples.
- Added `tests/test_publish_refactor.py::test_publish_uses_home_absolute_mock_registry_path` (test119):
	- verifies publish destination is `<home>/kinnoo-mock-registry-scratch/jerry/<agent>/<version>/<agent>.kno`
	- verifies destination is absolute
	- verifies behavior is independent of process CWD
	- verifies publish output reports that absolute target path

## Tests added/updated
- Added `test_publish_uses_home_absolute_mock_registry_path` in `tests/test_publish_refactor.py` (test119).
- Updated `tests/test_docs.py::test_feature13_docs_cover_archive_registry_refactor` expected mock registry path strings.

## Commands and results
- `python3 -m pytest tests/test_publish_refactor.py tests/test_docs.py -q`
	- Result: `8 passed`
- `python3 -m pytest tests/test_pack_refactor.py tests/test_publish_refactor.py tests/test_install_refactor.py tests/test_cli_registry_modes.py tests/test_docs.py -q`
	- Result: `16 passed`

## Status updates
- Updated `TASKS.txt`: `task91` status moved to `needs-review`.
