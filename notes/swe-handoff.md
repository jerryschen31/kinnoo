## SWE Handoff: feature32 - Daemon Runtime Type + Process Controls

### Scope
Implement feature32 from [FEATURES.txt](FEATURES.txt) using tasks task178-task183 from [TASKS.txt](TASKS.txt). This is the daemon lifecycle/control-plane layer for Phase 4 and must preserve existing one-shot and mcp-server behavior.

### Feature Intent
Add generic daemon runtime support with operator lifecycle controls (`run` start semantics, `stop`, `attach`, `logs`) and supervisor/health diagnostics for Python and Node.js agents.

### Task Breakdown (Execution Order)
1. task178: Schema + validator support for `runtime.type: daemon`.
2. task179: Daemon start path in `kinnoo run` + persisted PID/state metadata.
3. task180: `kinnoo stop <agent>` graceful shutdown + deterministic fallback behavior.
4. task181: `kinnoo attach <agent>` interactive attach controls for supported daemon sessions.
5. task182: `kinnoo logs <agent>` tail/follow command with source/timestamp context.
6. task183: Supervisor/health integration and regression gate for daemon lifecycle states.

### AC Coverage Map
- AC1 -> task178 -> test276
- AC2 -> task179 -> test277
- AC3 -> task180 -> test278
- AC4 -> task181 -> test279
- AC5 -> task182 -> test280
- AC6 -> task183 -> test281

### Key Implementation Constraints
- This feature is daemon lifecycle support, not full OpenClaw gateway orchestration.
- Reuse existing [src/kinnoo/supervisor.py](src/kinnoo/supervisor.py) and [src/kinnoo/health_check.py](src/kinnoo/health_check.py) architecture where possible.
- Preserve backward compatibility for existing runtime modes (`one-shot`, `mcp-server`) and existing CLI flows.
- Keep operator diagnostics deterministic and actionable; never leak secret values.
- Daemon state file layout and log metadata format should be stable and testable.

### JS/TS Test Guidance
- No feature32 behavior requires mandatory JavaScript-native test execution at this stage; pytest integration tests can validate daemon lifecycle contracts for both Python and Node.js fixtures.
- If a JS-native control-surface behavior becomes unavoidable during implementation, use Vitest and record automation_path as a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/cli.py
- src/kinnoo/run_command.py
- src/kinnoo/supervisor.py
- src/kinnoo/health_check.py
- tests/test_validator.py
- tests/test_cli.py
- tests/test_run_preflight.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test276-test281.
- Run daemon-focused regression slices for python + node compatibility paths.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task178-task183 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## SWE Handoff: feature33 - Manifest Schema Extensions for OpenClaw/JS Agents

### Scope
Implement feature33 from [FEATURES.txt](FEATURES.txt) using tasks task184-task188 from [TASKS.txt](TASKS.txt). This is the manifest contract layer for OpenClaw-oriented and generic JS/TS agents and must stay backward-compatible for existing manifests.

### Feature Intent
Extend manifest schema/validation to support `runtime.package_manager`, `channels`, `skills`, and `state_dirs`, add framework-targeted validation behavior for `framework: openclaw`, and document the contract with clear examples.

### Task Breakdown (Execution Order)
1. task184: Add schema + validator support for `runtime.package_manager` with allowed values (`npm`, `pnpm`).
2. task185: Add optional `channels`, `skills`, and `state_dirs` schema handling with strict type/path validation.
3. task186: Add framework-targeted validation behavior and diagnostics for `framework: openclaw`.
4. task187: Add non-openclaw compatibility guards proving new fields are optional/non-breaking.
5. task188: Update manifest documentation with OpenClaw and generic Node.js examples.

### AC Coverage Map
- AC1 -> task184 -> test282
- AC2 -> task185 -> test283
- AC3 -> task186 -> test284
- AC4 -> task187 -> test285
- AC5 -> task188 -> test286

### Key Implementation Constraints
- Keep schema extensions framework-agnostic and reusable for non-OpenClaw JS/TS frameworks.
- Preserve existing validation behavior for manifests that do not use the new fields.
- Path safety checks must reject unsafe absolute/traversal paths for `skills` and `state_dirs` entries.
- OpenClaw-specific validation must be gated behind `framework: openclaw` and return framework-targeted diagnostics.
- Ensure docs clearly distinguish optional behavior for non-openclaw manifests.

### JS/TS Test Guidance
- This feature is schema/validator/docs work; pytest tests are sufficient for contract validation in this phase.
- Do not add Vitest by default.
- If a JS/TS-native parser/runtime behavior becomes absolutely required, use Vitest and record `automation_path` as a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- docs/manifest-schema-reference.md
- README.md
- tests/test_validator.py
- tests/test_regression_v1.py
- tests/test_docs.py

### Verification Gate
- Run targeted tests for test282-test286.
- Run focused validator/docs regression slices.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task184-task188 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## SWE Handoff: feature34 - OpenClaw Scaffold Template

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
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task189-task193 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
