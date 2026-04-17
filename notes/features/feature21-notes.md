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

1. `python3 scripts/validate_project_manifests.py`
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

---

## Human and TechLead Review 1 - additional tasks

### Review context and decisions

During review after `task126`-`task129`, two gaps were identified:

1. Dependency policy quality gap:
	 A generic pre-1.0 constraint style (for example broad `<1.0` patterns) was considered too weak for stability.
2. Template realism gap:
	 New framework templates needed to be framework-native runnable implementations, not placeholder hello-world shells.

A second review pass then added a third requirement:

3. Manifest metadata gap:
	 `kinnoo.yaml` should support an optional `model` field when the underlying default model is known.

In the same pass, run-path UX was reviewed and confirmed:

4. Pass-through args:
	 `kinnoo run <agent-dir> -- <args...>` behavior already worked and had coverage, but `run --help` needed clearer pass-through discoverability text.

### Additional tasks added

- `task130` — Feature21 dependency compatibility pinning update
	- Why: move from placeholder version policy to tested compatibility ranges.
	- Scope: update template dependency constraints and add policy-alignment checks.
	- Linked tests: `test192`, `test193`.

- `task131` — Feature21 implement real PydanticAI runnable template
	- Why: ensure generated `pydantic-ai` scaffold is framework-native and runnable in test-safe mode.
	- Linked tests: `test194`, `test195`.

- `task132` — Feature21 implement real LangGraph runnable template
	- Why: ensure generated `langgraph` scaffold uses graph/state constructs and runs in test-safe mode.
	- Linked tests: `test196`, `test197`.

- `task133` — Feature21 implement real OpenAI Agents runnable template
	- Why: ensure generated `openai-agents` scaffold uses native agent workflow constructs and runs in test-safe mode.
	- Linked tests: `test198`, `test199`.

- `task134` — Feature21 optional `kinnoo.yaml` model metadata field
	- Why: support optional `model` metadata when known without breaking existing manifests.
	- Scope: schema + validator + template emission logic.
	- Linked tests: `test200`, `test201`.

### Additional tests added in manifests

- `test192`: requirements use tested compatibility ranges (AC4 policy enforcement)
- `test193`: dependency policy text/implementation alignment
- `test194`: PydanticAI template contains framework-native constructs
- `test195`: PydanticAI basic run succeeds in test-safe mode
- `test196`: LangGraph template contains framework-native constructs
- `test197`: LangGraph basic run succeeds in test-safe mode
- `test198`: OpenAI Agents template contains framework-native constructs
- `test199`: OpenAI Agents basic run succeeds in test-safe mode
- `test200`: validator behavior for optional manifest `model` metadata
- `test201`: template generation emits `model` metadata when known

### Additional AC updates captured

- AC4 updated to tested compatibility range policy.
- AC13/AC14/AC15 added for framework-native implementation requirements.
- AC16 added for optional manifest `model` metadata behavior.

### Pass-through argument review outcome

- Behavioral status: pass-through argument forwarding was already implemented and covered by existing tests.
- UX/documentation status: `kinnoo run` help text was updated to include explicit separator example:
	- `kinnoo run <agent-dir> -- -e <some-string> -p <some-file-path> -u <some-url>`
- Code-level verification: targeted CLI tests were run for pass-through forwarding and usage/help text.

### Validation evidence for this review batch

- `python3 scripts/validate_project_manifests.py` -> passed after adding `task130`-`task134` and `test192`-`test201`.
- Focused CLI verification:
	- `python3 -m pytest tests/test_cli.py -k "run_pass_through_args_forwarded_verbatim or run_help_includes_pass_through_separator_usage or run_usage_includes_feature20_modes"`
	- Result: selected tests passed.

### Notes for next implementation cycle

- Implement `task130` before `task131`-`task133` so dependency-policy assertions match template output.
- Implement `task134` with backward compatibility as a hard requirement (`model` optional, non-breaking).
- Keep feature/task status flow unchanged: SWE moves tasks to `needs-review`; TechLead/human review gates completion.

---

## Tech Lead Agent - Review 2

### Scope reviewed

- Tasks: `task126` through `task134`
- Feature contract: `feature21` AC1-AC16
- Evidence sources: manifest link validation, test automation path verification, and focused pytest runs

### Findings (ordered by severity)

1. Medium — feature status is stale relative to implementation progress
	 - Observation: `feature21` remains `status: not-started` while all linked tasks `task126`-`task134` are `needs-review`.
	 - Risk: workflow/board state is misleading before merge and can confuse reviewers.
	 - Recommendation: move `feature21` to `needs-review` now (or `in-progress` if your process requires an intermediate step before review complete).

2. Low — stale wording in task127 no longer fully matches AC4 policy
	 - Observation: `task127` step text still references major-version-range pinning, while AC4 now allows tested bounded ranges or exact tested pins for pre-1.0 frameworks.
	 - Risk: subtle mismatch between task intent and accepted policy could cause future drift in follow-up work.
	 - Recommendation: refresh task127 wording to align with the current AC4 language.

3. Low — feature notes still include an older pinning hint
	 - Observation: feature21 notes include "Pin major versions..." wording that predates the tested-compatibility policy update.
	 - Risk: future contributors may follow outdated guidance.
	 - Recommendation: update note wording to reference tested compatibility ranges (stable major-bounded, pre-1.0 tested bounded or exact tested pins).

### Coverage audit results

- Task/test linkage check:
	- `task126`-`task134` each have linked tests.
	- `test180`-`test201` automation paths resolve to existing files and functions.
- AC coverage check:
	- AC1-AC16 all have at least one mapped test in `TESTS.txt`.
	- No uncovered feature21 ACs detected.

### Execution evidence (this review)

- Manifest consistency:
	- `python3 scripts/validate_project_manifests.py` -> pass
- Feature21 focused suites:
	- `python3 -m pytest tests/test_init.py tests/test_cli.py -k feature21` -> 21 passed
	- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> 1 passed

### Merge recommendation

- Readiness: functionally ready for merge review based on current evidence.
- Before merge to `phase3/main`, apply the low-cost housekeeping updates above (status + wording alignment) to keep manifests and guidance consistent with implemented behavior.
