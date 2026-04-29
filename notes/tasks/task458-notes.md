# task458 Notes

## Summary
- Implemented standardized README enrichment for init scaffolds:
  - explicit entrypoint edit guidance,
  - explicit `kinnoo.yaml` manifest guidance,
  - folder guide table for complete templates,
  - footer with CLI version and schema version.
- Applied README standardization across Python, JS, TS, and OpenClaw scaffold branches.
- Added regression test:
  - `tests/test_init.py::test_init_readme_content`

## Files changed
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k test_init_readme_content`
- Result:
  - `1 passed, 58 deselected`

## Teaching notes
- A small post-processing helper for generated docs (`_standardize_readme`) is cleaner than duplicating README edits across each framework branch.
- Footer provenance markers (CLI version + schema version) improve traceability when users share scaffolded agents across environments.
