# Feature14 SWE Handoff — Preflight Checks (`kinnoo run --preflight`)

## Scope
Implement feature14 through tasks `task92` to `task97` in order. The goal is to add a preflight-only validation mode to `kinnoo run` that checks runtime readiness without executing agent logic.

## Task execution order and dependencies
1. `task92` — Add `--preflight` CLI mode wiring
2. `task93` — Implement runtime version preflight check (depends on `task92`)
3. `task94` — Implement env vars preflight resolution check (depends on `task92`, and reuses feature10 env/security behavior)
4. `task95` — Implement entrypoint and dependency checks (depends on `task92`)
5. `task96` — Add checklist output and ready summary (depends on `task93`, `task94`, `task95`)
6. `task97` — Document preflight usage and contracts (depends on `task96`)

Single SWE agent can implement all six tasks in one pass because these are tightly coupled and sequential.

## Tests to implement (already declared in TESTS.txt)
- `task92` -> `test120`
- `task93` -> `test121`
- `task94` -> `test122`
- `task95` -> `test123`
- `task96` -> `test124`
- `task97` -> `test125`

Feature14 AC coverage mapping:
- `AC1`: `test120` (+ docs assertion in `test125`)
- `AC2`: `test121`
- `AC3`: `test122`
- `AC4` + `AC5`: `test123`
- `AC6` + `AC7`: `test124`

## Design constraints (must follow)
- `--preflight` must **never execute** the agent entrypoint.
- Output must be checklist-style and deterministic for stable assertions.
- Secret safety is mandatory: env var **names only**, never values.
- Reuse existing manifest/env resolution logic where possible; avoid duplicate logic.
- Keep normal `kinnoo run` behavior unchanged when `--preflight` is not used.

## Files expected to change
- Code: `src/kinnoo/cli.py`, `src/kinnoo/run_command.py`, optionally `src/kinnoo/validator.py`/`src/kinnoo/schema.py` if needed for reusable check helpers.
- Tests: add/extend `tests/test_run_preflight.py`; update `tests/test_docs.py` for docs coverage.
- Docs: `README.md`, `docs/manifest-schema-reference.md`.

## SWE completion checklist
- Implement tasks `task92`..`task97` in order.
- Implement tests `test120`..`test125` and ensure they pass.
- Run `python3 -m pytest` (or targeted preflight/doc tests first, then full suite as needed).
- Update task statuses to `needs-review` when complete.
- Run `python3 src/validate_project_manifests.py` before handoff.
