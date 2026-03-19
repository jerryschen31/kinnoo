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
        - python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task204-task208 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
