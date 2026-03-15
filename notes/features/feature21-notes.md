# Feature 21 Notes

## SWE Handoff

# SWE Agent Handoff — Feature 21: Framework Template Expansion

**Date:** 2026-03-15
**From:** TechLead Agent
**Feature:** feature21 — Framework & Template Expansion (PydanticAI, LangGraph, OpenAI Agents)
**Branch:** Create `phase3/feature21/main` from `phase3/main`; use task branches (`phase3/feature21/task126`, etc.)
**Status:** `not-started` -> set to `in-progress` when implementation starts

---

## Overview

Implement `kinnoo init --framework` support for three new frameworks:

1. `pydantic-ai`
2. `langgraph`
3. `openai-agents`

Each template must generate framework-specific `run.py`, `requirements.txt`, `kinnoo.yaml`, and `README.md` while preserving the existing kinnoo runtime contract and backward compatibility for current frameworks (`gemini`, `chatgpt`, `claude-chat`).

Primary risks:

- parser/choices regressions in init command
- template quality drift that breaks run-path contract
- hidden regressions in existing frameworks

---

## Task Execution Order

`task126 -> task127 -> task128 -> task129`

Tasks are ordered from parser acceptance -> template generation -> runnable smoke validation -> regression gate.

---

## Task 1 — task126: Extend init framework parsing

**Files:**

- `src/kinnoo/cli.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`

**Tests:** `test180`, `test181`

### Implementation goals

- Add `pydantic-ai`, `langgraph`, `openai-agents` as accepted framework values.
- Keep invalid-framework messaging explicit and complete.
- Preserve existing framework values and behavior.

### AC coverage targets

- AC1/AC2/AC3 entry path via `test181`
- AC9 via `test180`

---

## Task 2 — task127: Generate templates and metadata artifacts

**Files:**

- `src/kinnoo/templates.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`

**Tests:** `test182`, `test183`, `test184`, `test185`, `test186`, `test187`

### Implementation goals

- Add framework-specific template strings for all four generated artifacts.
- Pin framework dependencies to major-version ranges in requirements files.
- Ensure generated manifests validate and set framework field correctly.
- Ensure generated READMEs contain framework-specific setup guidance.

### AC coverage targets

- AC1 via `test182`
- AC2 via `test183`
- AC3 via `test184`
- AC4 via `test185`
- AC5 via `test186`
- AC6 via `test187`

### Design constraints

- Keep templates minimal and deterministic for testing.
- Do not introduce plaintext secret values in templates or logs.

---

## Task 3 — task128: Runnable smoke tests for new frameworks

**Files:**

- `tests/test_init.py`
- `tests/test_cli.py`

**Tests:** `test188`, `test189`, `test190`

### Implementation goals

- Verify each new template is runnable with a basic input (`"hello"`) through `kinnoo run`.
- Use test-safe configuration paths to avoid live external API dependencies.
- Assert non-empty stdout and absence of template-level errors.

### AC coverage targets

- AC7 via `test188`, `test189`, `test190`
- AC10 via `test188`
- AC11 via `test189`
- AC12 via `test190`

### Design constraints

- Smoke tests should be stable in CI without network credentials.
- Keep runtime assertions focused on contract, not model output quality.

---

## Task 4 — task129: Regression gate for existing frameworks

**Files:**

- `tests/test_init.py`
- `tests/test_cli.py`
- `tests/test_regression_v1.py`

**Test:** `test191`

### Implementation goals

- Prove existing framework behavior (`gemini`, `chatgpt`, `claude-chat`) is unchanged.
- Capture explicit regression evidence before handing off for review.

### AC coverage targets

- AC8 via `test191`

---

## Full AC-to-Test Mapping (Feature21)

- AC1: `test181`, `test182`
- AC2: `test181`, `test183`
- AC3: `test181`, `test184`
- AC4: `test185`
- AC5: `test186`
- AC6: `test187`
- AC7: `test188`, `test189`, `test190`
- AC8: `test191`
- AC9: `test180`
- AC10: `test188`
- AC11: `test189`
- AC12: `test190`

---

## Regression and Validation Requirements (Must Run)

Run these before marking tasks `needs-review`:

1. `python3 src/validate_project_manifests.py`
2. `python3 -m pytest tests/test_init.py -k "framework or feature21"`
3. `python3 -m pytest tests/test_cli.py -k "feature21"`
4. `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"`
5. `python3 -m pytest`

---

## Risks and Pitfalls

- New framework parser choices can accidentally drop existing valid choices.
- Template boilerplate can become non-runnable if runtime contract is violated.
- External SDK assumptions can destabilize tests unless smoke tests are fully test-safe.
- README/setup instructions can drift from actual template behavior.

---

## Status Update Guidance for SWE Agent

- Set `task126`..`task129` to `in-progress` when implementation begins.
- Move each task to `needs-review` only after linked tests pass with evidence.
- Do not set feature status to `completed`; completion is TechLead review + approval gate.
