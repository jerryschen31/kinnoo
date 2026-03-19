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

## SWE Handoff: feature35 - Mutable State Directories in Pack/Install

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

## SWE Handoff: feature36 - OpenClaw Import Detection & Manifest Inference

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

## SWE Handoff: feature37 - Node.js Dependency Audit & Lifecycle Script Controls

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
