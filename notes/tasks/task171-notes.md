# Task171 - feature31 pack/install archive behavior for node_modules and lockfiles

## Summary
- Implemented Node.js archive collection safeguards in [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py):
  - Added node_modules path detection for archive candidates.
  - Excluded node_modules content from both manifest-declared additional files and asset bundle collection when `runtime.language: nodejs`.
  - Added explicit auto-inclusion of Node package metadata files in archive output:
    - `package.json`
    - `package-lock.json`
    - `pnpm-lock.yaml`
    - `npm-shrinkwrap.json`
    - `yarn.lock`
  - Added guard requiring `package.json` for nodejs pack flow so install remains reproducible.
- Added scoped regression test267 in [tests/test_pack.py](tests/test_pack.py):
  - `test_feature31_pack_node_modules_excluded_lockfiles_preserved`
  - Verifies archive excludes `node_modules`, preserves package metadata/lockfiles, and install path invokes Node dependency restore (`npm install`) using archived metadata.
- Updated `task171` status to `needs-review` in [TASKS.txt](TASKS.txt).

## Tests and results
- `python3 -m pytest tests/test_pack.py::test_feature31_pack_node_modules_excluded_lockfiles_preserved` -> `1 passed`

## Bug/error notes
- Encountered one error: `IndentationError` in the new test block due mixed indentation after insertion.
- Fixed by normalizing indentation in the added test function.
- Same bug/error class fix attempts: `1` (below the 5-attempt limit).

## Teaching notes
- For reproducible Node installs, package metadata is the source of truth, not the materialized `node_modules` tree. Archiving lockfiles plus `package.json` keeps installs deterministic while avoiding large, non-portable bundles.
- Runtime-specific archive filters are safer when applied at file-collection boundaries, so “do-not-bundle” directories (like `node_modules`) are blocked regardless of where they were declared (assets or additional files).
- Regression tests should validate both artifact shape (archive contents) and downstream behavior (install command path). This reduces the chance of passing “contents-only” tests while breaking real install flows.
