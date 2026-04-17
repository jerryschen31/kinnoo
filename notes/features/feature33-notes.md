## SWE Handoff

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
	- python3 scripts/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task184-task188 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.

## Tech Lead Review 1

Date: 2026-03-18
Reviewer: techlead-agent
Feature: feature33 - Manifest Schema Extensions for OpenClaw/JS Agents

### Verdict
- Status: approved for merge to phase4/main
- Rationale: implementation satisfies AC1-AC5 with explicit automated coverage and full-suite regression remains green.

### Scope Reviewed
- Manifest definitions:
	- FEATURES.txt: feature33
	- TASKS.txt: task184-task188
	- TESTS.txt: test282-test286
- Implementation surfaces:
	- src/kinnoo/schema.py
	- src/kinnoo/validator.py
	- docs/manifest-schema-reference.md
	- README.md
- Test surfaces:
	- tests/test_validator.py
	- tests/test_regression_v1.py
	- tests/test_docs.py

### AC Coverage Assessment
- AC1: `runtime.package_manager` accepts `npm`/`pnpm` and rejects invalid values with clear errors.
	- test282: tests/test_validator.py::test_feature33_runtime_package_manager_validation
	- Result: covered and passing.

- AC2: optional `channels`, `skills`, `state_dirs` are type-validated and path safety checked.
	- test283: tests/test_validator.py::test_feature33_extension_fields_type_and_path_safety
	- Result: covered and passing.

- AC3: `framework: openclaw` triggers framework-targeted validation and diagnostics.
	- test284: tests/test_validator.py::test_feature33_openclaw_framework_specific_validation
	- Result: covered and passing.

- AC4: non-openclaw manifests remain optional/non-breaking with extension fields.
	- test285: tests/test_regression_v1.py::test_feature33_non_openclaw_optional_nonbreaking_regression_gate
	- Result: covered and passing.

- AC5: docs updated with OpenClaw and generic Node examples.
	- test286: tests/test_docs.py::test_feature33_manifest_extension_docs_examples
	- Result: covered and passing.

Assessment summary:
- AC mapping completeness: 5/5
- Execution evidence: 5/5 ACs have passing automated evidence

### Regression Execution
Command executed:
- python3 -m pytest

Result:
- 286 collected
- 285 passed
- 1 skipped
- 0 failed
- Runtime: 417.13s

### Findings (Ordered by Severity)
1. No merge blockers found.
- Feature33 acceptance gates and full regression are green.

2. Non-blocking workflow metadata inconsistency.
- feature33 remains `not-started` while task184-task188 are `needs-review`.
- Recommendation: advance feature33 to `needs-review` in workflow metadata during merge bookkeeping.

3. Non-blocking docs/runtime consistency improvement.
- Feature33 examples use `runtime.version: ">=20.0.0"` for Node manifests.
- Runtime preflight policy in feature31 is Node >=22, so examples can be clarified to `>=22.0.0` to avoid operator confusion.

4. Non-blocking diagnostics polish opportunity.
- Invalid OpenClaw package manager can emit both generic and framework-targeted messages.
- Recommendation: keep both for now (current behavior is actionable), or deduplicate in a future cleanup for tighter output.

### Merge Recommendation
- Approved to merge feature33 into phase4/main.
- Keep changelog merge hash placeholder until merge commit is available.
