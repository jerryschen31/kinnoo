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

1. `python3 src/validate_project_manifests.py`
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
