# SWE Agent Handoff — Feature 20: Flexible Runtime Inputs

**Date:** 2026-03-15
**From:** TechLead Agent
**Feature:** feature20 — Flexible Runtime Inputs (No-input run & pass-through arguments)
**Branch:** Create `phase3/feature20/main` from `master`; use one task branch per task (`phase3/feature20/task121`, etc.)
**Status:** `not-started` -> set to `in-progress` when implementation starts

---

## Overview

Implement flexible input handling for `kinnoo run` with three supported invocation modes:

1. Legacy single input (must remain unchanged):
   - `kinnoo run <dir> "hello"`
2. No-input execution for self-contained agents:
   - `kinnoo run <dir>` only when manifest has `inputs.required: false`
3. Parameterized pass-through mode:
   - `kinnoo run <dir> -- -e "text" -u "url" -p "path"`

This feature also requires schema support for `inputs.required` and integration with the existing input safety guard so pass-through arguments are scanned (unless `--no-guard` is used).

Primary risk: CLI parsing and run flow changes can break legacy V2 behavior if not done carefully.

---

## Task Execution Order

`task121 -> task122 -> task123 -> task124`

Tasks are intentionally sequential because each later task depends on earlier schema/parsing behavior.

---

## Task 1 — task121: Add `inputs.required` manifest field

**Files:**
- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `tests/test_validator.py`

**Tests:** `test167`, `test168`, `test169`

### Implementation goals

- Add optional manifest field `inputs.required` as boolean.
- Default behavior remains required input when the field is absent.
- Validation must reject non-boolean values with clear errors.

### AC coverage targets

- AC7 via `test167`, `test168`
- AC2 default-required behavior path via `test169`

---

## Task 2 — task122: Update run CLI parsing for no-input and pass-through

**Files:**
- `src/kinnoo/cli.py`
- `tests/test_cli.py`

**Tests:** `test170`, `test171`, `test172`

### Implementation goals

- Allow optional positional input for run command while preserving legacy syntax.
- Capture pass-through args after `--` and forward to run command layer.
- Keep existing usage/error behavior stable for legacy invocations.

### AC coverage targets

- AC1 via `test170`
- AC4 via `test171`
- AC3 via `test172`

### Design constraints

- Prefer standard argparse remainder behavior for args after `--`.
- Do not change existing flags semantics (`--preflight`, `--no-guard`).

---

## Task 3 — task123: Implement runtime flexible input flow + guard integration

**Files:**
- `src/kinnoo/run_command.py`
- `src/kinnoo/input_guard.py`
- `tests/test_input_guard_integration.py`
- `tests/test_cli.py`

**Tests:** `test173`, `test174`, `test175`, `test176`

### Implementation goals

- In no-input mode, run without positional input only when `inputs.required: false`.
- In pass-through mode, forward args after `--` to subprocess argv in order.
- Use guard aggregation for pass-through arguments through `check_inputs()`.
- Ensure `--no-guard` bypasses checks in all modes.

### AC coverage targets

- AC5 via `test173`
- AC6 via `test174`
- AC2 explicit required=true rejection via `test175`
- AC1 + AC4 coexistence path via `test176`

### Design constraints

- Preserve legacy single-input subprocess behavior unchanged.
- Keep non-interactive guard safety behavior consistent with feature18.

---

## Task 4 — task124: Regression verification gate

**Files:**
- `tests/test_cli.py`
- `tests/test_install.py`
- `tests/test_regression_v1.py`

**Test:** `test177`

### Implementation goals

- Verify feature20 did not regress V2 run/install behavior.
- Add explicit regression assertion for backward compatibility contract.

### AC coverage targets

- AC8 via `test177`

---

## Full AC-to-Test Mapping (Feature20)

- AC1: `test170`, `test176`
- AC2: `test169`, `test175`
- AC3: `test172`
- AC4: `test171`, `test176`
- AC5: `test173`
- AC6: `test174`
- AC7: `test167`, `test168`
- AC8: `test177`

---

## Regression Test Requirements (Must Run)

Run these after implementation before marking tasks `needs-review`:

1. `python3 scripts/validate_project_manifests.py`
2. `python3 -m pytest tests/test_validator.py -k "inputs_required"`
3. `python3 -m pytest tests/test_cli.py -k "run"`
4. `python3 -m pytest tests/test_input_guard_integration.py`
5. `python3 -m pytest tests/test_install.py tests/test_regression_v1.py`
6. `python3 -m pytest` (full suite)

---

## Risks and Pitfalls

- Argparse regressions can silently break legacy `kinnoo run <dir> "input"` behavior.
- Pass-through guard evaluation must avoid changing feature18 warning semantics.
- Default behavior for manifests without `inputs.required` must remain input-required to avoid unexpected behavior changes.
- Ensure no secrets/unsafe values are logged when guard warnings include pass-through parameters.

---

## Status Update Guidance for SWE Agent

- Set `task121`..`task124` to `in-progress` when work begins.
- Set each to `needs-review` only after tests pass and evidence is captured.
- Do not move feature status to `completed`; TechLead review + approval gate handles final completion.

---

