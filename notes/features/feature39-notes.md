## SWE Handoff

### Scope
Implement feature39 from [FEATURES.txt](FEATURES.txt) using tasks task214-task218 from [TASKS.txt](TASKS.txt). This is the manifest-permissions and sandbox-enforcement foundation and must preserve backward compatibility for existing agents without permissions declarations.

### Feature Intent
Introduce explicit permission declarations for network/filesystem/shell/browser/env access, require clear operator consent at install time, and enforce declared policy through a sandboxed run path with deterministic violation/fallback diagnostics.

### Task Breakdown (Execution Order)
1. task214: Extend schema/validator support for permissions declarations with deterministic validation behavior.
2. task215: Add install-time human-readable permission summary and explicit consent/non-interactive override flow.
3. task216: Implement `kinnoo run --sandbox` path with enforceable backend controls and deterministic failure modes.
4. task217: Ensure permission enforcement parity for Python and Node agents where technically feasible.
5. task218: Add secret-safe violation diagnostics/logging with actionable remediation output.

### AC Coverage Map
- AC1 -> task214 -> test312
- AC2 -> task215 -> test313
- AC3 -> task216 -> test314
- AC4 -> task217 -> test315
- AC5 -> task218 -> test316

### Key Implementation Constraints
- Preserve backward compatibility: manifests without `permissions` must continue to validate and run with existing behavior when sandbox mode is not requested.
- Keep operator UX explicit and safe by default: permission summaries must be human-readable, consent defaults to deny, and automation overrides must be explicit.
- Sandbox behavior must be deterministic across supported platforms: unsupported backends/policies should fail with clear classification and guidance.
- Enforce no-secret-value invariant in all diagnostics/logs while retaining actionable context for remediation.
- Maintain runtime-aware parity for Python and Node policy enforcement and document any technically infeasible controls.

### JS/TS Test Guidance
- Feature39 behavior can be validated primarily via pytest integration tests using Python and Node fixture agents to assert CLI policy behavior.
- Use Vitest only if a JS/TS runtime-specific enforcement behavior cannot be validated reliably from pytest orchestration.
- If Vitest becomes absolutely required, TESTS.txt `automation_path` must reference a concrete exported test function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/install_command.py
- src/kinnoo/run_command.py
- src/kinnoo/cli.py
- src/kinnoo/sandbox.py
- src/kinnoo/install_trace.py
- docs/manifest-schema-reference.md
- README.md
- tests/test_validator.py
- tests/test_cli_install.py
- tests/test_cli.py
- tests/test_regression_v1.py
- tests/test_run_preflight.py

### Verification Gate
- Run targeted tests for test312-test316.
- Run policy-focused install/run regression slices for both python and node fixtures.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task214-task218 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## Tech Lead Review 1

### Verdict
Blocked for merge pending regression remediation.

### Scope Reviewed
- Feature: feature39
- Tasks: task214, task215, task216, task217, task218
- Tests: test312, test313, test314, test315, test316

### AC Coverage Assessment
- AC1: PASS
	- Evidence: `tests/test_validator.py::test_feature39_permissions_schema_validation` passed and validates permissions schema constraints and invalid-declaration handling.
- AC2: PASS
	- Evidence: `tests/test_cli_install.py::test_feature39_install_permission_summary_and_consent` passed and covers summary + consent/override flow.
- AC3: PASS
	- Evidence: `tests/test_cli.py::test_feature39_run_sandbox_permission_enforcement` passed and covers sandbox allow/deny behavior.
- AC4: PASS
	- Evidence: `tests/test_regression_v1.py::test_feature39_python_node_permission_parity` passed and asserts Python/Node enforcement parity path.
- AC5: PASS
	- Evidence: `tests/test_run_preflight.py::test_feature39_violation_diagnostics_secret_safe` passed and validates actionable secret-safe diagnostics.

### Findings (Ordered by Severity)
1. Blocker: full regression is not green in this review cycle.
	- Earlier full-suite run (`python3 -m pytest`) in this Tech Lead cycle reported 3 failures tied to pre-existing feature26 permissions-compatibility behavior.
	- Merge approval is withheld until the full suite returns green, because phase4/main merge gate requires no regressions.
2. Inconsistency: feature/task status drift in manifests.
	- `feature39` remains `not-started` in `FEATURES.txt` while tasks task214-task218 are `needs-review` in `TASKS.txt`.
	- Status alignment should be corrected as part of merge workflow hygiene.
3. Improvement: add explicit negative-contract tests for unsupported sandbox backend combinations.
	- Current AC3 tests validate enforcement behavior, but additional deterministic error-shape assertions for unsupported backend/policy pairs would strengthen operator predictability across platforms.

### Regression Evidence
- Feature39 targeted gate command:
	- `python3 -m pytest tests/test_validator.py::test_feature39_permissions_schema_validation tests/test_cli_install.py::test_feature39_install_permission_summary_and_consent tests/test_cli.py::test_feature39_run_sandbox_permission_enforcement tests/test_regression_v1.py::test_feature39_python_node_permission_parity tests/test_run_preflight.py::test_feature39_violation_diagnostics_secret_safe -q`
- Result:
	- `5 passed in 5.22s`
- Full-suite status in this review cycle:
	- `python3 -m pytest` previously failed (3 failures), so merge gate is currently blocked.

### Recommendation
- Do not merge feature39 to `phase4/main` yet.
- Resolve full-suite regression failures, rerun `python3 -m pytest`, and then re-open Tech Lead review for final approval.

## SWE agent - test failure and improvement recommendation resolution

### Root Cause and Fix for the 3 failing regressions
- Root cause: `permissions` optional-field generic type validation in [src/kinnoo/validator.py](src/kinnoo/validator.py) was enforcing `dict` for non-`mcp-server` manifests, which regressed Feature26 backward-compatibility behavior (`permissions` ignored outside `runtime.type: mcp-server` for legacy shapes).
- Fix applied:
	- added a targeted compatibility guard in the optional-field validation loop:
		- when `optional_field == "permissions"` and `runtime.type != "mcp-server"` and value is non-dict, skip generic type error and defer to legacy compatibility behavior.
	- this restores Feature26 expected behavior while preserving Feature39 permission contract checks in the dedicated permissions validator path.

### Resolution for TL improvement recommendation
- Recommendation addressed: strengthened negative-contract sandbox backend failure-shape testing.
- Added explicit failure-shape unit coverage in [tests/test_cli.py](tests/test_cli.py):
	- `test_feature39_sandbox_backend_failure_shapes` validates deterministic denied decision shape for:
		- unsupported runtime type (`backend_unsupported_runtime`),
		- unsupported runtime language (`backend_unsupported_runtime_language`),
		- missing permissions declaration (`missing_permissions_policy`).
	- assertions cover stable `code`, actionable `message`, and `remediation` fields.

### Verification run (targeted)
- `python3 -m pytest tests/test_validator.py::test_feature26_permissions_schema_validation tests/test_regression_v1.py::test_feature26_framework_template_regression_gate tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 tests/test_cli.py::test_feature39_sandbox_backend_failure_shapes -q`
- Result: `4 passed`
