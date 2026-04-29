## SWE Handoff

### Scope
Implement feature37 from [FEATURES.txt](FEATURES.txt) using tasks task204-task208 from [TASKS.txt](TASKS.txt). This is the Node install security hardening layer and must keep Python install flows unchanged.

### Feature Intent
Add Node.js dependency risk checks and lifecycle-script controls to install workflows with configurable policy gates suitable for local development and stricter CI/publisher environments.

### Task Breakdown (Execution Order)
1. task204: Add Node install dependency audit execution and deterministic severity summary output.
2. task205: Enforce default block on critical vulnerabilities with explicit `--allow-vulnerable` override.
3. task206: Detect lifecycle scripts, warn operators, and support `--ignore-scripts` install mode.
4. task207: Persist audit findings and operator/policy decisions in machine-readable install trace artifacts.
5. task208: Add regression safeguards proving Python install behavior is unaffected.

### AC Coverage Map
- AC1 -> task204 -> test302
- AC2 -> task205 -> test303
- AC3 -> task206 -> test304
- AC4 -> task207 -> test305
- AC5 -> task208 -> test306

### Key Implementation Constraints
- Keep behavior runtime-aware: Node-specific audit/script controls must not run for Python agents.
- Surface security posture clearly: deterministic severity output and warning-first script visibility.
- Default policy should be safe (block critical vulnerabilities) while preserving explicit override controls.
- Ensure install trace data is machine-readable, deterministic, and free of secret values.
- Keep package-manager command behavior explicit (`npm audit`/equivalent and script policy propagation).

### JS/TS Test Guidance
- Feature37 behavior can be validated through Python pytest integration tests by asserting CLI behavior, subprocess invocation, and trace outputs.
- Do not add Vitest unless a JS/TS-native behavior cannot be validated reliably from pytest.
- If Vitest becomes absolutely required, ensure TESTS.txt `automation_path` references a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/install_command.py
- src/kinnoo/cli.py
- src/kinnoo/install_trace.py
- tests/test_cli_install.py
- tests/test_regression_v1.py
- docs/manifest-schema-reference.md
- README.md

### Verification Gate
- Run targeted tests for test302-test306.
- Run install-focused regression slices for node and python fixtures.
- Run full regression before handoff completion:
        - python3 -m pytest
- Validate manifests after task/test updates:
        - python3 scripts/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task204-task208 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## Tech Lead Review 1

### Verdict
Not approved for merge (blocking test inconsistency and failing full regression).

### Scope Reviewed
- Feature: feature37
- Tasks: task204, task205, task206, task207, task208
- Tests: test302, test303, test304, test305, test306

### AC Coverage Assessment
- AC1: Implemented and covered
        - Evidence: Node install runs audit summary output in install flow and is asserted in feature37 tests.
- AC2: Implemented and covered, but test contract conflict exists
        - Evidence: install blocks by default on critical findings and supports `--allow-vulnerable` override.
- AC3: Implemented and covered
        - Evidence: lifecycle scripts detected/warned and `--ignore-scripts` propagated.
- AC4: Implemented and covered
        - Evidence: machine-readable install trace includes severity counts and decision metadata.
- AC5: Implemented and covered
        - Evidence: python no-op regression guard verifies no node audit/script controls run for python installs.

### Findings (Ordered by Severity)
1. Blocker: feature37 regression suite is red due to internal test expectation mismatch.
         - `tests/test_cli_install.py::test_feature37_node_audit_severity_summary` expects install success while fixture audit output includes `critical=1`.
         - Current implementation correctly enforces AC2 and blocks default installs with critical findings.
         - This failure cascades to `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`.
         - Impact: cannot approve feature37 merge while full regression fails.

2. Improvement: AC1 test would be stronger with an explicit non-critical severity fixture.
         - Current summary test asserts output shape but uses a critical fixture that now intersects AC2 block behavior.
         - Recommended follow-up: keep one AC1 test with `critical=0` and move critical-path assertions to AC2-only tests.

### Regression Evidence
- Full suite: `python3 -m pytest`
- Result: `2 failed, 307 passed, 1 skipped`
- Focused rerun: `python3 -m pytest tests/test_cli_install.py::test_feature37_node_audit_severity_summary tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`
- Result: `2 failed` (deterministic, non-flaky)

### Required Remediation Before Approval
- Align `test_feature37_node_audit_severity_summary` expectations with AC2 default-block semantics, or use a non-critical audit fixture for AC1-only validation.
- Re-run full regression and return tasks to Tech Lead review after green suite.

## SWE agent - test failure resolution

### Root Cause
- `test_feature37_node_audit_severity_summary` used a fixture that reported `critical=1` and expected successful install.
- After feature37 AC2 enforcement, default install behavior blocks on critical vulnerabilities unless `--allow-vulnerable` is set.
- This created a direct conflict between AC1 summary-output validation and AC2 default-block policy.

### Code/Test Change Applied
- Updated the node install invocation in `tests/test_cli_install.py::test_feature37_node_audit_severity_summary` to include `--allow-vulnerable`.
- This preserves AC1 intent (severity summary visibility) while explicitly opting into AC2 override behavior for that scenario.

### Verification
- Focused rerun:
        - `python3 -m pytest tests/test_cli_install.py::test_feature37_node_audit_severity_summary tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`
        - Result: `2 passed`
- Full regression:
        - `python3 -m pytest`
        - Result: `309 passed, 1 skipped`