## TechLead Review (Pre-merge) — 2026-03-15

### Review Scope

- Verified task definitions and statuses for `task121`..`task124`.
- Audited feature acceptance criteria coverage using `test167`..`test177` and implemented test code.
- Reviewed implementation in runtime/parser/schema paths for feature20 behavior and regressions.

### Evidence Run

- `python3 scripts/validate_project_manifests.py` -> pass
- `python3 -m pytest tests/test_validator.py -k "inputs_required"` -> 2 passed
- `python3 -m pytest tests/test_cli.py -k "feature20 or run_without_input or pass_through"` -> 5 passed
- `python3 -m pytest tests/test_input_guard_integration.py -k "pass_through or no_guard"` -> 3 passed
- `python3 -m pytest tests/test_regression_v1.py -k "feature20_does_not_regress_v2_behavior"` -> 1 passed

### Findings (ordered by severity)

1. **High: behavior conflict with feature contract for `inputs.required: true`**
   - Current logic in `run_command.py` only rejects missing positional input when both input and pass-through args are absent.
   - This allows `kinnoo run <dir> -- -e text` to proceed even when `inputs.required` is true.
   - Feature20 contract states only agents with `inputs.required: false` may omit positional input.
   - Impact: agents marked input-required can be run without positional input by using pass-through mode.
   - Recommendation: enforce positional input requirement whenever `inputs.required` is true, regardless of pass-through args. Add a dedicated regression test for required=true + pass-through without positional input.

2. **Medium: feature manifest linkage/state is stale**
   - `FEATURES.txt` still shows feature20 `tasks: []` and `status: not-started`.
   - `TASKS.txt` shows `task121`..`task124` at `needs-review`.
   - Impact: project-tracking inconsistency before merge gate.
   - Recommendation: update feature20 task list and status to match current task progression before merge into phase3 main.

3. **Low: run usage/help text no longer reflects supported modes**
   - CLI usage error still prints `Usage: kinnoo run <agent-dir> '<input>'` as the only form.
   - Feature20 now supports no-input and pass-through modes.
   - Impact: user-facing guidance is incomplete and can cause confusion.
   - Recommendation: expand usage/help examples to include:
     - `kinnoo run <agent-dir>` (when `inputs.required: false`)
     - `kinnoo run <agent-dir> -- <args...>`

### AC Coverage Audit

- AC1: covered (`test170`, `test176`)
- AC2: covered for plain no-input (`test169`, `test175`), but **missing required=true + pass-through/no positional input case**
- AC3: covered (`test172`)
- AC4: covered (`test171`, `test176`)
- AC5: covered (`test173`)
- AC6: covered (`test174`; existing single-input no-guard integration also present)
- AC7: covered (`test167`, `test168`)
- AC8: covered (`test177`)

### Recommended Follow-up Before Merge

1. Patch runtime required-input gate to align with feature contract for required=true manifests.
2. Add one explicit test case for required=true + pass-through without positional input -> must fail.
3. Update feature20 entry in `FEATURES.txt` (tasks list + status progression).
4. Update run usage/help text to represent all supported invocation modes.

### Merge Recommendation

- **Status: changes requested before merge**
- Rationale: core implementation is close and tests are largely solid, but the required-input bypass in pass-through mode is a contract-level mismatch that should be fixed before integrating into `phase3/main`.

---

## Tech Lead Feature 20 Review 2

### Review Context

- Scope for this follow-up review: validate task125 fixes for prior outcomes 1 and 3 only.
- Outcome 2 (feature/task manifest linkage and status consistency) was updated separately and is treated as resolved per maintainer update.

### Outcome 1 Check (required input cannot be bypassed with pass-through)

- Code check: `run_command.py` now enforces required input with `if input_arg is None and inputs_required:` before execution.
- Test evidence:
   - `tests/test_cli.py::test_run_required_input_cannot_be_bypassed_by_pass_through` -> pass
   - `tests/test_cli.py::test_run_without_input_rejected_when_required` -> pass
   - `tests/test_cli.py::test_run_pass_through_args_forwarded_verbatim` -> pass (confirms valid pass-through path still works)
- Assessment: outcome 1 is resolved and behavior matches feature20 contract.

### Outcome 3 Check (run usage/help text includes new modes)

- Code check: CLI now defines `RUN_USAGE_TEXT` including legacy, no-input, and pass-through invocation patterns.
- Test evidence:
   - `tests/test_cli.py::test_run_usage_includes_feature20_modes` -> pass
- Assessment: outcome 3 is resolved and user guidance now reflects supported feature20 runtime modes.

### Targeted Verification Commands Executed

1. `python3 -m pytest tests/test_cli.py -k "cannot_be_bypassed or usage_includes_feature20_modes"` -> 2 passed
2. `python3 -m pytest tests/test_cli.py -k "run_without_input_rejected_when_required or run_pass_through_args_forwarded_verbatim"` -> 2 passed

### Final Decision

- **Approval: approved to merge to phase3/main**
- Rationale: task125 closes both remaining technical issues from the first Tech Lead review (outcomes 1 and 3), and targeted verification confirms expected behavior.
