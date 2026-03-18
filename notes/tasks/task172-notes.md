# Task172 - feature31 Node.js preflight checks

## Summary
- Added reusable Node toolchain check helpers in [src/kinnoo/health_check.py](src/kinnoo/health_check.py):
  - `check_node_runtime_constraint(runtime_constraint)` verifies `node` presence and evaluates version constraints from `runtime.version`.
  - `check_node_package_manager_availability(package_manager)` verifies package manager executable availability on `PATH`.
- Integrated runtime-aware preflight branching in [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
  - For `runtime.language: nodejs`, preflight now checks Node binary/version and configured package manager availability.
  - Preserved existing Python preflight behavior and messages for Python agents.
  - Added Node-specific remediation guidance in both action lines and remediation summary.
- Extended Node install flow safeguards in [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - Added fail-fast checks for Node runtime/version and configured package manager before `npm/pnpm install` execution.
  - Added actionable install error guidance when toolchain checks fail.
- Added scoped regression test268 in [tests/test_run_preflight.py](tests/test_run_preflight.py):
  - `test_feature31_node_preflight_toolchain_guards`
  - Covers: missing node binary, node version below `>=22`, and missing configured package manager (`pnpm`).
- Updated `task172` status to `needs-review` in [TASKS.txt](TASKS.txt).

## Tests and results
- `python3 -m pytest tests/test_run_preflight.py::test_feature31_node_preflight_toolchain_guards` -> `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Treat runtime toolchain checks as explicit capability probes, not implicit subprocess failures. This gives deterministic diagnostics and faster remediation for users.
- Keep runtime branching narrow: reuse existing Python paths unchanged and add Node-specific checks only where needed. This minimizes regression risk while enabling multi-runtime support.
- Preflight checks are most useful when they include direct remediation language (install/upgrade Node, add package manager to `PATH`) tied to each failure mode.
