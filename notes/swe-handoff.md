# SWE Agent Handoff — Feature 22: Asset Bundling

**Date:** 2026-03-15
**From:** TechLead Agent
**Feature:** feature22 — Asset Bundling
**Branch:** Create `phase3/feature22/main` from `phase3/main`; use task branches (`phase3/feature22/task135`, etc.)
**Status:** `not-started` -> set to `in-progress` when implementation starts

## Overview

Implement manifest-driven asset bundling with an `assets` object in `kinnoo.yaml`:

- `assets.paths` for file/directory declarations
- `assets.bundle` opt-out switch (default `true`)
- `assets.max_bundle_size_mb` threshold override (default `100`)

Feature22 adds pack/install/inspect behavior for assets plus warning-only heuristic credential scanning over asset files.

Primary risks:

- regression in pack/install behavior for agents without assets
- path traversal vulnerabilities in recursive path handling
- scanning logic that is either too noisy or accidentally blocking

## Task Execution Order

`task135 -> task136 -> task137 -> task138 -> task139 -> task140`

Order rationale:

- define schema first
- wire pack behavior second
- then install/inspect visibility
- then thresholds and scanning
- finish with docs/regression gate

## Task 1 — task135: Manifest assets schema and validation

**Files:**

- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `tests/test_validator.py`

**Tests:** `test202`, `test203`

### Implementation goals

- Add optional `assets` object validation.
- Enforce:
	- `assets.paths` as `list[str]`
	- `assets.bundle` as `bool` (default `true`)
	- `assets.max_bundle_size_mb` as number (default `100`)
- Keep manifests without assets fully backward compatible.

### AC coverage targets

- AC1 via `test202`, `test203`

## Task 2 — task136: Pack asset inclusion and path safety

**Files:**

- `src/kinnoo/pack_command.py`
- `tests/test_pack.py`

**Tests:** `test204`, `test205`, `test206`, `test207`

### Implementation goals

- Include declared assets recursively in archive when enabled.
- Implement `assets.bundle: false` opt-out message and behavior.
- Reject traversal/escape paths.
- Warn for missing declared asset paths per feature contract.

### AC coverage targets

- AC2 via `test204`
- AC3 via `test205`
- AC4 via `test206`
- AC5 via `test207`

## Task 3 — task137: Install extraction and inspect visibility

**Files:**

- `src/kinnoo/install_command.py`
- `src/kinnoo/inspect_command.py`
- `tests/test_cli_install_extract.py`
- `tests/test_cli_inspect.py`

**Tests:** `test208`, `test210`

### Implementation goals

- Ensure installed agent retains bundled asset paths exactly.
- Display declared asset paths and sizes in inspect output for dir/archive.

### AC coverage targets

- AC6 via `test208`
- AC8 via `test210`

## Task 4 — task138: Asset size threshold behavior

**Files:**

- `src/kinnoo/pack_command.py`
- `tests/test_pack.py`

**Test:** `test209`

### Implementation goals

- Use `assets.max_bundle_size_mb` when present.
- Keep 100 MB default warning threshold.

### AC coverage targets

- AC7 via `test209`

## Task 5 — task139: Warning-only credential sweep for assets

**Files:**

- `src/kinnoo/code_sweep.py`
- `src/kinnoo/pack_command.py`
- `tests/test_pack.py`

**Tests:** `test212`, `test213`

### Implementation goals

- Add filename-based secret checks on assets.
- Add regex-based text checks for size-limited UTF-8 assets.
- Skip binary files in text regex scan path.
- Keep findings warning-only with explicit heuristic disclaimer.

### AC coverage targets

- AC10 via `test212`
- AC11 via `test213`
- AC12 via `test213`

## Task 6 — task140: Docs and regression gate

**Files:**

- `README.md`
- `docs/manifest-schema-reference.md`
- `tests/test_regression_v1.py`

**Test:** `test211`

### Implementation goals

- Ensure docs explain what can be included and how folder-based inclusion works.
- Confirm no-assets flows are unchanged from pre-feature22 behavior.

### AC coverage targets

- AC9 via `test211`

## Full AC-to-Test Mapping (Feature22)

- AC1: `test202`, `test203`
- AC2: `test204`
- AC3: `test205`
- AC4: `test206`
- AC5: `test207`
- AC6: `test208`
- AC7: `test209`
- AC8: `test210`
- AC9: `test211`
- AC10: `test212`
- AC11: `test213`
- AC12: `test213`

## Regression and Validation Requirements (Must Run)

1. `python3 src/validate_project_manifests.py`
2. `python3 -m pytest tests/test_validator.py -k "feature22 or assets"`
3. `python3 -m pytest tests/test_pack.py -k "feature22 or assets"`
4. `python3 -m pytest tests/test_cli_install_extract.py -k "feature22 or assets"`
5. `python3 -m pytest tests/test_cli_inspect.py -k "feature22 or assets"`
6. `python3 -m pytest tests/test_regression_v1.py -k "feature22 or assets"`

## Status Update Guidance for SWE Agent

- Set `task135`..`task140` to `in-progress` when implementation begins.
- Move each task to `needs-review` only after linked tests pass with evidence.
- Do not set feature status to `completed`; completion is TechLead review + approval gate.
