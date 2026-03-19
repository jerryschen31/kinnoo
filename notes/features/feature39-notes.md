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
