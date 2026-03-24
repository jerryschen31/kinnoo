## Tech Lead Review

### Findings (ordered by severity)

1. High: AC5 is only partially satisfied; current `mcp-client` template does not demonstrate an actual MCP connection flow.
- Feature AC5 requires a template that demonstrates connecting to an MCP server.
- The generated template currently includes an explicit placeholder comment instead of a concrete connection example.
- Evidence:
  - `src/kinnoo/templates.py` line 363: `Connection placeholder: replace this with your framework-specific MCP client.`
  - `src/kinnoo/templates.py` line 365: template prints metadata only (`[mcp-client template] ...`) rather than initiating a client session.
- Impact: contract/demo intent for AC5 is weakened; users receive scaffold guidance but not a true connection demonstration.

2. Medium: AC3 runtime assertion is helper-level, not end-to-end MCP tool-call path.
- AC3 expects runtime rejection of write/create tool calls in read-only mode.
- Current coverage validates permission-gate helper behavior in fixture module, not a full MCP protocol/tool-call execution path.
- Evidence:
  - `tests/test_registry.py` line 35 (`test_feature26_filesystem_permissions_runtime_enforcement`) imports fixture helpers and asserts `FilesystemPermissionGate` behavior.
- Impact: strong unit-style confidence, but incomplete proof that live MCP request handling path enforces the same behavior.

3. Process consistency: feature/task status drift.
- Feature26 is still `not-started` while task154-task157 are `needs-review`.
- Evidence:
  - `FEATURES.txt` line 1007: `status: not-started`
  - `TASKS.txt` lines 3035, 3054, 3075, 3094: `status: needs-review`
- Impact: governance metadata inconsistency before merge.

### AC Coverage Assessment
- AC1: Covered by `test236` (`tests/test_pack.py` line 751) for filesystem MCP fixture validity and packability.
- AC2: Covered by `test237` (`tests/test_validator.py` line 802) for permissions schema shape/type validation on mcp-server manifests.
- AC3: Partially covered by `test238` (`tests/test_registry.py` line 35) via permission-gate runtime helper behavior; lacks end-to-end MCP tool-call path assertion.
- AC4: Covered by `test239` (`tests/test_pack.py` line 782) for GitHub MCP fixture validity and packability.
- AC5: Partially covered by `test240` (`tests/test_init.py` line 633) for template generation and README workflow text, but blocked by missing concrete connection demonstration in template implementation.
- AC6: Covered by `test241` (`tests/test_init.py` line 655) for contract behavior and manifest validation.
- AC7: Covered by `test237` (`tests/test_validator.py` line 802) for unknown keys, boolean typing, and `allowed_paths` list typing.

### Task Review Summary
- task154: Implemented with manifest/schema + pack validation evidence.
- task155: Implemented with runtime permission helper enforcement tests; end-to-end enforcement depth remains follow-up.
- task156: Implemented with mcp-client framework addition and template tests; connection demonstration depth remains follow-up.
- task157: Implemented focused regression gate (`tests/test_regression_v1.py` line 224).

### Full Regression Result
- Command: `python3 -m pytest`
- Result: `238 passed, 1 skipped`
- Assessment: no cross-feature regressions detected.

### Recommendation Before Merge
- Do not merge yet.
- Required fixes:
  1. Upgrade `mcp-client` template to include a concrete MCP connection demonstration path (even if test-safe mocked mode is used) to satisfy AC5 intent.
  2. Add an end-to-end runtime test that exercises write/create MCP tool-call handling against the filesystem server wrapper in read-only mode (AC3 closure).
  3. Align feature/task statuses for review readiness.

### Suggested Follow-up Improvements
- Add a dedicated feature26 docs snippet in `docs/` showing server package + client template handshake command flow.
- Add explicit assertions that `permissions` validation is ignored for non-mcp runtime types (already present behavior, strengthen with messaging expectations).
- Add a focused `kinnoo init --framework mcp-client` snapshot-style test to guard README/run template drift over time.

### Verdict
- Needs follow-up before merge.

# Feature26 Review 1 remediation (task157 follow-up) - SWE Agent

