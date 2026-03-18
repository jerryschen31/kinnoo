# Task170 - feature31 Node.js dependency install via npm or pnpm

## Summary
- Implemented Node package-manager support in [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - Added runtime-aware Node dependency install branch for `runtime.language: nodejs`.
  - Added package-manager resolution with `npm` default and `pnpm` optional override via `runtime.package_manager`.
  - Added actionable failure handling that reports the exact failed command and package-manager stderr.
  - Preserved existing Python install behavior as-is by keeping venv/pip flow for non-node runtimes.
- Added schema constant in [src/kinnoo/schema.py](src/kinnoo/schema.py):
  - `SUPPORTED_NODE_PACKAGE_MANAGERS = ["npm", "pnpm"]`
- Added scoped regression test266 in [tests/test_install.py](tests/test_install.py):
  - `test_feature31_node_dependency_install_npm_and_pnpm`
  - Verifies npm default path, pnpm override path, and actionable failure output for pnpm install failures.
- Updated `task170` status to `needs-review` in [TASKS.txt](TASKS.txt).

## Tests and results
- `python3 -m pytest tests/test_install.py::test_feature31_node_dependency_install_npm_and_pnpm` -> `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For multi-runtime installers, resolve runtime intent from manifest first, then dispatch into runtime-specific installers. This keeps Python and Node concerns isolated and reduces cross-runtime regressions.
- Actionable install errors should include command context (for example `pnpm install`) and stderr details, because dependency resolution failures are typically environment-specific.
- Test external package-manager behavior with subprocess mocking at the install module boundary. This gives deterministic CI coverage of command selection logic without requiring npm/pnpm binaries on every test host.
