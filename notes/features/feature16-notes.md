# Feature16 SWE Handoff — Archive Integrity (Checksums)

## Scope
Implement feature16 through tasks `task105` to `task111` in order. The goal is to add checksum generation, verification, and propagation across pack/install/inspect/publish to detect tampered or corrupted archives.

Core contract: checksum verification must be deterministic, user-facing errors must be clear, and install behavior must distinguish between **mismatch (hard fail)** and **missing checksum (warning + proceed)**.

## Task execution order and dependencies

### Group 1 — Checksum foundation
1. `task105` — Generate `.kno.sha256` during pack and alongside local archive artifacts (AC1, AC5)
2. `task106` — Add shared checksum helpers for compute/parse/verify (internal foundation)

### Group 2 — Install integrity enforcement
3. `task107` — Verify checksum on file-path install when sidecar exists (AC2, AC3)
4. `task108` — Missing checksum warning path that continues install (AC4)

### Group 3 — Visibility and registry propagation
5. `task109` — Display checksum in inspect output for archives (AC6)
6. `task110` — Publish `.kno.sha256` alongside `.kno` when present (AC7)

### Group 4 — Documentation finish
7. `task111` — Docs coverage for pack/install/inspect/publish checksum lifecycle

A single SWE agent can implement all tasks in one sequence. Group 1 should land first, Group 2 second, Group 3 third, Group 4 last.

## Tests to implement (already declared in TESTS.txt)
- `task105` -> `test135`, `test136`
- `task106` -> `test137`
- `task107` -> `test138`, `test139`
- `task108` -> `test140`
- `task109` -> `test141`
- `task110` -> `test142`
- `task111` -> `test143`

## Feature16 AC coverage mapping
- `AC1`: `test135`
- `AC2`: `test138`
- `AC3`: `test139`
- `AC4`: `test140`
- `AC5`: `test136`
- `AC6`: `test141`
- `AC7`: `test142`

`test143` validates docs completeness for the full checksum lifecycle.

## Design constraints (must follow)

### Checksum file format and naming
- Sidecar path format must be sibling to archive: `<archive>.kno.sha256`.
- Content format must be stable and parseable: `<sha256>  <archive-filename>`.
- SHA256 digest must be lowercase hex and computed from archive bytes only.

### Install verification semantics
- For `kinnoo install <file.kno>`:
  - If sidecar exists and hash matches -> proceed.
  - If sidecar exists and hash mismatches -> abort with exact error:  
    `Archive integrity check failed — the file may be corrupted or tampered with`
  - If sidecar missing -> print warning and proceed:  
    `No checksum file found — archive integrity not verified`
- Verification must happen before extraction/write operations.

### Publish and inspect behavior
- Publish should copy checksum sidecar iff source sidecar exists; absence is non-fatal.
- Inspect should display checksum for archive targets when available from sidecar (or deterministic helper path).
- Do not break existing inspect/list/publish output contracts beyond additive checksum information.

### Security and reliability
- Never include secret/env var values in checksum-related logs or errors.
- File I/O errors should produce actionable messages with non-ambiguous failure causes.
- Reuse shared helpers to avoid duplicate hashing/parsing logic across commands.

## Files expected to change
- New file: `src/kinnoo/checksum.py`
- Modify: `src/kinnoo/pack_command.py`
- Modify: `src/kinnoo/install_command.py`
- Modify: `src/kinnoo/inspect_command.py`
- Modify: `src/kinnoo/publish_command.py`
- New tests: `tests/test_archive_integrity.py`
- Modify: `tests/test_docs.py`
- Modify docs: `README.md`, `docs/manifest-schema-reference.md`

## SWE implementation guidance
- Implement checksum helper APIs first (compute, parse sidecar, verify pair), then integrate command-by-command.
- Keep error strings stable so tests can assert exact behavior.
- Ensure feature15 trust warning behavior for unverified source remains coherent with feature16 checksum verification (feature16 adds verification, not conflicting prompts).
- Use temporary files/fixtures in tests to cover both match and mismatch hash cases deterministically.

## SWE completion checklist
- [ ] Implement `task105`..`task111` in dependency order.
- [ ] Implement `test135`..`test143` with deterministic fixtures.
- [ ] Run focused tests: `python3 -m pytest tests/test_archive_integrity.py tests/test_docs.py -q`.
- [ ] Run manifest validation: `python3 scripts/validate_project_manifests.py`.
- [ ] Update task statuses `not-started -> in-progress -> needs-review`.
- [ ] Add implementation notes for each task under `notes/tasks/task105-notes.md` .. `notes/tasks/task111-notes.md`.

## Per-Task Handoff Notes

### task105 — Generate checksum sidecar during pack
**Objective**
- Ensure every successful `kinnoo pack` run emits `<archive>.kno.sha256` next to the produced archive.

**Implementation notes**
- Hook checksum generation after final archive write succeeds.
- Use a stable sidecar format: `<sha256>  <archive-filename>`.
- Ensure this works for both explicit output paths and archive-first local paths.

**Definition of done**
- `test135` and `test136` pass.
- Pack output clearly indicates where checksum sidecar is written.

### task106 — Add checksum utility helpers
**Objective**
- Centralize checksum compute/parse/verify logic so install/inspect/publish share the same behavior.

**Implementation notes**
- Create `src/kinnoo/checksum.py` with small, composable functions.
- Helper API should cover file hash compute, sidecar parse/read, and expected-vs-actual verify.
- Keep parsing strict enough to avoid ambiguous sidecar interpretation.

**Definition of done**
- `test137` passes.
- No duplicate checksum/parsing logic remains in command modules.

### task107 — Enforce checksum verification on install
**Objective**
- Verify integrity before extraction when sidecar exists for `kinnoo install <file.kno>`.

