# Task156 - feature26 github MCP server package and mcp-client init template

## Summary
- Added a first-party GitHub MCP server fixture under `scratch/feature26-github-mcp-server/` with a packable `runtime.type: mcp-server` manifest and minimal runnable entrypoint.
- Added `mcp-client` framework template support in init scaffolding:
  - `src/kinnoo/templates.py` now provides `MCP_CLIENT_RUN_PY`, `MCP_CLIENT_REQUIREMENTS`, `MCP_CLIENT_README`.
  - `src/kinnoo/init_command.py` now includes `mcp-client` in supported frameworks and framework template mapping.
  - `src/kinnoo/cli.py` now accepts `--framework mcp-client` via parser choices and help text.
- Added task156 tests:
  - `tests/test_pack.py::test_feature26_github_mcp_fixture_valid_and_packable` (test239)
  - `tests/test_init.py::test_feature26_mcp_client_template_generation` (test240)
  - `tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation` (test241)
- Updated task156 status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_pack.py::test_feature26_github_mcp_fixture_valid_and_packable` -> `1 passed`
- `python3 -m pytest tests/test_init.py::test_feature26_mcp_client_template_generation tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation` -> `2 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- Encountered two related issues during first test run:
  - `test239` was not collected because the new function was accidentally nested by indentation in `tests/test_pack.py`.
  - `test240/test241` failed because CLI parser choices in `src/kinnoo/cli.py` did not yet include `mcp-client`.
- Resolved by:
  - fixing test function indentation to top-level,
  - adding `mcp-client` to CLI init parser `--framework` choices/help.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- Keep framework allow-lists synchronized across all entry points (template mapping and user-facing CLI parser). Drift between these layers creates confusing, avoidable failures.
- For template features, test both generation semantics (artifact contents and README workflow) and runtime contract semantics (`sys.argv[1]` -> stdout). This mirrors how agent templates are actually consumed.
- Fixture-based packaging tests are a low-friction way to validate end-to-end behavior without coupling tests to external network services.
