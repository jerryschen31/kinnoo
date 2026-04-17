# Task155 - feature26 filesystem MCP runtime permission enforcement

## Summary
- Implemented runtime permission guardrails in `scratch/feature26-filesystem-mcp-server/run.py` via a dedicated wrapper layer (not CLI core):
  - `FilesystemPermissionError`
  - `FilesystemPermissions`
  - `permissions_from_manifest(...)`
  - `FilesystemPermissionGate.assert_allowed(...)`
- Enforced default-safe behavior when permissions are omitted:
  - `read_only=True`
  - `allow_write=False`
  - `allow_create=False`
- Added explicit opt-in behavior for write/create and sandbox checks using `allowed_paths`.
- Added task155 runtime test in `tests/test_registry.py`:
  - `test_feature26_filesystem_permissions_runtime_enforcement` (test238)
- Updated task155 status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_registry.py::test_feature26_filesystem_permissions_runtime_enforcement` -> `1 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- Encountered a dynamic-module loading issue while importing the scratch fixture in the test (dataclass processing expected the module to be present in `sys.modules`).
- Resolved by registering the module in `sys.modules` before `exec_module(...)`.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Runtime policy enforcement belongs at the runtime boundary (wrapper/tool layer), while schema/type validation belongs in validator code; splitting these concerns keeps behavior testable and easier to evolve.
- “Safe defaults” are a key design pattern in agent systems: default deny for mutating capabilities reduces blast radius and supports progressive permission elevation.
- When dynamically importing modules in tests, register them in `sys.modules` prior to execution to avoid subtle issues in introspection-heavy features like `dataclasses`.
