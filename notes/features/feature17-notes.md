# Feature17 SWE Handoff — Pack Size Reporting & Warnings

## Scope
Implement feature17 through tasks `task112` to `task115`. Goal: improve package footprint visibility by reporting archive size at pack time, warning on large artifacts, and surfacing size in inspect/list.

## Task execution order and dependencies

### Group 1 — Pack size foundation
1. `task112` — Pack archive size reporting + >100MB warning

### Group 2 — Consumer visibility
2. `task113` — Inspect displays archive size metadata
3. `task114` — List includes archive size in local and remote modes

### Group 3 — Docs and regression
4. `task115` — Docs + docs regression coverage for feature17

Recommended order: `task112` -> (`task113`, `task114`) -> `task115`.

## Tests to implement (already declared)
- `task112` -> `test144`, `test145`
- `task113` -> `test146`
- `task114` -> `test147`
- `task115` -> `test148`

## AC coverage mapping
- `AC1`: `test144`
- `AC2`: `test145`
- `AC3`: `test146`
- `AC4`: `test147`

## Design constraints

### Size formatting and consistency
- Use one shared formatting function for human-readable sizes across pack/inspect/list.
- Keep unit labels stable (B, KB, MB, GB) and deterministic decimal formatting.

### Large archive warning contract
- Warning condition: final archive size strictly greater than 100 MB.
- Warning message contract:
  - `Warning: archive is large (X MB). Consider whether all dependencies are necessary.`

### Testability requirement for >100MB branch
- Do not force CI to generate true 100+ MB archives for normal test runs.
- Add a test-only threshold override path (for example env var `KINNOO_PACK_WARN_THRESHOLD_MB`) so integration tests can validate warning logic with small fixtures.
- Keep production default threshold at 100 MB.

## How to test the >100MB warning (requested detail)

Use this two-layer strategy:

1. **Branch-validation integration test (primary):**
	- Set threshold override to `1` MB.
	- Create archive fixture with incompressible payload slightly above 1 MB.
	- Run `kinnoo pack` and assert warning is printed.
	- This validates real command behavior without heavy test artifacts.

2. **Optional true-threshold smoke test (non-default / manual):**
	- Build a larger fixture >100 MB (incompressible bytes), run pack, verify warning.
	- Keep out of default CI due to runtime/storage cost.

This gives high confidence in warning behavior while keeping test suite fast and reliable.

## Files expected to change
- `src/kinnoo/pack_command.py`
- `src/kinnoo/inspect_command.py`
- `src/kinnoo/list_command.py`
- `src/kinnoo/archive.py`
- `src/kinnoo/registry_backends.py`
- `tests/test_pack_size_reporting.py` (new)
- `tests/test_docs.py`
- `README.md`
- `docs/manifest-schema-reference.md`

## Per-Task Handoff Notes

### task112 — Pack archive size reporting and large-archive warning
**Objective**
- Print final archive size after pack and emit warning when size exceeds 100 MB.

**Implementation notes**
- Compute size from the final stored archive path, not temp staging path.
- Add threshold override hook for tests while preserving 100 MB default.
- Ensure message text exactly matches AC contract for warning.

**Definition of done**
- `test144`, `test145` pass.

### task113 — Inspect displays archive size metadata
**Objective**
- Show archive size in `kinnoo inspect <archive.kno>` output.

**Implementation notes**
- Add additive metadata line (no breaking output changes).
- Reuse shared size formatter to avoid drift.

**Definition of done**
- `test146` passes.

### task114 — List output includes archive size
**Objective**
- Include archive size for local and remote list modes.

**Implementation notes**
- Extend list row model to carry size metadata.
- Maintain existing list behavior while adding size field/column.

**Definition of done**
- `test147` passes.

### task115 — Docs and regression coverage for feature17
**Objective**
- Document size reporting/warning behavior and lock it with docs tests.

**Implementation notes**
- Document pack output line + >100 MB warning semantics.
- Document inspect/list size visibility.
- Add docs assertion test for feature17.

**Definition of done**
- `test148` passes.

## SWE completion checklist
- [ ] Implement tasks `task112`..`task115` in order.
- [ ] Implement tests `test144`..`test148`.
- [ ] Run focused tests: `python3 -m pytest tests/test_pack_size_reporting.py tests/test_docs.py -q`.
- [ ] Run manifest validator: `python3 src/validate_project_manifests.py`.
- [ ] Move task statuses to `in-progress` then `needs-review` when complete.

## TechLead Addendum: Full-Suite Failures To Address Before Merge

Date captured: 2026-03-12
Command: `python3 -m pytest`
Result: `18 failed, 122 passed, 1 skipped`

Feature17-focused tests are green, but these full-suite failures are currently blocking merge confidence.

