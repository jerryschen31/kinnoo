## SWE Handoff - Feature26 MCP Server Packages & Client Templates

### Context
- Feature: feature26 "MCP Server Packages & Client Templates"
- Goal: ship a proof-of-concept reference pair (MCP server package + mcp-client template) and enforce mcp-server permissions schema/runtime behavior.
- Scope: reference MCP server fixtures, permissions validation/enforcement, and new `--framework mcp-client` template generation.

### Tasks To Implement (Ordered)
1. `task154` - Filesystem MCP server fixture + permissions schema validation
2. `task155` - Filesystem runtime permission enforcement (read-only default)
3. `task156` - GitHub MCP server fixture + `mcp-client` init template
4. `task157` - AC coverage and focused regression gate

### Dependency Chain
- `task154` -> `task155` -> `task156` -> `task157`

### Design Constraints
- Build on feature23 mcp-server runtime support; do not regress one-shot runtime paths.
- `permissions` validation is MCP-server specific: enforce only when `runtime.type: mcp-server`.
- Filesystem permission enforcement belongs in MCP server wrapper logic, not kinnoo CLI core.
- Read-only must be default-safe: reject write/create unless explicitly enabled.
- Adding `mcp-client` framework must not break existing framework templates.

### Files Expected To Change
- `src/kinnoo/validator.py`
- `src/kinnoo/schema.py`
- `src/kinnoo/init_command.py`
- `src/kinnoo/templates.py`
- `tests/test_validator.py`
- `tests/test_pack.py`
- `tests/test_init.py`
- `tests/test_regression_v1.py`
- MCP fixture workspace paths under `scratch/` (reference server fixtures)

### AC-to-Test Mapping
- AC1 -> `test236`
- AC2 -> `test237`
- AC3 -> `test238`
- AC4 -> `test239`
- AC5 -> `test240`, `test242`
- AC6 -> `test241`, `test242`
- AC7 -> `test237`

### Suggested Implementation Notes
- Keep fixture manifests explicit and minimal; include only fields needed for valid pack/install behavior.
- Validate unknown `permissions` keys deterministically with actionable error messages.
- For runtime permissions, test both deny-by-default and explicit allow paths.
- In template README, include clear setup/run steps for connecting client template to packaged MCP server.

### Validation Commands (SWE)
- `python3 src/validate_project_manifests.py`
- `python3 -m pytest tests/test_validator.py -k feature26`
- `python3 -m pytest tests/test_pack.py -k feature26`
- `python3 -m pytest tests/test_init.py -k feature26`
- `python3 -m pytest tests/test_regression_v1.py -k feature26`
- `python3 -m pytest` (final regression gate)

### Done Criteria
- All feature26 ACs are covered by automated tests (`test236`-`test242`).
- Filesystem and GitHub MCP server fixtures are validation-clean and packable.
- `mcp-client` template generation is contract-compliant and documented.
- Existing framework template behavior remains regression-safe.
