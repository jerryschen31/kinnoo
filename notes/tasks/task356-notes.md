# task356 notes

## Summary
- Added `src/kinnoo/diff_command.py` with archive comparison primitives for manifest and file-tree changes.
- Implemented deterministic manifest diffs for `dependencies`, `env_vars`, and `permissions`.
- Implemented deterministic file-tree change detection (`added`, `removed`, `modified`) using sorted paths and checksum comparison for shared files.
- Added new CLI subcommand wiring: `kinnoo diff <archive-a.kno> <archive-b.kno>` in `src/kinnoo/cli.py`.
- Added integration regression test `tests/test_cli.py::test_feature73_diff_manifest_and_files`.

## Teaching Notes
- Stable ordering in diff output is crucial for review ergonomics and machine-assertable tests.
- Separating manifest-level and file-level deltas helps operators reason about behavior changes vs. payload changes.
- Hash-based modified-file detection gives deterministic semantics independent of zip metadata ordering.

## Validation
- `python3 -m pytest tests --testmon -k test_feature73_diff_manifest_and_files`