### Failure cluster A: install flow now halts on unverified-source prompt in non-interactive tests

Observed stderr/stdout pattern in multiple failures:
- `No checksum file found — archive integrity not verified`
- `This agent is from an unverified source.`
- `Install aborted by user.`

Likely issue:
- Tests invoking `kinnoo install` non-interactively do not provide confirmation input and are now exiting before the rest of install assertions run.

Affected tests:
- `tests/test_cli_install_extract.py::test_install_extracts_archive`
- `tests/test_cli_install_invalid.py::test_install_invalid_archive_or_missing_files[invalid_zip]`
- `tests/test_cli_install_invalid.py::test_install_invalid_archive_or_missing_files[missing_kinnoo_yaml]`
- `tests/test_cli_install_manifest.py::test_install_aborts_on_invalid_manifest`
- `tests/test_cli_install_runnable.py::test_install_makes_agent_runnable`
- `tests/test_cli_install_wheels.py::test_install_creates_venv_and_attempts_wheel_install`
- `tests/test_install_refactor.py::test_install_name_resolves_latest_from_mock_registry`
- `tests/test_install_refactor.py::test_install_name_equals_version_from_mock_registry`
- `tests/test_install_refactor.py::test_install_file_path_mode_preserved`

Suggested fix direction:
- Update these tests to use `--yes` when interactive confirmation is not under test.
- For tests that must exercise prompt behavior, provide explicit stdin input (`y`/`n`) and assert the prompt contract intentionally.

### Failure cluster B: pack tests still assume archive output in temp cwd, but pack now stores under local archive backend

Observed behavior:
- Several tests look for `<tmp>/<agent>.kno` and fail to find output.
- Some tests fail due to overwrite prompt/abort when canonical destination already exists.

Affected tests:
- `tests/test_pack.py::test_pack_includes_wheel_files`
- `tests/test_pack.py::test_pack_creates_correct_archive_structure`
- `tests/test_pack.py::test_manual_extraction_verifies_files`
- `tests/test_pack.py::test_pack_prompts_before_overwrite_existing_archive`
- `tests/test_pack_robustness.py::test_pack_includes_transitive_wheels_for_pinned_deps`
- `tests/test_pack_robustness.py::test_kno_zip_format_is_canonical`
- `tests/test_pack_robustness.py::test_pack_continues_on_per_dependency_wheel_failure`
- `tests/test_pack_robustness.py::test_pack_warns_on_platform_specific_wheels`

Suggested fix direction:
- In tests, set `KINNOO_ARCHIVE_ROOT` to a per-test temp directory.
- Assert output/contents using canonical path resolution under archive root instead of cwd assumptions.
- For overwrite-path tests, pre-create collisions at canonical archive destination (not tmp cwd artifact path).

### Failure cluster C: umbrella regression test fails due to underlying pack test failures

Affected test:
- `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`

Suggested fix direction:
- Fix clusters A/B first; this regression should pass once underlying failures are corrected.

### Recommended execution order for SWE recovery

1. Stabilize install tests with explicit non-interactive behavior (`--yes` vs prompt scenarios).
2. Stabilize pack tests around canonical archive path + `KINNOO_ARCHIVE_ROOT` test isolation.
3. Re-run targeted groups:
	- `python3 -m pytest tests/test_cli_install_extract.py tests/test_cli_install_invalid.py tests/test_cli_install_manifest.py tests/test_cli_install_runnable.py tests/test_cli_install_wheels.py tests/test_install_refactor.py`
	- `python3 -m pytest tests/test_pack.py tests/test_pack_robustness.py`
4. Re-run umbrella + full suite:
	- `python3 -m pytest tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`
	- `python3 -m pytest`


# Feature17 TechLead Review (Pre-Merge)

Date: 2026-03-12
Reviewer: techlead-agent
Feature: feature17 - Pack Size Reporting & Warnings

## Verdict

Approved for merge to phase2/main after SWE stabilization.

Initial review was blocked due to repository-level regression failures. After SWE remediation, full-suite health is green and feature17 remains AC-complete.

## Scope Reviewed

- task112: Pack archive size reporting and large-archive warning
- task113: Inspect displays archive size metadata
- task114: List output includes archive size
- task115: Docs and regression coverage for feature17

## Evidence Checked

1. Code paths
   - src/kinnoo/pack_command.py
   - src/kinnoo/inspect_command.py
   - src/kinnoo/list_command.py
   - src/kinnoo/archive.py
   - src/kinnoo/registry_backends.py
   - src/kinnoo/size_format.py
2. Tests
   - tests/test_pack_size_reporting.py
   - tests/test_docs.py
3. Documentation
   - README.md
   - docs/manifest-schema-reference.md
