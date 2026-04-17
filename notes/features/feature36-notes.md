## SWE Handoff

### Scope
Implement feature36 from [FEATURES.txt](FEATURES.txt) using tasks task199-task203 from [TASKS.txt](TASKS.txt). This is the OpenClaw onboarding/import inference layer and must preserve non-OpenClaw analyzer behavior.

### Feature Intent
Extend analyzer-backed `kinnoo import` to detect existing OpenClaw projects via weighted evidence, infer runtime/package-manager/skills/state state fields, and generate actionable manifest output with warning-first guidance for unresolved fields.

### Task Breakdown (Execution Order)
1. task199: Add weighted OpenClaw detection with confidence and evidence output.
2. task200: Infer runtime language/type, package manager, skill paths, and candidate `state_dirs`.
3. task201: Recognize OpenClaw identity files (`SOUL.md`, `AGENTS.md`, optional `USER.md`) as explicit inference signals.
4. task202: Ensure generated `kinnoo.yaml` is valid when possible, or emit clear TODO/warning guidance when fields remain unresolved.
5. task203: Add regression safeguards ensuring non-OpenClaw analyzer/import behavior does not regress.

### AC Coverage Map
- AC1 -> task199 -> test297
- AC2 -> task200 -> test298
- AC3 -> task201 -> test299
- AC4 -> task202 -> test300
- AC5 -> task203 -> test301

### Key Implementation Constraints
- Use weighted evidence model (strong vs medium signals) rather than brittle single-signal detection.
- Keep import UX warning-first and operator-confirmed for mixed/ambiguous confidence.
- Align inferred manifest fields with existing feature33 and feature35 contracts.
- Preserve existing non-openclaw import flows and confidence semantics.
- Output diagnostics must be deterministic and actionable for operators.

### JS/TS Test Guidance
- Feature36 behavior is analyzer/import inference logic and can be validated in pytest.
- Do not add Vitest unless a JS/TS-native behavior cannot be asserted reliably from pytest.
- If Vitest becomes absolutely required, ensure TESTS.txt `automation_path` points to a concrete function inside a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/analyzer.py
- src/kinnoo/import_command.py
- src/kinnoo/validator.py
- tests/test_analyzer.py
- tests/test_cli_import.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test297-test301.
- Run analyzer/import regression slices for OpenClaw and non-OpenClaw fixtures.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 scripts/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task199-task203 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## Tech Lead Review 1

### Verdict
Approved for merge.

### Scope Reviewed
- Feature: feature36
- Tasks: task199, task200, task201, task202, task203
- Tests: test297, test298, test299, test300, test301

### AC Coverage Check
- AC1: PASS
	- Weighted OpenClaw detection and confidence/evidence reporting are implemented in analyzer and surfaced by import output.
	- Coverage: tests/test_analyzer.py::test_feature36_openclaw_weighted_detection_scores, tests/test_cli_import.py::test_feature36_openclaw_detection_weighted_confidence_output
- AC2: PASS
	- Import inference includes runtime language/type, package manager, skills, and candidate state_dirs for OpenClaw projects.
	- Coverage: tests/test_analyzer.py::test_feature36_openclaw_hint_inference_runtime_package_manager_skills_state_dirs, tests/test_cli_import.py::test_feature36_infers_runtime_skills_state_dirs
- AC3: PASS
	- Identity files SOUL.md and AGENTS.md are explicit signals; USER.md remains optional additive signal.
	- Coverage: tests/test_analyzer.py::test_feature36_identity_signal_detection
- AC4: PASS
	- Import flow validates generated manifest and emits deterministic TODO/warning guidance for unresolved fields.
	- Coverage: tests/test_cli_import.py::test_feature36_manifest_valid_or_todo_guidance
- AC5: PASS
	- Non-OpenClaw import behavior remains stable and protected by regression coverage.
	- Coverage: tests/test_regression_v1.py::test_feature36_non_openclaw_import_regression_guard

### Regression Evidence
- Full suite executed: `python3 -m pytest`
- Result: 304 passed, 1 skipped

### Findings
- No blocker findings.
- Follow-up process note: feature36 status in FEATURES.txt is still `not-started` while tasks are `needs-review`; update feature status during merge workflow for consistency.
