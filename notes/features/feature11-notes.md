## Feature11 TechLead Review — `kinnoo inspect` (task62–task68)
## Feature11 SWE Handoff — `kinnoo inspect` (tasks 62→68)

### Scope
Implement `kinnoo inspect` to inspect either an agent directory or a `.kno` archive and display human-readable manifest metadata, while enforcing names-only secret safety and clear guidance for missing required files.

### Recommended implementation order (and why)

1. **task62 — Add inspect CLI command parsing**
	 - Establish the command surface and argument behavior first.
	 - This unblocks all downstream inspect behavior behind a stable CLI entrypoint.

2. **task63 — Implement inspect target detection**
	 - Add target type routing (directory vs archive) plus required-file checks for directory targets.
	 - Implement graceful guidance exits for missing `kinnoo.yaml` and missing `requirements.txt`.

3. **task64 — Read manifest directly from .kno zip**
	 - Build archive-path manifest loading next so both source types are functional.
	 - Keep this reusable so future commands can share the same archive-manifest reader.

4. **task65 — Validate manifest and format inspect output**
	 - After manifests can be loaded from both source types, enforce validator-backed errors and human-readable output formatting.
	 - Ensure required-field missing errors are surfaced clearly from validator output.

5. **task66 — Enforce inspect secret-safe display**
	 - Apply safety hardening once output exists.
	 - Confirm inspect remains metadata-only (names, never values) across all output/error paths.

6. **task68 — Add inspect guidance templates with maintenance note**
	 - Centralize missing-file guidance strings and minimal `kinnoo.yaml` example in one reusable location.
	 - Include explicit `[agent]` maintenance note so schema/template changes trigger updates to the minimal example.
	 - Placing this after core flow reduces rework while still shipping as part of feature11.

7. **task67 — Document inspect command usage and examples**
	 - Land documentation last so it reflects the final command behavior and exact guidance text.

### Expected file touch points by task

- **task62**
	- `src/kinnoo/cli.py`

- **task63**
	- `src/kinnoo/inspect_command.py`

- **task64**
	- `src/kinnoo/inspect_command.py`
	- `src/kinnoo/install_command.py` (only if shared archive reader helper is placed/reused here)

- **task65**
	- `src/kinnoo/inspect_command.py`
	- `src/kinnoo/validator.py` (only if message plumbing/helper reuse is needed)

- **task66**
	- `src/kinnoo/inspect_command.py`
	- `tests/test_cli.py` and/or `tests/test_cli_inspect.py` when implemented

- **task68**
	- `src/kinnoo/templates.py` (preferred location for reusable minimal manifest text)
	- `src/kinnoo/inspect_command.py` (consume centralized template/guidance strings)

- **task67**
	- `README.md`
	- `docs/manifest-schema-reference.md`

### Implementation constraints and quality guardrails

- Keep inspect output **human-readable**, not raw YAML.
- Missing optional fields should be **omitted**, not shown as `None`/empty placeholders.
- For directory targets:
	- Missing `kinnoo.yaml` ⇒ print stdout guidance + minimal manifest example, then graceful non-zero exit.
	- Missing `requirements.txt` ⇒ print stdout guidance + robust generation guidance:
		- `pip install uv`
		- `uv export --format requirements-txt > requirements.txt`
- For archive targets:
	- Read `kinnoo.yaml` directly from zip members without full extraction.
- Secret safety:
	- Show env var **names only**; never resolve/print runtime secret values.
- Keep error messages deterministic and stable to support future unit/integration assertions.

### Suggested SWE grouping

- **Group A (core runtime path):** task62, task63, task64, task65
- **Group B (security + template centralization):** task66, task68
- **Group C (docs):** task67

This grouping allows one SWE to complete Group A first for functional inspect behavior, then harden and document without blocking core delivery.


**Review date:** 2026-03-05  
**Reviewer:** techlead-agent  
**Scope reviewed:** `task62` → `task68`, `test89` → `test95`, feature11 AC1–AC9

### Verdict

**Approved for merge to `phase2/main`** with minor non-blocking cleanup suggestions.

Implementation quality is strong, behavior aligns with requested UX/security constraints, and automated evidence is complete for the scoped feature.

### Evidence checked

- SWE implementation notes reviewed for:
  - `notes/tasks/task62-notes.md`
  - `notes/tasks/task63-notes.md`
  - `notes/tasks/task64-notes.md`
  - `notes/tasks/task65-notes.md`
  - `notes/tasks/task66-notes.md`
  - `notes/tasks/task67-notes.md`
  - `notes/tasks/task68-notes.md`
- Source paths reviewed:
  - `src/kinnoo/cli.py`
  - `src/kinnoo/inspect_command.py`
  - `src/kinnoo/templates.py`
  - `src/kinnoo/validator.py`
  - `tests/test_cli_inspect.py`
  - `tests/test_docs.py`
- Validation run by TechLead:
  - `python3 -m pytest tests/test_cli_inspect.py tests/test_docs.py` → **9 passed**
  - `python3 src/validate_project_manifests.py` → **Validation passed**

### AC coverage assessment (feature11)

- **AC1** (`inspect <agent-dir>` metadata incl. env var names): **Covered** by `test92`, `test93`.
- **AC2** (`inspect <archive.kno>` manifest read from zip without extraction): **Covered** by `test91`.
- **AC3** (human-readable output, not raw YAML): **Covered** by `test92`.
- **AC4** (omit missing optional fields): **Covered** by `test92`.
- **AC5** (invalid manifest gives clear validator-based error): **Covered** by `test92`.
- **AC6** (missing inspect args prints usage): **Covered** by `test89`.
- **AC7** (missing `kinnoo.yaml` guidance + minimal example + graceful exit): **Covered** by `test90`, `test95`.
- **AC8** (missing `requirements.txt` guidance + robust uv instructions + graceful exit): **Covered** by `test90`.
- **AC9** (missing required fields clearly named): **Covered** by `test92`.

### Gaps / inconsistencies found

No blocking gaps found against AC1–AC9.

Non-blocking inconsistencies/improvements:

1. **Task file-touchpoint drift (minor):**
   - `task66` lists `tests/test_cli.py`, but implemented/covered in `tests/test_cli_inspect.py`.
   - Suggest updating task file list to match actual touched test module for traceability.

2. **Guidance channel consistency (minor UX):**
   - Missing-file guidance intentionally prints to stdout (per requirement), while other errors print to stderr.
   - Behavior is acceptable; consider documenting this explicitly in docs to reduce operator confusion.

3. **Output contract hardening (future-proofing):**
   - Current tests assert key lines and no secrets; consider adding snapshot-style formatting tests if inspect output evolves.

### Security review note

- Names-only env var behavior is correctly enforced in inspect path.
- No evidence of runtime env var value leakage in inspect output.
- Centralized minimal manifest template with explicit `[agent]` maintenance note is present and tested (`test95`).

### Merge recommendation

Proceed with merge of feature11 task62–task68 into `phase2/main`.
