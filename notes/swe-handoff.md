# SWE Handoff - Feature23

## Feature
- ID: `feature23`
- Title: `MCP Server Runtime Type - Schema & Lifecycle`
- Goal: Add first-class `runtime.type: mcp-server` support in manifest validation and runtime execution, with supervisor-managed lifecycle, readiness probes, streaming, graceful shutdown, and trace logging.

## Scope Summary
Implement support for long-running MCP server agents while preserving existing one-shot behavior.

- Schema/validator: accept `mcp-server` runtime type.
- Runtime: route mcp-server runs through a dedicated supervisor module.
- Readiness: support TCP and stdout-marker probe modes plus default fallback behavior.
- Shutdown: SIGINT -> SIGTERM -> timeout -> SIGKILL escalation.
- Observability: trace logs record start/stop and exit metadata.
- Regression: one-shot mode must remain unchanged.

## Task Execution Order
Tasks are sequential for this feature:

1. `task141` - schema support for `mcp-server`
2. `task142` - supervisor lifecycle + readiness probes
3. `task143` - integrate supervisor into `run_command`
4. `task144` - graceful shutdown + trace logging
5. `task145` - one-shot regression gate

## Task-to-Test Mapping

- `task141` -> `test214`
- `task142` -> `test216`, `test221`
- `task143` -> `test215`, `test218`
- `task144` -> `test217`, `test219`
- `task145` -> `test220`

## AC Coverage Mapping (Feature23)

- AC1 -> `test214`
- AC2 -> `test215`
- AC3 -> `test216`
- AC4 -> `test217`
- AC5 -> `test218`
- AC6 -> `test219`
- AC7 -> `test220`
- AC8 -> `test221`

## Primary Files to Modify

- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `src/kinnoo/supervisor.py` (new)
- `src/kinnoo/run_command.py`
- `src/kinnoo/cli.py` (only if runtime wiring requires parser/dispatch updates)
- `tests/test_validator.py`
- `tests/test_cli.py`
- `tests/test_trust_baseline.py`

## Design Constraints

- Keep lifecycle logic out of `run_command.py` as much as possible; place process control in `src/kinnoo/supervisor.py`.
- Keep one-shot path behavior unchanged.
- Preserve real-time streaming semantics already used in run flow.
- Keep readiness behavior deterministic and testable.
- Do not expose secret values in logs or stdout/stderr diagnostics.

## Implementation Guidance

### 1) Runtime Type Schema
- Add `mcp-server` to supported runtime types.
- Keep invalid `runtime.type` errors explicit and list allowed values.

### 2) Supervisor API
Recommended minimal API (shape can vary as long as behavior is equivalent):

- `start_server(...)`
- `wait_until_ready(...)`
- `stream_output(...)`
- `shutdown_server(...)`

Use a small readiness strategy model:

- TCP check (port-based)
- stdout marker check
- fallback: if no readiness config, use default TCP when `runtime.port` exists, else immediate-ready

### 3) Run Integration
- For `runtime.type == one-shot`: keep existing path.
- For `runtime.type == mcp-server`: start supervisor and block until interrupted.

### 4) Shutdown Semantics
- On Ctrl+C/SIGINT:
	- send SIGTERM
	- wait timeout
	- send SIGKILL if still alive

### 5) Trace Logging
- Record:
	- start timestamp
	- stop timestamp
	- exit code or signal

## Regression & Validation Commands

Run these after implementation:

```bash
python3 src/validate_project_manifests.py
python3 -m pytest tests/test_validator.py -k feature23
python3 -m pytest tests/test_cli.py -k feature23
python3 -m pytest tests/test_trust_baseline.py -k feature23
python3 -m pytest tests/test_regression_v1.py::test_feature23_no_regression_for_one_shot_runtime
```

Then run broader regression for runtime/CLI confidence:

```bash
python3 -m pytest tests/test_cli.py tests/test_validator.py tests/test_regression_v1.py
```

## Delivery Checklist

- [ ] Tasks moved through status flow: `not-started -> in-progress -> needs-review`
- [ ] All feature23 tests implemented and passing
- [ ] AC1-AC8 coverage confirmed in TESTS mapping
- [ ] One-shot regression evidence captured
- [ ] No secret leaks in logs/output
- [ ] Manifest validation script passes

