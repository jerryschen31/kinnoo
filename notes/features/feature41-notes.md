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
