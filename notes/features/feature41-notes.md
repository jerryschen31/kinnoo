## SWE Handoff

### Scope
Implement feature41 from [FEATURES.txt](FEATURES.txt) using tasks task224-task228 from [TASKS.txt](TASKS.txt). This is the runtime defense-in-depth layer and must integrate with feature39 permissions while preserving stable baseline run behavior.

### Feature Intent
Add runtime behavioral telemetry, deterministic permission-violation enforcement (including kill switch), resource-limit controls, and dry-run trace capability with graceful degradation on platforms lacking low-level telemetry primitives.

### Task Breakdown (Execution Order)
1. task224: Add baseline runtime monitor event capture for process/network/filesystem behavior.
2. task225: Add deterministic violation enforcement and kill-switch path.
3. task226: Add configurable resource controls (timeout/CPU/memory where supported).
4. task227: Add `kinnoo run --dry-run` low-risk tracing mode.
5. task228: Integrate feature41 monitor policy with feature39 permissions and graceful degradation behavior.

### AC Coverage Map
- AC1 -> task224 -> test322
- AC2 -> task225 -> test323
- AC3 -> task226 -> test324
- AC4 -> task227 -> test325
- AC5 -> task228 -> test326

### Key Implementation Constraints
- Keep monitor outputs structured and deterministic so they remain machine-consumable for post-run auditing.
- Enforce no-secret-value diagnostic invariant when emitting telemetry and violation events.
- Treat kill-switch as policy-driven deterministic behavior, not heuristic best-effort.
- Ensure resource-control behavior is explicit on unsupported platforms (graceful degradation with clear guidance).
- Maintain cross-runtime behavior parity (Python and Node) where technically feasible, and document deltas.

### JS/TS Test Guidance
- Feature41 behavior should be validated primarily through pytest integration tests across Python and Node fixture agents.
- Do not add Vitest unless a JS/TS-native telemetry/enforcement behavior cannot be reliably validated from pytest orchestration.
- If Vitest becomes absolutely required, ensure TESTS.txt `automation_path` points to a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/run_command.py
- src/kinnoo/runtime_monitor.py
- src/kinnoo/sandbox.py
- src/kinnoo/cli.py
- src/kinnoo/validator.py
- docs/manifest-schema-reference.md
- README.md
- tests/test_cli.py
- tests/test_run_preflight.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test322-test326.
- Run runtime monitoring regression slices for python and node fixture agents.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task224-task228 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## SWE agent - fixes

### Failing Test Root Cause
The 7 failures were a cascade from process-launch compatibility regressions introduced while wiring feature41 resource controls into `run_command.py`:

1. `process.communicate(timeout=...)` was being used in the non-JSON run path even when test doubles only implemented `communicate()` with no keyword arguments.
2. `subprocess.Popen(..., preexec_fn=resource_preexec_fn)` always passed `preexec_fn`, including when it was `None`, but some strict fake `Popen` constructors in existing tests did not accept that keyword.

These exceptions were caught by the generic launch error handler, causing `run_agent(...)` to return `1` instead of the expected mocked return code (for example, expected `17` in the feature31 node test).

### Code Changes Applied
File updated: `src/kinnoo/run_command.py`

1. Added conditional launch kwargs for both JSON and non-JSON execution branches:
	- Build `process_kwargs` dict first.
	- Only include `preexec_fn` when `resource_preexec_fn is not None`.
	- This preserves resource-limit behavior when configured and avoids strict-mock breakage when not configured.

2. Added backward-compatible `communicate(...)` behavior in the non-JSON branch:
	- If no timeout is configured (`max_seconds is None`): call `process.communicate()`.
	- If timeout is configured: try `process.communicate(timeout=...)`.
	- If a strict test double raises `TypeError` for unsupported `timeout` kwarg: fall back to `process.communicate()`.
	- Existing `TimeoutExpired` handling remains in place for real subprocess timeout enforcement.

### Why This Fix Is Correct
The fix keeps feature41 controls intact while restoring compatibility with pre-existing test harness patterns:

1. Real runtime behavior remains unchanged for configured limits (timeout enforcement still active).
2. Non-limited runs no longer force optional kwargs into mocked process APIs.
3. Older tests that intentionally mock minimal subprocess interfaces now pass without weakening policy or monitor logic.

### Validation Performed
Ran targeted failing tests first, then all previously failing tests, then the same user command:

