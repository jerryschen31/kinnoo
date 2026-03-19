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

## Tech Lead Review 1

Date: 2026-03-19
Reviewer: Tech Lead Agent
Verdict: Approved for merge

### Scope Reviewed
- Feature: feature35 - Mutable State Directories in Pack/Install
- Tasks: task194, task195, task196, task197, task198
- Tests: test292, test293, test294, test295, test296

### Task and AC Validation
- task194 / AC1 (contract + validation): Pass. `state_dirs` supports string and structured entries, with path safety and exclude-shape validation in validator.
- task195 / AC1 (pack snapshot semantics): Pass. Pack stores mutable state under `state_snapshots/<declared-state-dir>/...` with deterministic layout.
- task196 / AC2 (install overwrite controls): Pass. Install restores snapshots and warns/preserves existing state by default; explicit `--state-overwrite` enables replacement.
- task197 / AC3 (exclude patterns): Pass. `state_dirs[].exclude` patterns are applied during snapshot collection; excluded files are omitted and not restored.
- task198 / AC4+AC5 (docs + regression compatibility): Pass. Docs describe mutable-vs-immutable semantics and regression gate verifies asset-only behavior remains unchanged without `state_dirs`.

### AC Coverage Assessment
- AC1: Covered by test292 and test293.
- AC2: Covered by test294.
- AC3: Covered by test295.
- AC4: Covered by test296 and docs assertions.
- AC5: Covered by test296 regression gate.

### Regression Evidence
- Full suite run executed: `python3 -m pytest`
	- Result: `1 failed, 296 passed, 1 skipped`
	- Failure: `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
	- Nested failing case in output: `tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr`
- Focused re-run executed:
	- `python3 -m pytest tests/test_cli.py::test_feature23_mcp_server_streams_stdout_stderr tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`
	- Result: `2 passed`
- Interpretation: observed failure appears flaky/timing-sensitive in legacy MCP stream assertion path and is not specific to feature35 state snapshot behavior.

### Findings, Gaps, and Improvements
- Medium: Full-suite run did not finish green in this cycle due a flaky legacy regression gate, so merge confidence relies on focused re-run plus feature35-targeted evidence.
- Low: Metadata consistency gap: feature35 in FEATURES remains `status: not-started` while tasks task194-task198 are `needs-review`.
- Low: Documentation duplication risk: Feature35 mutable snapshot guidance appears in two README sections and can drift unless consolidated.

### Merge Decision
- Approved for merge based on implementation evidence and AC coverage, with the noted flaky-test residual risk.
