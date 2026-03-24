# Task198 - feature35 docs and compatibility regression safeguards

## Summary
- Updated feature35 documentation in [README.md](README.md):
  - added a dedicated mutable state section clarifying `state_dirs` as mutable snapshots distinct from immutable `assets`,
  - documented `exclude` usage examples,
  - documented warning-first install behavior and explicit `--state-overwrite` control,
  - documented compatibility guarantee for manifests that omit `state_dirs`.
- Extended schema reference docs in [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md):
  - added explicit pack layout and install restore mapping examples for `state_snapshots/...`.
- Added docs coverage regression in [tests/test_docs.py](tests/test_docs.py):
  - `test_feature35_docs_cover_mutable_state_semantics`.
- Added test296 implementation in [tests/test_regression_v1.py](tests/test_regression_v1.py):
  - `test_feature35_assets_backward_compatibility_without_state_dirs` verifies asset-only pack/install/run behavior remains stable and archives without `state_dirs` do not include `state_snapshots/` content.
- Updated [TASKS.txt](TASKS.txt):
  - `task198` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_docs.py::test_feature35_docs_cover_mutable_state_semantics tests/test_regression_v1.py::test_feature35_assets_backward_compatibility_without_state_dirs` -> `2 passed`

## Bug/error notes
- No implementation bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Keeping mutable state (`state_dirs`) and immutable resources (`assets`) semantically separate is a portability and safety pattern: state can be selectively omitted/overwritten while assets remain deterministic package resources.
- Regression tests for compatibility should assert both positive behavior (assets still bundled/usable) and negative behavior (no unintended `state_snapshots/` entries when `state_dirs` is absent).
- For operator-facing docs, include both policy and concrete path examples; this reduces ambiguity and makes testable documentation contracts easier to maintain.
