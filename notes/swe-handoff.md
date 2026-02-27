# SWE Handoff Brief — Feature7 (CLI Refactor & Modular Architecture)

## Goal
Implement `feature7` end-to-end with clean modularization and no regressions:

- AC1: Install logic lives in `src/kinnoo/install_command.py`.
- AC2: `cli.py` delegates install operations to `install_command.py`.
- AC3: `kinnoo --version` prints package version and exits `0`.
- AC4: No duplicate test functions exist in the test suite.
- AC5: Existing V1 tests pass after refactor.

Feature status reference:
- Feature: `feature7`
- Tasks: `task39`, `task40`, `task41`
- Tests: `test61`, `test62`, `test63`, `test64`

---

## Current Codebase Context (as of handoff)

- `src/kinnoo/install_command.py` does **not** exist yet.
- Install flow is currently implemented inline in `src/kinnoo/cli.py` under `elif args.command == "install":`.
- `cli.py` currently has no top-level `--version` flag.
- Package version is declared in `pyproject.toml` as `1.0.0`.
- `src/kinnoo/__init__.py` currently exports only `validate`.

This means `task39` and `task40` are currently unmet and are the first implementation priorities.

---

## Implementation Scope & Order

### 1) task39 — Extract install flow into module
Files:
- `src/kinnoo/install_command.py` (new)
- `src/kinnoo/cli.py`
- `src/kinnoo/__init__.py` (only if needed for version/import ergonomics)

Required outcome:
- Move install-specific logic out of `cli.py` into a dedicated function in `install_command.py`.
- `cli.py` should parse install args, then call the install command function.
- Preserve behavior and user-facing error semantics unless intentionally improved.

Suggested function shape:
- `def install_agent(archive_path: str, target_dir: str | None = None, force: bool = False) -> int:`

Guidance:
- Keep CLI argument parsing in `cli.py`; keep install execution in `install_command.py`.
- Return exit codes from command functions rather than calling `sys.exit()` deep in helper logic when practical.
- Handle errors with clear messages; avoid stack traces for expected failures.

### 2) task40 — Add global `--version`
Files:
- `src/kinnoo/cli.py`
- `src/kinnoo/__init__.py`
- `pyproject.toml` (only if needed to avoid version duplication)

Required outcome:
- `kinnoo --version` works without subcommands and exits `0`.
- Version should come from a single canonical source (avoid hardcoded duplicates).

Suggested approach:
- Add parser-level version action in argparse.
- Expose `__version__` from package metadata (e.g., `importlib.metadata.version("kinnoo")`) or other single-source strategy.

### 3) task41 — Remove duplicate test functions
Files (minimum):
- `tests/test_cli.py`
- `tests/test_init.py`
- `tests/test_pack.py`
- `tests/test_install.py`
- `tests/test_validator.py`
- plus any new test files needed by test entries below.

Required outcome:
- No duplicate test function names / duplicate collection targets causing ambiguous pytest collection.
- Keep scenario coverage while consolidating duplicates.

---

## Test Implementation Requirements

These test manifest entries already exist and must be implemented/aligned:

- `test61` → `tests/test_cli_install.py::test_install_delegates_to_install_command`
- `test62` → `tests/test_cli.py::test_cli_version_flag`
- `test63` → `tests/test_suite_integrity.py::test_no_duplicate_test_functions`
- `test64` → `tests/test_regression_v1.py::test_v1_suite_passes_after_feature7`

Notes:
- If these files do not exist, create them.
- Keep tests deterministic and CI-friendly.
- For CLI tests, follow project guidance to invoke via script path (e.g., `python src/kinnoo/cli.py ...`) where applicable.

---

## Validation Checklist (must run before handback)

1. Run targeted tests for feature7 additions:
	- `python3 -m pytest tests/test_cli_install.py tests/test_cli.py tests/test_suite_integrity.py tests/test_regression_v1.py`
2. Run broader regression as needed for confidence:
	- `python3 -m pytest`
3. Validate manifests after any TASKS/TESTS edits:
	- `python3 src/validate_project_manifests.py`

Expected result:
- Feature7 tests pass.
- V1 regression pass condition for AC5 is demonstrated.
- Manifest validator passes.

---

## Constraints / Non-Goals

- Do not implement new product features beyond feature7.
- Do not change manifest schema semantics.
- Preserve security hygiene (no secret values in logs/output).
- Keep changes minimal and modular; avoid broad CLI rewrites unrelated to feature7.

---

## Status Update Protocol

When work starts/completes:
- Set `task39`, `task40`, `task41` to `in-progress` during implementation.
- Set to `needs-review` when code + tests are complete and validated.
- Do not mark these tasks `completed` in SWE handoff; completion occurs after TechLead review.

---

## Handoff Deliverables

Please hand back:
- Code changes implementing task39–41.
- New/updated tests satisfying test61–64.
- Test run outputs summary.
- Confirmation that manifest validation passes.
