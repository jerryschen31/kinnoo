# Feature17 TechLead Review (Pre-Merge)

Date: 2026-03-12
Reviewer: techlead-agent
Feature: feature17 - Pack Size Reporting & Warnings

## Verdict

Do not approve merge to phase2/main yet.

Feature17 implementation itself appears correct and AC-complete, but repository-level test health is not green at review time (full suite has failing tests). Merge should be blocked until baseline failures are resolved or explicitly triaged/waived by project maintainers.

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

Hold merge for now.

Approval can proceed once full-suite failures are resolved or formally dispositioned with owner sign-off.