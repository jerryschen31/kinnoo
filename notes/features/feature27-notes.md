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
- `python3 scripts/validate_project_manifests.py` passes after any manifest edits.
- Focused analyzer tests pass, then full `python3 -m pytest` regression passes.
- Task statuses should move to `needs-review` when SWE implementation is complete.

### Suggested SWE Execution Sequence
1. Write failing tests for report contract + API (`test243`, `test249`).
2. Implement task158 minimal API until those pass.
3. Implement detector groups in order: task159 -> task160 -> task161 with corresponding tests.
4. Finish matrix/reusability gates (`test250`, `test251`) and run full regression.

## Tech Lead Review

### Findings (ordered by severity)

1. Medium: Feature/task status drift in manifests.
- `feature27` is still marked `not-started` while implementation tasks `task158`-`task162` are `needs-review`.
- Evidence:
  - `FEATURES.txt` line 1056: `status: not-started`
  - `TASKS.txt` lines 3113, 3131, 3149, 3167, 3187: `status: needs-review`
- Impact: governance metadata is inconsistent for pre-merge review flow.

2. Medium: task162 step intent includes a focused regression gate file path, but no feature27 regression gate was added to `tests/test_regression_v1.py`.
- task162 references focused regression-gate intent and lists `tests/test_regression_v1.py` in task files.
- Current regression gate file includes feature20-feature26 tests but no feature27 test entry.
- Evidence:
  - `TASKS.txt` lines 3178-3183 (task162 steps include focused regression gate language).
  - `tests/test_regression_v1.py` contains test functions up to `test_feature26_framework_template_regression_gate` at line 224, with no `test_feature27...` function.
- Impact: analyzer behavior is well-covered in `tests/test_analyzer.py`, but cross-feature regression gate convention in `tests/test_regression_v1.py` is not yet followed for feature27.

3. Low: Analyzer file discovery is broad and may include virtualenv/build trees, which can dilute inference confidence on real projects.
- `_iter_python_files(...)` currently traverses all `*.py` files recursively with no directory exclusions (for example `.venv`, `build`, cache directories).
- Evidence:
  - `src/kinnoo/analyzer.py` line 53: `_iter_python_files` uses `project_dir.rglob("*.py")` directly.
- Impact: potential false positives/performance overhead when analyzing larger repos containing dependency/vendor trees.

### AC Coverage Assessment
- AC1: Covered by `test243` (`tests/test_analyzer.py` line 20) for public API/report structure.
- AC2: Covered by `test244` (`tests/test_analyzer.py` line 70) for clear vs ambiguous entrypoint/runtime/framework detection and confidence downgrades.
- AC3: Covered by `test245` (`tests/test_analyzer.py` line 125) for requirements/pyproject dependency normalization and dedup.
- AC4: Covered by `test246` (`tests/test_analyzer.py` line 158) for `os.getenv`/`os.environ` pattern extraction and dedup.
- AC5: Covered by `test247` (`tests/test_analyzer.py` line 190) for asset candidate inference with unsafe path filtering.
- AC6: Covered by `test248` (`tests/test_analyzer.py` line 219) for service inference and health-check hint behavior.
- AC7: Covered by `test249` (`tests/test_analyzer.py` line 43) for stable inferred/confidence/warnings report sections.
- AC8: Covered by `test250` (`tests/test_analyzer.py` line 60) for non-CLI adapter/library reuse path.
- AC9: Covered by `test251` (`tests/test_analyzer.py` line 254) for detector matrix positive/ambiguous diagnostics.

### Task Review Summary
- task158: Implemented (`src/kinnoo/analyzer.py` public API/report model) with tests `test243`, `test249`, `test250`.
- task159: Implemented detector set `_detect_entrypoint`, `_detect_runtime`, `_detect_framework` with ambiguity handling (`test244`).
- task160: Implemented `_detect_dependencies` + `_detect_env_vars` (`test245`, `test246`).
- task161: Implemented `_detect_assets` + `_detect_services` (`test247`, `test248`).
- task162: AC-level detector matrix coverage implemented (`test251`), but task step intent referencing a focused regression gate in `tests/test_regression_v1.py` remains a follow-up item.

### Full Regression Result
- Command: `python3 -m pytest`
- Result: `247 passed, 1 skipped`
- Assessment: no cross-feature regressions detected.

### Recommendation Before Merge
- Implementation quality and AC coverage are strong; core feature behavior is mergeable from functional perspective.
- Complete the following pre-merge cleanup for process consistency:
  1. Align feature27 status metadata (`not-started` -> `needs-review` at minimum).
  2. Decide whether to add a dedicated feature27 regression gate in `tests/test_regression_v1.py` to match existing project convention and task162 step intent.
  3. Optionally harden analyzer traversal with directory exclusions (`.venv`, cache/build paths) and add one targeted test.

### Verdict
- Approved with minor follow-up items (non-blocking for functional correctness).