4. Manifest traceability
   - FEATURES.txt
   - TASKS.txt
   - TESTS.txt

## Test Results

### Feature17-focused tests

- Command: python3 -m pytest tests/test_pack_size_reporting.py tests/test_docs.py -k 'feature17 or pack_warns_when_archive_exceeds_threshold_override or pack_prints_human_readable_archive_size or inspect_displays_archive_size_for_archive_target or list_includes_archive_size'
- Result: 5 passed, 7 deselected

### Full repository suite

- Command: python3 -m pytest
- Result: 18 failed, 122 passed, 1 skipped
- High-level failing areas observed:
  - install/unverified-source prompt flow expectations
  - legacy pack output location/overwrite behavior expectations
  - downstream regression umbrella test that depends on those behaviors

## AC Coverage Assessment

- AC1 (`kinnoo pack` prints archive size): covered by test144 and implementation in pack_command.
- AC2 (>100 MB warning): covered by test145 via threshold override mechanism and warning assertion.
- AC3 (`kinnoo inspect` shows archive size): covered by test146 and inspect archive-size output path.
- AC4 (`kinnoo list` includes archive size): covered by test147 for default/local/remote modes.

Conclusion: AC1-AC4 are covered by automated tests and corresponding implementation paths.

## Findings

1. Blocking: Full suite is not green at pre-merge review time.
   - Even though feature17-targeted checks pass, merge-to-main quality gate is not satisfied.

2. Non-blocking (fixed in this review): stale automation_path references for feature17 tests in TESTS.txt.
   - Updated test144/test145/test146 automation_path values to match current test function names.
   - Manifest validator passes after update.

## Improvements / Follow-ups

1. Stabilize pack/install expectation drift across older tests and current behavior contracts so full suite returns to green.
2. Consider a documented CI profile split (feature-scope vs full-regression) to make pre-merge decision criteria explicit.
3. Keep TESTS.txt automation_path entries synchronized during refactors to preserve traceability integrity.

## Merge Recommendation

Merge approved.

Revalidation confirms full-suite quality gate is now satisfied.

---

## SWE Addendum (Post-Stabilization)

Date: 2026-03-12
Author: swe-agent

### What was done to fix the 18 regression failures

1. Stabilized install tests that were unintentionally blocked by the unverified-source prompt flow.
    - Updated non-interactive install tests to pass `--yes` when prompt behavior was not the test objective.
    - Files updated:
       - tests/test_cli_install_extract.py
       - tests/test_cli_install_invalid.py
       - tests/test_cli_install_manifest.py
       - tests/test_cli_install_runnable.py
       - tests/test_cli_install_wheels.py
       - tests/test_install_refactor.py

2. Stabilized pack tests for archive-backend destination semantics.
    - Added per-test `KINNOO_ARCHIVE_ROOT` isolation to prevent cross-test collisions.
    - Updated assertions to use canonical archive backend path:
       - `<archive-root>/<name>/<version>/<name>.kno`
    - Updated overwrite-prompt test to pre-create collision at canonical destination (instead of tmp cwd artifact path).
    - Files updated:
       - tests/test_pack.py
       - tests/test_pack_robustness.py

3. Addressed one wording drift in invalid-archive assertion.
    - Accepted current invalid-zip message variant (`zip-based .kno file`) in addition to older wording.
    - File updated:
       - tests/test_cli_install_invalid.py

### Validation results after fixes

- Targeted cluster rerun:
   - `python3 -m pytest tests/test_cli_install_extract.py tests/test_cli_install_invalid.py tests/test_cli_install_manifest.py tests/test_cli_install_runnable.py tests/test_cli_install_wheels.py tests/test_install_refactor.py tests/test_pack.py tests/test_pack_robustness.py -q`
   - Result: `22 passed`
- Umbrella regression gate:
   - `python3 -m pytest tests/test_regression_v1.py::test_v1_suite_passes_after_feature7 -q`
   - Result: `1 passed`
- Full suite:
   - `python3 -m pytest -q`
   - Result: `140 passed, 1 skipped`

### Teaching note

Security-hardening features often introduce new interaction contracts (for example, explicit trust confirmation prompts).
When that happens, tests should be split intentionally into:

1. Non-interactive flow tests, which must explicitly opt into deterministic behavior (`--yes`) when prompts are not under test.
2. Prompt-contract tests, which should provide explicit stdin (`y`/`n`) and assert prompt text and outcomes.

This pattern keeps trust UX intact while preventing unrelated regressions in CI.

## TechLead Revalidation (Post-SWE Fix)

Date: 2026-03-12
Reviewer: techlead-agent

- Re-ran full suite: `python3 -m pytest -q`
- Result: `140 passed, 1 skipped`
- Decision update: feature17 approved for merge to `phase2/main`.