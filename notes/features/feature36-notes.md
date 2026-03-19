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
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task199-task203 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
