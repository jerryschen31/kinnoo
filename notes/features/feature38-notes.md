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
	- python3 scripts/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task209-task213 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## Tech Lead Review 1

### Verdict
Approved for merge.

### Scope Reviewed
- Feature: feature38
- Tasks: task209, task210, task211, task212, task213
- Tests: test307, test308, test309, test310, test311

### AC Coverage Assessment
- AC1: PASS
	- Coverage evidence: JS/TS/JSON credential scan coverage and redaction assertions validated in `tests/test_trust_baseline.py::test_feature38_scans_jstsjson_credentials`.
- AC2: PASS
	- Coverage evidence: risky execution primitive findings with file/line evidence validated in `tests/test_trust_baseline.py::test_feature38_flags_risky_js_execution_primitives_with_file_line`.
- AC3: PASS
	- Coverage evidence: dangerous OpenClaw config detection plus safe-config negative check validated in `tests/test_trust_baseline.py::test_feature38_openclaw_config_dangerous_settings_warning`.
- AC4: PASS
	- Coverage evidence: memory snapshot credential-risk warning-first behavior validated in `tests/test_pack_robustness.py::test_feature38_memory_snapshot_credential_warning_first`.
- AC5: PASS
	- Coverage evidence: stable output contract and no-secret-value regression guard validated in `tests/test_regression_v1.py::test_feature38_output_format_and_secret_safety_regression_guard`.

### Findings
1. No blocker findings.
2. Improvement opportunity: OpenClaw dangerous-config detection currently relies on filename/content candidacy heuristics for JSON targeting; consider a follow-up enhancement to support optional explicit config path declarations for teams with custom naming conventions.
3. Process inconsistency: feature38 remains `not-started` in FEATURES while tasks are `needs-review`; align status transitions during merge workflow for manifest consistency.

### Regression Evidence
- Full suite: `python3 -m pytest`
- Result: `314 passed, 1 skipped`

### Recommendation
- Merge-ready. Proceed with merge workflow and post-merge commit hash backfill in changelog.
