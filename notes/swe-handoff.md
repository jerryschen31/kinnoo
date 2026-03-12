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
