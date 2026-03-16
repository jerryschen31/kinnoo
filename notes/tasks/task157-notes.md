# Task157 - feature26 AC coverage and regression gate

## Summary
- Added `tests/test_regression_v1.py::test_feature26_framework_template_regression_gate` (test242).
- The regression gate executes a focused feature26 stability set to ensure adding `mcp-client` did not regress existing init framework template behavior.
- The gate also includes `tests/test_validator.py::test_feature26_permissions_schema_validation` to keep MCP permissions schema behavior in the focused regression path.
- Confirmed AC mapping for feature26 tests remains aligned in `TESTS.txt` (`test236` through `test242`).
- Updated `task157` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py -k feature26` -> `1 passed`
- `python3 -m pytest tests/test_pack.py -k feature26` -> `2 passed`
- `python3 -m pytest tests/test_init.py -k feature26` -> `2 passed`
- `python3 -m pytest tests/test_regression_v1.py -k feature26` -> `1 passed`

## Bug/error notes
- No task157 implementation or test failures were encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Regression gates should target contract boundaries, not implementation details. Here that means template generation behavior, manifest validity, and runtime I/O contract behavior.
- A focused gate can still be comprehensive when it composes existing acceptance tests (`test236`-`test241`) with one high-signal orchestrator (`test242`).
- In agentic systems, permission-policy regressions are security regressions; including schema validation in the gate reduces the chance of silently widening capability.

## Review 1 remediation follow-up
- Addressed AC5 gap by replacing the mcp-client template connection placeholder with a concrete JSON-RPC-over-stdio handshake flow in [src/kinnoo/templates.py](src/kinnoo/templates.py).
- The generated template now demonstrates:
	- launching an MCP server command from `KINNOO_MCP_SERVER_CMD`,
	- sending `initialize`,
	- sending `tools/list`,
	- printing deterministic success indicators to stdout.
- Addressed AC3 depth gap by adding a runtime handler path in [scratch/feature26-filesystem-mcp-server/run.py](scratch/feature26-filesystem-mcp-server/run.py) and extending [tests/test_registry.py](tests/test_registry.py) to assert permission enforcement through `tools/call` requests, not just direct helper invocation.

## Follow-up test results
- `python3 -m pytest tests/test_init.py::test_feature26_mcp_client_template_generation tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation` -> `2 passed`
- `python3 -m pytest tests/test_registry.py::test_feature26_filesystem_permissions_runtime_enforcement` -> `1 passed`
- `python3 -m pytest tests/test_regression_v1.py::test_feature26_framework_template_regression_gate` -> `1 passed`

## Additional teaching notes
- For protocol-client templates, a concrete handshake example (`initialize` + `tools/list`) is a better learning scaffold than prose placeholders because it demonstrates message shape and lifecycle semantics directly.
- End-to-end policy assertions should cross the request handler boundary. In agent systems, helper-level tests catch local logic bugs, but handler-path tests catch integration bugs in request parsing, action routing, and policy wiring.
