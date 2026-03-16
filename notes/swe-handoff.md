## Feature27 SWE Handoff - Project Analyzer Module (task158-task162)

### Scope
Implement feature27 by delivering a reusable analyzer library in `src/kinnoo/analyzer.py` that infers manifest-relevant metadata from existing projects and returns a structured report for future `kinnoo import` workflows.

### Scope Tightening (Important)
- Implement analyzer as a pure library module only. Do not add CLI commands, interactive prompts, or file-writing behavior.
- Keep detection heuristics deterministic and stdlib-only.
- Use confidence-based outputs for uncertainty; avoid raising errors for ambiguous detection unless inputs are invalid (e.g., missing project path).
- Keep V1 heuristic coverage intentionally narrow and explicit; avoid broad fuzzy matching that causes unstable tests.

### Task Order and Grouping
Single SWE agent can implement all tasks in one sequence because they are tightly coupled and build on shared analyzer internals.

1. `task158` - Analyzer core API and report model
2. `task159` - Entrypoint/runtime/framework detectors
3. `task160` - Dependencies/env var detectors
4. `task161` - Assets/services detectors
5. `task162` - Analyzer matrix tests and reusability gate

### Dependencies
- `task159` depends on `task158`
- `task160` depends on `task158`
- `task161` depends on `task158`
- `task162` depends on `task159`, `task160`, `task161`

### Design Constraints
- Keep detector functions independent and composable.
- Use stdlib-first parsing (`ast`, `pathlib`, `re`, `tomllib`) and avoid heavy dependencies.
- Do not couple analyzer logic to CLI behavior; analyzer must be importable/reusable as a library path.
- Return confidence and evidence/diagnostic metadata instead of hard-failing on ambiguous inputs.

### Report Contract (V1)
`analyze_project(project_dir)` should return a single structured report with these stable sections:
1. `inferred`:
	- Manifest-shaped inferred fields (entrypoint, runtime, framework, dependencies, env_vars, assets, services).
2. `confidence`:
	- Per-field confidence and concise evidence strings.
3. `warnings`:
	- Actionable todo/gap messages for unresolved or low-confidence fields.

Notes:
- Keep field names stable for tests.
- Empty sections are allowed but keys must always exist.

### Files Expected to Change
- `src/kinnoo/analyzer.py`
- `tests/test_analyzer.py`
- `tests/test_regression_v1.py` (only if needed for focused feature27 regression gate wiring)

### Per-Task Deliverables
1. `task158`:
	- Create module, public API, and report schema.
	- Add detector orchestration skeleton (detectors may be stubs initially).
2. `task159`:
	- Implement `_detect_entrypoint`, `_detect_runtime`, `_detect_framework`.
	- Include explicit uncertainty paths (confidence downgrade + warning).
3. `task160`:
	- Implement `_detect_dependencies` from `requirements.txt` + `pyproject.toml`.
	- Implement `_detect_env_vars` for `os.getenv`, `os.environ[...]`, and `.get()` access forms.
4. `task161`:
	- Implement `_detect_assets` for common artifact extensions and directories with path-safety filtering.
	- Implement `_detect_services` from recognizable endpoint patterns and optional health-check hints.
5. `task162`:
	- Add analyzer matrix tests (positive + ambiguous) across all detectors.
	- Add focused reusability gate proving analyzer can be called by a non-CLI adapter path.

### Out of Scope (Feature27)
- No `kinnoo import` command implementation.
- No manifest writing/generation.
- No new dependencies beyond stdlib.
- No network calls or live service probing.
- No runtime execution side effects in analyzer.

### Test Plan (from TESTS.txt)
- `test243`: analyzer public API and detector hooks (AC1)
- `test244`: entrypoint/runtime/framework uncertainty handling (AC2)
- `test245`: requirements + pyproject dependency normalization (AC3)
- `test246`: env var pattern detection and deduplication (AC4)
- `test247`: asset candidate inference with path-safety filtering (AC5)
- `test248`: service inference with health-check hints (AC6)
- `test249`: report sections contract: inferred/confidence/warnings (AC7)
- `test250`: feature19-style reusability path without logic duplication (AC8)
- `test251`: detector matrix positive/ambiguous coverage with diagnostics (AC9)

### Execution Notes for SWE
- Build fixture-based tests first to lock expected report contract.
- Implement detectors incrementally and keep each detector unit-testable in isolation.
- Ensure warning text is actionable (what was missing, why confidence dropped, what to check).
- Keep behavior deterministic where possible for stable tests.
- Use small in-repo fixtures under tests to avoid brittle filesystem assumptions.
- Prefer explicit parser helpers per detector over one large monolithic scanner.
- Keep detector failure modes visible in warnings; do not suppress exceptions silently.

### Definition of Done
- All ACs for feature27 are mapped to passing automated tests (`test243`-`test251`).
- `python3 src/validate_project_manifests.py` passes after any manifest edits.
- Focused analyzer tests pass, then full `python3 -m pytest` regression passes.
- Task statuses should move to `needs-review` when SWE implementation is complete.

### Suggested SWE Execution Sequence
1. Write failing tests for report contract + API (`test243`, `test249`).
2. Implement task158 minimal API until those pass.
3. Implement detector groups in order: task159 -> task160 -> task161 with corresponding tests.
4. Finish matrix/reusability gates (`test250`, `test251`) and run full regression.
