# Task489 SWE Handoff — Multi-Entrypoint Manifest and Runtime Selection

## Context
Task489 introduces first-class support for agents that expose multiple runnable scripts while preserving backward compatibility for existing single-entrypoint agents.

Requested contract:
- Allow either:
  - `entrypoint: <script>` (legacy single-entrypoint form), OR
  - `entrypoints: [<script1>, <script2>, ...]` (new multi-entrypoint form)
- Disallow both fields in the same manifest.
- Add `kinnoo run --entrypoint <script>`:
  - script must be declared in manifest (single or list form)
  - script path must exist in agent codebase
- If manifest uses `entrypoints` and run is called without `--entrypoint`, default to first list item.
- Ensure `kinnoo inspect` and `kinnoo check` enforce these validation rules.
- Ensure `kinnoo run --json` includes relevant selected-entrypoint metadata.
- Support nested subfolder script paths such as `scripts/src/main.py`.

## Scope
Implement `task489` exactly as captured in `TASKS.txt` with tests `test685`-`test692` in `TESTS.txt` and AC17 in `FEATURES.txt`.

## Ordered Implementation Plan
1. Extend schema and validation for entrypoint union contract.
2. Update runtime selection logic (`run`) with explicit `--entrypoint` behavior.
3. Add validation checks in inspect/check paths (mutual exclusivity + path existence).
4. Add JSON contract fields for selected/default/declared entrypoint in run output.
5. Add tests and docs updates.

## Detailed Requirements

### A) Manifest contract
- Accept one of the following:
  - `entrypoint: <script>` where `<script>` is a non-empty string.
  - `entrypoints: [<script>, ...]` where list is non-empty and each item is non-empty string.
- Reject manifests where both keys are present.
- Reject manifests where neither key is present (unless existing schema currently guarantees one; preserve existing required-field semantics).

### B) Path validation rules
- Declared script path(s) must exist under agent root.
- Relative nested paths are valid (e.g., `scripts/src/main.py`, `src/runner.ts`).
- Validation should produce deterministic, user-readable errors naming missing path(s).
- `kinnoo inspect` and `kinnoo check` should surface these errors consistently.

### C) Run CLI behavior
- Add `--entrypoint <script>` option to `kinnoo run` parser and help.
- Selection logic:
  - `entrypoint` mode:
    - default selected script = `entrypoint` value
    - if `--entrypoint` provided and differs, fail with clear mismatch guidance
  - `entrypoints` mode:
    - default selected script = first list element when no `--entrypoint`
    - if `--entrypoint` provided, must be in list; else fail with allowed-values guidance
- Selected script must also pass path existence checks prior to execution.

### D) JSON output contract
- `kinnoo run --json` should include entrypoint-selection metadata at minimum:
  - selected entrypoint script
  - selection source (`default` or `flag`)
  - declared contract mode (`entrypoint` or `entrypoints`)
- Keep prior JSON fields backward compatible where possible.

### E) Backward compatibility guarantees
- Existing agents using only `entrypoint` should continue to run unchanged.
- Existing tests unrelated to entrypoint selection should remain stable.
- Error messages should be intelligent and deterministic for CI assertions.

## Files Expected to Change
- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `src/kinnoo/cli.py`
- `src/kinnoo/run_command.py`
- `src/kinnoo/inspect_command.py`
- `src/kinnoo/check_command.py`
- `tests/test_cli.py`
- `tests/test_cli_inspect.py`
- `tests/test_run_preflight.py`
- `tests/test_docs.py`
- `docs/manifest-schema-reference.md`
- `docs/cli-reference.md`
- `docs/getting-started.md`

## Acceptance Criteria Mapping
- Feature: `feature115`
- AC coverage: `AC17`
- Tests: `test685`, `test686`, `test687`, `test688`, `test689`, `test690`, `test691`, `test692`

## Test Execution Guidance
At minimum run:
- `python3 -m pytest tests/test_cli.py -k "entrypoint or entrypoints"`
- `python3 -m pytest tests/test_cli_inspect.py -k "entrypoint or entrypoints"`
- `python3 -m pytest tests/test_run_preflight.py -k "entrypoint or entrypoints"`
- `python3 -m pytest tests/test_docs.py -k "entrypoint or entrypoints"`
- `python3 src/validate_project_manifests.py`

## Risks and Pitfalls
- Ambiguous precedence if both fields are accidentally accepted.
- Silent fallback to an undeclared script when `--entrypoint` is invalid.
- Divergent validation between run/inspect/check causing confusing UX.
- JSON contract drift if selected entrypoint metadata is omitted in some paths.
- Path normalization issues for nested scripts on different OS path separators.

## Definition of Done
- Manifest schema/validator enforces exclusive single-vs-list entrypoint contract.
- `kinnoo run --entrypoint` works with deterministic selection and robust validation.
- `kinnoo inspect`/`kinnoo check` enforce exclusivity and file existence checks.
- `run --json` exposes selected-entrypoint metadata.
- Tests `test685`-`test692` pass and docs are updated accordingly.
