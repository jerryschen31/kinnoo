## SWE Handoff

### Scope
Implement feature38 from [FEATURES.txt](FEATURES.txt) using tasks task209-task213 from [TASKS.txt](TASKS.txt). This is the JS/TS security sweep expansion and must preserve existing sweep output conventions and no-secret-value guarantees.

### Feature Intent
Extend static security sweep coverage to JavaScript/TypeScript and JSON artifacts so kinnoo can flag credential exposure risks, dangerous execution/configuration patterns, and risky memory snapshot content in warning-first mode.

### Task Breakdown (Execution Order)
1. task209: Add JS/TS/JSON credential and token scanning coverage.
2. task210: Add risky JS/TS execution primitive detection with file/line evidence.
3. task211: Add dangerous OpenClaw JSON configuration detection and targeted warnings.
4. task212: Add memory snapshot candidate scanning before pack with warning-first findings.
5. task213: Add output contract and no-secret regression safeguards for mixed-language sweep paths.

### AC Coverage Map
- AC1 -> task209 -> test307
- AC2 -> task210 -> test308
- AC3 -> task211 -> test309
- AC4 -> task212 -> test310
- AC5 -> task213 -> test311

### Key Implementation Constraints
- Preserve warning-first posture (non-blocking) for local workflows while surfacing actionable security findings.
- Emit deterministic file/line evidence for risky primitive/config findings wherever available.
- Preserve no-secret-value invariant in all sweep outputs; redact values and report patterns/locations only.
- Keep output shape consistent with existing sweep UX to avoid breaking operator automation and regression baselines.
- Ensure feature38 logic applies to JS/TS/JSON additions without regressing existing Python sweep behavior.

### JS/TS Test Guidance
- Feature38 behavior can be validated in pytest by creating fixture files and asserting sweep output/findings.
- Do not add Vitest unless a JS/TS-native runtime behavior cannot be validated reliably via pytest file-based fixtures.
- If Vitest becomes absolutely required, ensure TESTS.txt `automation_path` points to a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/code_sweep.py
- src/kinnoo/pack_command.py
- tests/test_trust_baseline.py
- tests/test_pack_robustness.py
- tests/test_regression_v1.py
- docs/manifest-schema-reference.md
- README.md

### Verification Gate
- Run targeted tests for test307-test311.
- Run security sweep regression slices across python and js/ts/json fixtures.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task209-task213 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
