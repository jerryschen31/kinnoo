## SWE Handoff

### Scope
Implement feature34 from [FEATURES.txt](FEATURES.txt) using tasks task189-task193 from [TASKS.txt](TASKS.txt). This is the OpenClaw scaffold/template onboarding layer and must remain standalone (no full gateway orchestration).

### Feature Intent
Add `kinnoo init --framework openclaw` generation for a runnable standalone OpenClaw-style project layout, with valid OpenClaw-oriented manifest wiring and actionable setup documentation.

### Task Breakdown (Execution Order)
1. task189: Generate OpenClaw scaffold files/directories (`package.json`, `openclaw.json`, `index.mjs`, `skills/default/SKILL.md`, `memory/`, `AGENTS.md`, `SOUL.md`).
2. task190: Ensure generated `kinnoo.yaml` validates with OpenClaw + Node runtime contract.
3. task191: Ensure generated scaffold runs through `kinnoo run` when required env vars are configured.
4. task192: Add README setup guidance (Node prerequisites, dependency install path, required env vars).
5. task193: Ensure deterministic scaffold output and no dependency on external `openclaw` CLI binary.

### AC Coverage Map
- AC1 -> task189 -> test287
- AC2 -> task190 -> test288
- AC3 -> task191 -> test289
- AC4 -> task192 -> test290
- AC5 -> task193 -> test291

### Key Implementation Constraints
- Keep scaffold standalone and package-oriented; do not attempt full OpenClaw gateway bootstrap.
- Generated layout must include OpenClaw identity artifacts and default skill folder conventions.
- Manifest output must satisfy feature33 OpenClaw-targeted validation rules.
- README guidance should be concise, actionable, and aligned with existing project docs tone.
- Scaffold generation must not shell out to `openclaw` binary or require it at init-time.

### JS/TS Test Guidance
- Feature34 behavior can be fully validated with pytest integration/unit tests in this phase.
- Do not add Vitest unless a JS/TS-native behavior cannot be validated reliably from pytest.
- If Vitest becomes absolutely required, define `automation_path` as a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/templates.py
- src/kinnoo/init_command.py
- src/kinnoo/run_command.py
- tests/test_init.py
- tests/test_cli.py
- tests/test_validator.py
- tests/test_docs.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test287-test291.
- Run scaffold-focused init/run regression slices.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 scripts/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task189-task193 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
