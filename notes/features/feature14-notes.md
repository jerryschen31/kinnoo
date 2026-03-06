# Feature14 TechLead Review — Preflight Checks (`kinnoo run --preflight`)

Date: 2026-03-06
Reviewer: techlead-agent
Verdict: **Approved for merge to `phase2/main` with non-blocking follow-ups**

## Scope reviewed
- Feature manifest entry: `feature14` in `FEATURES.txt`
- Tasks: `task92`..`task97` in `TASKS.txt` (all currently `needs-review`)
- Tests: `test120`..`test125` in `TESTS.txt`
- SWE implementation notes: `notes/tasks/task92-notes.md` .. `notes/tasks/task97-notes.md`
- Implementation files sampled:
  - `src/kinnoo/cli.py`
  - `src/kinnoo/run_command.py`
  - `tests/test_run_preflight.py`
  - `tests/test_docs.py`
  - docs references in `README.md` and `docs/manifest-schema-reference.md`

## Evidence executed
- `python3 -m pytest tests/test_run_preflight.py tests/test_docs.py -q`
  - Result: `10 passed`
- `python3 src/validate_project_manifests.py`
  - Result: `Validation passed: manifests are consistent`

## Task-by-task review
- `task92` (CLI preflight wiring): implemented and evidenced; preflight branch exits without executing entrypoint.
- `task93` (runtime.version check): implemented with deterministic pass/fail messaging and actionable guidance.
- `task94` (env var resolvability, names-only): implemented using env + `.env` resolution and non-disclosure output.
- `task95` (entrypoint + dependency checks): implemented; detects missing entrypoint and dependency readiness gaps.
- `task96` (checklist + readiness summary): implemented; stable checklist output and final PASS/FAIL summary behavior.
- `task97` (docs): implemented; docs test validates preflight command contract and security language.

Task notes in `notes/tasks/task92-notes.md`..`task97-notes.md` are present, consistent with code and test artifacts, and include concrete command evidence.

## AC coverage assessment
Feature14 ACs are fully covered by declared tests and observed implementation:
- AC1 -> `test120` (runtime behavior), additionally reinforced by `test125` (docs contract)
- AC2 -> `test121`
- AC3 -> `test122`
- AC4 + AC5 -> `test123`
- AC6 + AC7 -> `test124`

No missing AC mapping found in `TESTS.txt` for `feature14`.

## Gaps / inconsistencies / improvement opportunities
No blocking issues found. Non-blocking improvements:
1. **AC5 wording vs implementation depth**
   - AC5 says dependencies are "installed in the venv (or installable)".
   - Current implementation verifies installed readiness (`pip show`) and `.venv` presence, but does not explicitly validate "installable" in the absence of installed packages.
   - Recommendation: add a follow-up task/test to check installability semantics (e.g., deterministic dry-run or explicit resolver check) if this interpretation is required.

2. **Preflight argument strictness (optional hardening)**
   - Current CLI allows `kinnoo run <dir> <input> --preflight` (input ignored in preflight mode).
   - Recommendation: optionally enforce no input with `--preflight` for stricter UX determinism, or document that extra input is ignored.

3. **Deterministic messaging contract**
   - Output is currently stable and test-covered, which is good.
   - Recommendation: keep snapshot/contract tests for all checklist lines to prevent accidental message drift in future refactors.

## Merge recommendation
- Feature14 is technically sound, tests pass, manifests are consistent, and AC coverage is complete.
- Recommend advancing feature/task statuses per workflow after human approval in PR review.
