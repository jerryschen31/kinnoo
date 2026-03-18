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
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task184-task188 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