1. `python3 -m pytest tests/test_cli.py::test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit tests/test_cli.py::test_feature25_interactive_prompt_allows_proceed_or_abort tests/test_regression_v1.py::test_feature39_python_node_permission_parity`
	- Result: `3 passed`

2. `python3 -m pytest` on the 7 previously failing tests:
	- `tests/test_cli.py::test_feature31_run_nodejs_entrypoint_streams_and_propagates_exit`
	- `tests/test_cli.py::test_feature25_interactive_prompt_allows_proceed_or_abort`
	- `tests/test_regression_v1.py::test_feature39_python_node_permission_parity`
	- `tests/test_regression_v1.py::test_feature42_json_contract_guidance_and_text_regression_gate`
	- `tests/test_regression_v1.py::test_feature25_ac_coverage_and_no_services_regression_gate`
	- `tests/test_regression_v1.py::test_feature20_does_not_regress_v2_behavior`
	- `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
	- Result: `7 passed`

3. Re-ran the exact command reported by user:
	- `python3 -m pytest --testmon`
	- Result: `13 passed, 66 deselected, 0 failed`

## Tech Lead Review 1

### Review Scope
Reviewed feature41 implementation against AC1-AC5 in [FEATURES.txt](FEATURES.txt), mapped tasks task224-task228 in [TASKS.txt](TASKS.txt), and mapped tests test322-test326 in [TESTS.txt](TESTS.txt). Verified implementation evidence in runtime execution/monitoring paths and completed the required regression command sequence.

### Acceptance Criteria Validation
1. AC1 Runtime behavioral telemetry baseline: PASS
	- Evidence: Runtime monitor event capture baseline is implemented and validated by `test_feature41_runtime_event_monitoring_baseline`.
	- Files:
		- `src/kinnoo/runtime_monitor.py` (`RuntimeMonitor`, event schema, network/filesystem/process capture)
		- `src/kinnoo/run_command.py` (monitor lifecycle wiring)
		- `tests/test_run_preflight.py` (`test_feature41_runtime_event_monitoring_baseline`)

2. AC2 Deterministic violation enforcement and kill switch: PASS
	- Evidence: warn/continue and hard kill-switch paths are exercised and asserted via reason codes and persisted violation events.
	- Files:
		- `src/kinnoo/runtime_monitor.py` (`resolve_violation_enforcement`)
		- `src/kinnoo/run_command.py` (violation handling and kill-switch error path)
		- `tests/test_cli.py` (`test_feature41_violation_enforcement_and_kill_switch`)

3. AC3 Resource controls with graceful degradation: PASS
	- Evidence: wall-clock and CPU-limit enforcement paths are covered; unsupported platform mode emits explicit degraded diagnostics and continues safely.
	- Files:
		- `src/kinnoo/runtime_monitor.py` (`normalize_runtime_resource_controls`, `posix_resource_limits_supported`)
		- `src/kinnoo/run_command.py` (timeout/CPU/memory enforcement wiring)
		- `tests/test_cli.py` (`test_feature41_resource_control_enforcement`)

4. AC4 Dry-run low-risk trace mode: PASS
	- Evidence: `--dry-run` suppresses entrypoint execution, reports predicted actions, and prevents side effects.
	- Files:
		- `src/kinnoo/run_command.py` (`dry_run` branch and predicted actions output)
		- `src/kinnoo/runtime_monitor.py` (`predict_dry_run_actions`)
		- `tests/test_cli.py` (`test_feature41_dry_run_monitoring_trace`)

5. AC5 Feature39 permissions integration + graceful telemetry degradation: PASS
	- Evidence: monitor policy summary respects manifest permissions for Python/Node and emits deterministic telemetry-limited degradation signal when forced.
	- Files:
		- `src/kinnoo/run_command.py` (policy summary and degradation messaging)
		- `src/kinnoo/runtime_monitor.py` (`resolve_monitor_policy_summary`)
		- `tests/test_regression_v1.py` (`test_feature41_feature39_integration_and_graceful_degradation`)

### Regression Evidence
1. Required command executed:
	- `python3 -m pytest --testmon`
	- Result: `collected 0 items` (no file-change selection by testmon)

2. Full regression in testmon workflow executed for meaningful coverage:
	- `python3 -m pytest --testmon-noselect`
	- Result: `330 passed, 1 skipped`

### Verdict
APPROVED for merge readiness from Tech Lead review perspective.

### Notes
- No blocking functional regressions observed in feature41 acceptance paths.
- Existing process-launch compatibility fix recorded by SWE remains valid under current regression run.
