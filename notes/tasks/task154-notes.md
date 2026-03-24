# Task154 - feature26 filesystem MCP server package and permissions schema

## Summary
- Added MCP-server permissions schema constants in `src/kinnoo/schema.py`:
  - `MCP_SERVER_PERMISSION_KEYS`
  - `MCP_SERVER_PERMISSION_BOOL_FIELDS`
- Implemented mcp-server-specific permissions validation in `src/kinnoo/validator.py`.
- Added a first-party filesystem MCP fixture under `scratch/feature26-filesystem-mcp-server/` with a valid `runtime.type: mcp-server` manifest and packable layout.
- Added task154 tests:
  - `tests/test_validator.py::test_feature26_permissions_schema_validation` (test237)
  - `tests/test_pack.py::test_feature26_filesystem_mcp_fixture_valid_and_packable` (test236)
- Updated `task154` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature26_permissions_schema_validation` -> `1 passed`
- `python3 -m pytest tests/test_pack.py::test_feature26_filesystem_mcp_fixture_valid_and_packable` -> `1 passed`
- `python3 -m pytest tests/test_validator.py::test_feature26_permissions_schema_validation tests/test_pack.py::test_feature26_filesystem_mcp_fixture_valid_and_packable` -> `2 passed`
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- Encountered one indentation error in the new pack test function.
- Resolved by aligning function and block indentation with file style.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Gate schema rules by runtime mode when fields are mode-specific. Here, `permissions` is validated only for `runtime.type: mcp-server`, which avoids accidental regressions in one-shot manifests.
- Use deterministic allowlists for object keys and emit actionable "allowed keys" guidance so validation errors are self-healing.
- For packaging fixtures, keep the fixture minimal but realistic: valid manifest, entrypoint, and requirements are enough to prove packability without adding runtime complexity.
