## SWE Handoff

### Scope
Implement feature35 from [FEATURES.txt](FEATURES.txt) using tasks task194-task198 from [TASKS.txt](TASKS.txt). This is the mutable state snapshot/restore layer and must preserve existing asset-only workflows.

### Feature Intent
Add first-class `state_dirs` snapshot/restore behavior for mutable runtime state (for example OpenClaw memory folders), with safe validation, selective exclusion support, overwrite controls at install time, and clear docs/regression guarantees.

### Task Breakdown (Execution Order)
1. task194: Define and validate `state_dirs` contract (including exclude policy structure and safe path rules).
2. task195: Implement pack-time state snapshot capture with deterministic archive layout.
3. task196: Implement install-time state restore with warning-first overwrite behavior and explicit force controls.
4. task197: Implement `state_dirs[].exclude` handling to omit noisy/sensitive files while preserving core state.
5. task198: Document mutable state semantics and add compatibility regression safeguards for legacy asset-only flows.

### AC Coverage Map
- AC1 -> task194/task195 -> test292/test293
- AC2 -> task196 -> test294
- AC3 -> task197 -> test295
- AC4 -> task198 -> test296
- AC5 -> task198 -> test296

### Key Implementation Constraints
- Distinguish mutable `state_dirs` semantics from immutable `assets`; do not conflate behavior.
- Preserve backward compatibility for manifests that do not declare `state_dirs`.
- Enforce path safety for state roots and keep deterministic archive/restore path mapping.
- Overwrite of existing state must be warning-first by default and only destructive with explicit operator force/overwrite control.
- Exclusion support should target practical noisy files (for example daily memory logs) without removing core warm-start state.

### JS/TS Test Guidance
- Feature35 behavior is file/manifest/pack/install contract work and can be validated in pytest.
- Do not add Vitest unless a JS/TS-native behavior becomes impossible to assert reliably via pytest.
- If Vitest is absolutely required, ensure TESTS.txt `automation_path` points to a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/pack_command.py
- src/kinnoo/archive_utils.py
- src/kinnoo/install_command.py
- src/kinnoo/cli.py
- docs/manifest-schema-reference.md
- README.md
- tests/test_validator.py
- tests/test_pack.py
- tests/test_install.py
- tests/test_docs.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test292-test296.
- Run pack/install compatibility regression slices for assets-only and state_dirs-enabled manifests.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task194-task198 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
