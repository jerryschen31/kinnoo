# Task253 - Add mcp-server framework option to kinnoo init

## Summary
- Implemented `task253` to add `mcp-server` as a supported framework option for `kinnoo init`.
- Updated CLI help/examples so `kinnoo init -h` includes explicit mcp-server initialization usage.
- Added mcp-server scaffold templates (manifest, run script, README) and wired them into init generation flow.
- Added/updated tests for mcp-server framework acceptance, scaffold generation, and help output example coverage.

## Code Changes
- `src/kinnoo/cli.py`
  - Added `mcp-server` to `--framework` choices.
  - Added help epilog example:
    - `kinnoo init my-mcp-server --framework mcp-server`
  - Updated framework help text list to include `mcp-server`.

- `src/kinnoo/init_command.py`
  - Added `mcp-server` to `SUPPORTED_FRAMEWORKS`.
  - Added template imports for mcp-server scaffold constants.
  - Added dedicated manifest selection branch for mcp-server:
    - uses `MCP_SERVER_KINNOO_YAML_TEMPLATE`.
  - Added mcp-server entry to framework template mapping:
    - `MCP_SERVER_RUN_PY`, `MCP_SERVER_REQUIREMENTS`, `MCP_SERVER_README`.
  - Kept metadata append logic (`framework`/`model`) off for frameworks with dedicated manifest templates (`openclaw`, `mcp-server`).

- `src/kinnoo/templates.py`
  - Added `MCP_SERVER_RUN_PY`:
    - minimal newline-delimited JSON-RPC stdio loop.
    - supports `initialize`, `tools/list`, `tools/call` (`echo` tool).
  - Added `MCP_SERVER_REQUIREMENTS` (empty by default).
  - Added `MCP_SERVER_README` with run and smoke-test examples.
  - Added `MCP_SERVER_KINNOO_YAML_TEMPLATE`:
    - `framework: mcp-server`
    - `runtime.type: mcp-server`
    - `channels: [stdio]`
  - Fixed escaped braces in README JSON examples so `.format(name=...)` does not raise `KeyError`.

- `tests/test_init.py`
  - Extended valid framework acceptance test to include `mcp-server`.
  - Added `test_framework_mcp_server_scaffold_generation` (test354):
    - verifies generated files exist.
    - validates manifest.
    - asserts `framework: mcp-server`, `runtime.type: mcp-server`, and `channels` includes `stdio`.
  - Added `test_init_help_includes_mcp_server_example` (test355):
    - verifies `kinnoo init -h` contains explicit mcp-server example.

- `TASKS.txt`
  - Updated `task253` status to `needs-review` after implementation and test wiring.

## Manifest Validation
- Ran:
  - `python3 scripts/validate_project_manifests.py`
- Result:
  - `Validation passed: manifests are consistent`

## Test Runs and Results
- Focused task-related test run:
  - `python3 -m pytest tests/test_init.py -k "mcp_server or framework_valid or feature26_mcp_client"`
  - Result: `5 passed, 42 deselected`

- Full-suite run attempted once (as requested initially):
  - `python3 -m pytest`
  - Initial result: 2 failures unrelated to task253 implementation, both in publish regression path:
    - `tests/test_cli.py::test_backend_selection`
    - `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`

- Regression compatibility fix applied:
  - `src/kinnoo/publish_command.py`
  - Added backward-compatible `agent_name` alias handling for `publish_agent(...)` call sites.

- Verification of those failures after fix:
  - `python3 -m pytest tests/test_cli.py::test_backend_selection tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
  - Result: `2 passed`

- Per user instruction, no second full-suite rerun was performed.

## Notes
- The mcp-server scaffold is intentionally minimal and deterministic for reliable testability.
- The generated server template is usable as a baseline MCP stdio server and can be extended with additional tools/capabilities.