## Summary
- Fixed AC5 gap by replacing the mcp-client template placeholder flow with a concrete MCP JSON-RPC-over-stdio handshake in [src/kinnoo/templates.py](src/kinnoo/templates.py).
- Updated [tests/test_init.py](tests/test_init.py) assertions so generation checks require concrete connection-demo artifacts (`KINNOO_MCP_SERVER_CMD`, `initialize`, `tools/list`, stdio request helper).
- Fixed AC3 depth gap by adding `handle_mcp_tool_call(...)` to [scratch/feature26-filesystem-mcp-server/run.py](scratch/feature26-filesystem-mcp-server/run.py) and extending [tests/test_registry.py](tests/test_registry.py) to enforce read-only/sandbox policy via end-to-end `tools/call` requests.

## Tests and results
- `python3 -m pytest tests/test_init.py::test_feature26_mcp_client_template_generation tests/test_init.py::test_feature26_mcp_client_template_contract_and_validation` -> `2 passed`
- `python3 -m pytest tests/test_registry.py::test_feature26_filesystem_permissions_runtime_enforcement` -> `1 passed`
- `python3 -m pytest tests/test_regression_v1.py::test_feature26_framework_template_regression_gate` -> `1 passed`

## Bug/error notes
- No new failures encountered while applying Review 1 fixes.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Concrete protocol demos in templates are valuable for onboarding because they encode both transport and payload conventions in executable form.
- Runtime security policy tests should include handler-path execution to validate integration wiring, not only local helper logic.

## Tech Lead Review 2

### Findings (ordered by severity)

1. Resolved: AC5 concrete MCP connection demonstration is now implemented.
- The `mcp-client` template now includes a real JSON-RPC-over-stdio handshake path instead of placeholder-only guidance.
- Evidence:
  - `src/kinnoo/templates.py` line 363 defines `_request_over_stdio(...)` for request/response transport.
  - `src/kinnoo/templates.py` lines 396-404 send concrete `initialize` and `tools/list` JSON-RPC calls.
  - `tests/test_init.py` lines 648-651 assert generated template content includes `KINNOO_MCP_SERVER_CMD`, `initialize`, `tools/list`, and `_request_over_stdio`.
- Assessment: AC5 implementation gap is closed.

2. Resolved: AC3 now has request-handler-path enforcement coverage, not helper-only coverage.
- The filesystem MCP fixture includes `handle_mcp_tool_call(...)` that processes `tools/call` requests and routes through permission checks.
- Tests now exercise both blocked and allowed `tools/call` flows through the handler path.
- Evidence:
  - `scratch/feature26-filesystem-mcp-server/run.py` line 115 defines `handle_mcp_tool_call(...)`.
  - `scratch/feature26-filesystem-mcp-server/run.py` lines 123-124 validate MCP `tools/call` request shape.
  - `tests/test_registry.py` line 35 tests helper + handler-level enforcement.
  - `tests/test_registry.py` lines 54-62 assert read-only blocking through `tools/call` handler.
  - `tests/test_registry.py` lines 88-115 assert allowed and sandbox-rejected behavior through handler requests.
- Assessment: AC3 depth gap is closed for the fixture runtime path.

3. Process consistency: feature26 status alignment is corrected for review state.
- Evidence:
  - `FEATURES.txt` shows `feature26` with `status: needs-review`.
- Assessment: governance metadata now matches task review stage.

### AC Coverage Re-check
- AC1: Covered (unchanged).
- AC2: Covered (unchanged).
- AC3: Covered with end-to-end `tools/call` handler-path assertions.
- AC4: Covered (unchanged).
- AC5: Covered with concrete stdio JSON-RPC handshake implementation and generation assertions.
- AC6: Covered (unchanged).
- AC7: Covered (unchanged).

### Regression Verification
- Command: `python3 -m pytest`
- Result: `238 passed, 1 skipped`
- Assessment: no regressions detected after remediation.

### Recommendation
- Technical remediation requested in Review 1 is complete.
- Feature26 is ready for Tech Lead approval flow, subject to normal PR review/merge controls.

### Verdict
- Approved for merge readiness from Tech Lead perspective.
