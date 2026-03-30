# task357 notes

## Summary
- Extended `kinnoo diff` with machine-readable `--json` output in a stable schema.
- Implemented deterministic exit-code semantics for diff outcomes:
  - `0` when archives are identical,
  - `2` when differences are detected,
  - `1` for fatal input/processing errors.
- Kept text-mode output behavior while adding JSON payload generation in `src/kinnoo/diff_command.py`.
- Updated CLI diff dispatch to pass `--json` through to diff engine.
- Added regression test `tests/test_cli.py::test_feature73_diff_json_and_exit_codes`.

## Teaching Notes
- Exit-code contracts are part of your API surface; choose codes that map cleanly to CI branching.
- Stable JSON shape (`schema_version` + fixed keys) is important for long-lived automation compatibility.
- Keep human-readable and machine-readable output paths separate but driven by the same underlying diff data.

## Validation
- `python3 -m pytest tests --testmon -k test_feature73_diff_json_and_exit_codes`
