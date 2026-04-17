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
python3 scripts/validate_project_manifests.py
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


## Tech Lead Review

### Scope Reviewed
- Feature: feature23 (MCP Server Runtime Type - Schema & Lifecycle)
- Tasks reviewed: task141, task142, task143, task144, task145
- Tests reviewed: test214, test215, test216, test217, test218, test219, test220, test221

### Verdict
- Status: needs-follow-up before merge
- Summary: Implementation quality is strong overall and full-suite regression is green, but there is one AC coverage gap for Ctrl+C handling at the `kinnoo run` integration boundary.

### Evidence Checked
- Manifest/task/test linkage
  - `FEATURES.txt` links feature23 to `task141..task145`.
  - `TASKS.txt` marks `task141..task145` as `needs-review` and links expected tests.
  - `TESTS.txt` defines `test214..test221` and maps each to feature23 ACs.
- Code implementation
  - `src/kinnoo/schema.py`: `SUPPORTED_RUNTIME_TYPES` includes `mcp-server`.
  - `src/kinnoo/validator.py`: runtime type validator accepts both `one-shot` and `mcp-server` with explicit allowed-values messaging.
  - `src/kinnoo/supervisor.py`: readiness inference/probing, output streaming, SIGTERM->SIGKILL escalation.
  - `src/kinnoo/run_command.py`: mcp-server execution branch, readiness gating, SIGINT capture, lifecycle trace fields.

### AC Coverage Assessment
- AC1 (validator accepts mcp-server): covered by `test214` and implementation in validator/schema.
- AC2 (long-running subprocess mode): covered by `test215` and `run_command.py` mcp-server loop.
- AC3 (readiness probe tcp/stdout): covered by `test216` plus `supervisor.py` readiness logic.
- AC4 (Ctrl+C graceful shutdown with escalation): partially covered.
  - Current: `test217` validates shutdown semantics via supervisor helper (`shutdown_server_with_report`).
  - Gap: no integration test that sends SIGINT to `kinnoo run` process and asserts end-to-end handler path in `run_command.py`.
- AC5 (stdout/stderr real-time streaming): covered by `test218` and stream callbacks in mcp-server path.
- AC6 (trace log lifecycle metadata): covered by `test219`; lifecycle fields are present in trace payload.
- AC7 (one-shot unaffected): covered by `test220` plus full regression suite pass.
- AC8 (default readiness fallback): covered by `test221` and readiness inference behavior.

### Gaps / Inconsistencies
- Blocking gap (merge gate): AC4 integration boundary is not directly tested.
  - Why this matters: the feature promise is specifically Ctrl+C behavior during `kinnoo run`; helper-level testing alone can miss signal wiring regressions in CLI/runtime loop.
- Minor consistency issue: feature23 in `FEATURES.txt` still shows `status: not-started` while all feature23 tasks are `needs-review`.
  - Not a code blocker, but project-state metadata should be aligned during review workflow.

### Improvement Recommendations
- Add an integration test that:
  - launches `python src/kinnoo/cli.py run <mcp-agent-dir>`
  - sends SIGINT to the parent `kinnoo run` process
  - asserts SIGTERM-first then optional SIGKILL escalation behavior (via observable markers/exit metadata)
  - asserts lifecycle trace flags (`shutdown_sigterm_sent`, `shutdown_sigkill_sent`) match expected path.
- Optionally improve operator UX by printing an explicit readiness confirmation message once probe succeeds (currently behavior is implicit).

### Regression Validation
- Command executed: `python3 -m pytest`
- Result: `215 passed, 1 skipped` in `190.58s`
- Outcome: no cross-feature regression detected in current full suite.

### Merge Recommendation
- Do not merge yet.
- Required follow-up before merge:
  - add/land AC4 end-to-end SIGINT integration test for `kinnoo run` mcp-server path.
- After follow-up test passes and task status updates are aligned, feature23 is expected to be merge-ready.

## Tech Lead Review 2

### Scope Re-Check
- Focus: prior blocking review finding for feature23 AC4 integration-boundary coverage.
- Requested context updates validated:
  - SWE fix for AC4 integration test path.
  - feature23 status in `FEATURES.txt` updated to `needs-review`.

### What Was Re-Verified
- Test implementation for AC4 now targets the parent `kinnoo run` process path:
  - starts `python src/kinnoo/cli.py run <fixture>`
  - waits for readiness signal
  - sends `SIGINT` to the parent process
  - validates shutdown behavior and trace metadata.
- Manifest mapping still correctly points AC4 to:
  - `tests/test_cli.py::test_feature23_sigint_graceful_shutdown_with_escalation`

### Evidence
- Updated AC4 integration test logic inspected in `tests/test_cli.py`.
- AC4 mapping confirmed in `TESTS.txt` (`test217`).
- feature status confirmed in `FEATURES.txt` (`feature23: needs-review`).
- Targeted verification command executed:
  - `python3 -m pytest tests/test_cli.py::test_feature23_sigint_graceful_shutdown_with_escalation tests/test_regression_v1.py::test_feature23_no_regression_for_one_shot_runtime`
  - Result: `2 passed`.

### Updated AC Coverage Assessment
- AC4 is now covered end-to-end at the integration boundary.
- No remaining blocking gaps identified for feature23 AC coverage.

### Remaining Notes (Non-Blocking)
- Keep an eye on signal-path flakiness across CI platforms (timing-sensitive tests can become brittle under load); current local run is stable.

### Updated Merge Recommendation
- Prior blocker is resolved.
- Feature23 is approved from a technical review perspective, pending normal merge workflow/human approval.
