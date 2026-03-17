## Feature19 SWE Handoff - In-Place Import Onboarding (task163-task167)

### Scope
Implement feature19 as an in-place onboarding workflow:
`kinnoo import [path]` (default `.`) writes `kinnoo.yaml` into an existing
project using feature27 analyzer inference and a confirm-first wizard.

### Scope Tightening (Important)
- Do not implement copy/scaffold-clone behavior.
- Import is metadata-layer only: in-place `kinnoo.yaml` generation plus optional
  wrapper file when explicitly selected by user.
- Reuse `analyze_project()` as the single inference backend. Do not duplicate
  detector heuristics in import command code.
- Keep entrypoint mismatch behavior warning-first and non-blocking by default.
- Ensure interruption/failure safety leaves no partial artifacts.

### Task Order and Grouping
Single SWE agent can implement all tasks in order because they share one command
surface and one test module.

1. `task163` - Import CLI surface and path resolution
2. `task164` - In-place write + collision + rollback
3. `task165` - Analyzer integration + confirm-first wizard
4. `task166` - Conditional schema prompts + entrypoint bridge option
5. `task167` - Interrupt safety + in-place runnability regression gate

### Dependencies
- `task164` depends on `task163`
- `task165` depends on `task162`, `task163`
- `task166` depends on `task165`
- `task167` depends on `task164`, `task166`

### Design Constraints
- Command signature: `kinnoo import [path]` only; no destination directory.
- Default target path is current working directory.
- Existing project files must not be modified (except created/updated
  `kinnoo.yaml`, and optional wrapper when user explicitly accepts).
- Error and help text should be clear and actionable.
- Prompt minimization is required: show detected values first, ask follow-ups
  only for unresolved/low-confidence fields.

### Files Expected to Change
- `src/kinnoo/cli.py`
- `src/kinnoo/import_command.py` (new)
- `src/kinnoo/schema.py` (only if needed for prompt-gating helpers)
- `tests/test_cli_import.py` (new)
- `tests/test_regression_v1.py` (feature19 focused regression gate)

### Per-Task Deliverables
1. `task163`:
- Add import subcommand parser and usage/help wiring.
- Implement default `.` path behavior and invalid argument handling.
- Add tests for omitted path and invalid forms.

2. `task164`:
- Implement in-place manifest write path.
- Add collision protections for existing `kinnoo.yaml` unless explicit override.
- Add rollback cleanup for failure scenarios after write begins.
- Prove no scaffold-copy behavior.

3. `task165`:
- Integrate analyzer results into manifest generation.
- Implement confirm-first wizard flow.
- Prompt only for missing/ambiguous fields.

4. `task166`:
- Add conditional prompts for runtime/services/permissions fields only when
  unresolved or low-confidence.
- Implement entrypoint mismatch warning.
- Add optional wrapper-generation branch that is opt-in.

5. `task167`:
- Handle Ctrl+C/EOF safely with non-zero exit.
- Ensure no partial artifact remains on interruption.
- Add in-place runnability gate and feature19 regression protection.

### Out of Scope (Feature19)
- Remote URL import (`kinnoo import https://...`).
- Deep framework-specific translators.
- Runtime shims as a required import path.
- Any broad analyzer heuristic expansion beyond feature27 contract.

### Test Plan (from TESTS.txt)
- `test252`, `test253`: AC1 argument/default behavior
- `test254`: AC2 in-place write and no copy behavior
- `test255`: AC5 rollback on failure
- `test256`: AC7 collision safety
- `test257`: AC3 analyzer-backed inference and warnings
- `test258`: AC4 confirm-first wizard prompt minimization
- `test259`: AC9 conditional schema-extension prompts
- `test260`: AC10 warning-first entrypoint bridge with optional wrapper
- `test261`: AC6 Ctrl+C/EOF safety
- `test262`: AC8 in-place runnability after import

### Execution Notes for SWE
- Implement `tests/test_cli_import.py` early to lock behavior contract.
- Use fixture projects under `tests/` for deterministic inference and prompt flow.
- Keep user-facing warning text stable enough for test assertions.
- Prefer small helper functions in import module (path resolution, prompt policy,
  rollback cleanup, wrapper generation) to keep logic testable.

### Definition of Done
- All ACs (AC1-AC10) are covered by passing tests `test252`-`test262`.
- `python3 src/validate_project_manifests.py` passes.
- Focused feature19 tests pass.
- Full `python3 -m pytest` regression passes before handoff to TechLead review.
- Tasks move to `needs-review` when SWE completes implementation.