**Implementation notes**
- Resolve sidecar path deterministically from archive path.
- Run verify step before any extraction or venv setup side effects.
- On mismatch, fail with exact message:
  - `Archive integrity check failed — the file may be corrupted or tampered with`

**Definition of done**
- `test138` and `test139` pass.
- Mismatch case exits non-zero with exact expected message.

### task108 — Missing checksum warning on install
**Objective**
- Preserve install usability when sidecar is absent, while making integrity status explicit.

**Implementation notes**
- When no sidecar exists, emit warning and continue install path unchanged.
- Warning text must remain stable:
  - `No checksum file found — archive integrity not verified`

**Definition of done**
- `test140` passes.
- Missing-sidecar path remains warning-only (no false failure).

### task109 — Show checksum in inspect output
**Objective**
- Improve operator visibility by surfacing archive checksum in `kinnoo inspect` output.

**Implementation notes**
- For `.kno` target inspection, read checksum sidecar if available.
- Render checksum as additive metadata field without breaking existing formatting.
- Keep behavior deterministic for tests (avoid non-deterministic formatting).

**Definition of done**
- `test141` passes.
- Inspect output includes checksum field/value when available.

### task110 — Publish checksum sidecar with archive
**Objective**
- Keep published artifact and checksum paired so downstream install can verify integrity.

**Implementation notes**
- During publish, if source sidecar exists, copy it to destination alongside `.kno`.
- Sidecar absence must not block publish success.
- Add clear publish output indicating whether sidecar was published.

**Definition of done**
- `test142` passes.
- Registry destination contains both files when sidecar is present upstream.

### task111 — Docs and regression coverage for checksums
**Objective**
- Ensure docs and tests communicate the full checksum lifecycle to users and maintainers.

**Implementation notes**
- Update `README.md` and `docs/manifest-schema-reference.md` for pack/install/inspect/publish checksum behavior.
- Add/update docs test to assert required checksum statements are present.
- Keep examples aligned with exact CLI behavior and warning/error strings.

**Definition of done**
- `test143` passes.
- Docs reflect AC1-AC7 behaviors consistently.


# TechLead Review — Feature16 (Archive Integrity / Checksums)

Date: 2026-03-11  
Reviewer: TechLead agent

## Verdict

**Approved for merge to phase2/main**, with non-blocking follow-ups listed below.

## Scope Reviewed

- Feature: `feature16` in `FEATURES.txt`
- Tasks: `task105`–`task111` in `TASKS.txt`
- Tests: `test135`–`test143` in `TESTS.txt`
- SWE notes reviewed:
  - `notes/tasks/task105-notes.md` … `notes/tasks/task111-notes.md`
- Code paths reviewed:
  - `src/kinnoo/checksum.py`
  - `src/kinnoo/pack_command.py`
  - `src/kinnoo/install_command.py`
  - `src/kinnoo/inspect_command.py`
  - `src/kinnoo/publish_command.py`
- Docs reviewed:
  - `README.md`
  - `docs/manifest-schema-reference.md`

## Validation Evidence

Executed in repo root:

1. `python3 -m pytest tests/test_archive_integrity.py tests/test_docs.py -k "feature16 or checksum"`
   - Result: **9 passed, 6 deselected**

2. `python3 scripts/validate_project_manifests.py`
   - Result: **Validation passed: manifests are consistent**

## AC Coverage Assessment

### AC1 — pack generates `.kno.sha256` sidecar next to archive

**Status: Covered**

- Implemented via shared checksum sidecar writer called from pack flow.
- Covered by `test135`.

### AC2 — install verifies checksum when sidecar exists

**Status: Covered**

- Install resolves sidecar, parses, validates filename token, verifies digest before extraction.
- Covered by `test138`.

### AC3 — install aborts on checksum mismatch with clear error

**Status: Covered**

- Mismatch path aborts pre-extraction with required message:
  `Archive integrity check failed — the file may be corrupted or tampered with`
- Covered by `test139`.

### AC4 — install warns and proceeds if no sidecar

**Status: Covered**

- Warning path present and non-blocking:
  `No checksum file found — archive integrity not verified`
- Covered by `test140`.

### AC5 — pack stores checksum alongside local archive artifact

**Status: Covered**

- Archive-backend destination includes sibling sidecar after pack store.
- Covered by `test136`.

### AC6 — inspect displays archive checksum when available

**Status: Covered**

- Inspect archive path displays checksum metadata when valid sidecar exists.
- Covered by `test141`.

### AC7 — publish propagates sidecar with archive

**Status: Covered**

- Publish copies sidecar when source sidecar exists; emits explicit status line.
- Covered by `test142`.

## Gaps / Inconsistencies Found

No blocking implementation gaps were found for feature16 acceptance criteria.

Non-blocking inconsistencies:

1. **Workflow status mismatch in manifests:**
   - `task105`–`task111` are `needs-review`, but `feature16` status is still `not-started`.
   - Recommendation: move feature16 status to `in-progress`/`needs-review` to reflect actual lifecycle.

2. **Automation path drift in TESTS.txt metadata:**
   - Some `automation_path` node IDs appear stale compared to actual test function names in `tests/test_archive_integrity.py` / `tests/test_docs.py` (for example `test141`, `test142`, `test143`). FIXED
   - This does not break runtime validation but reduces manifest-to-test traceability.

## Improvement Suggestions (Post-merge)

1. Add a strict manifest lint check that resolves `automation_path` node IDs against collected pytest tests.
2. Consider surfacing sidecar parse failures in inspect output as explicit warning metadata (currently checksum display is opportunistic and silent on invalid sidecars).
3. Consider adding registry-install checksum verification path once registry sidecars are widely present.

## Final Recommendation

Feature16 is implemented correctly, test-backed, and ready to merge.
