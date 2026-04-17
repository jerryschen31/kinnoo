# Task280 Notes - OpenClaw-like Analyzer Detection Without Root package.json

Date: 2026-03-23
Status: needs-review

## Summary
Implemented a focused analyzer fix to improve import-time metadata inference for OpenClaw-like JS/TS projects that do not have a root-level package.json.

This addresses real-world layouts similar to:
- selfclaw-style nested server projects
- nanobot-style bridge/src projects
- build-your-own tutorial step layouts
- openclaw-core style src entrypoint layouts

## Implementation details

### 1) Node/TS source discovery fallback
Updated analyzer to scan JS/TS source files (with depth limits and ignored directories) even when root package.json is missing.

Files:
- src/kinnoo/analyzer.py

Key behavior:
- Added `_iter_node_files_with_depth(...)` to detect JS/TS files in nested layouts.

### 2) Node entrypoint fallback heuristics
Extended `_detect_node_entrypoint(...)` so inference no longer depends solely on package.json.

Key behavior:
- Keeps package.json `main`/`scripts.start` detection when available.
- Adds root and nested filename priority heuristics for common entrypoint names (boot/entry/server/index/main/cli).
- Prefers conventional directories (`src`, `server`, `bridge`, `daemon`, etc.) and deterministic path ordering.

### 3) Node runtime fallback inference
Extended `_detect_runtime(...)` so Node runtime can be inferred from source layout without package.json.

Key behavior:
- If JS/TS files exist, infer:
  - `runtime.language: nodejs`
  - `runtime.version: >=20.0.0` default (or from package metadata when present)
  - `runtime.package_manager` from lockfile heuristics
  - `runtime.type: one-shot` when entrypoint is inferred
  - `runtime.typescript: true` when TS files are present

### 4) Expanded OpenClaw weighted signals
Extended OpenClaw detection to better classify real OpenClaw-like projects with lightweight markers.

Key behavior:
- `_openclaw_dependency_marker_count(...)` now scans nested package.json files (depth-limited), not only root.
- Adds markers from package `name` containing openclaw and `openclaw` config block presence.
- Added `_openclaw_readme_signal(...)` for README/README.source OpenClaw mentions.
- Added `_openclaw_node_layout_signal(...)` for Node-first project layout hints.

## Tests added
Added four unit tests in tests/test_analyzer.py using minimal barebones fixtures (not dependent on example-scratch agents):

- `test_feature47_openclaw_like_selfclaw_layout_inference` (test410)
- `test_feature47_openclaw_like_nanobot_layout_inference` (test411)
- `test_feature47_openclaw_like_build_your_own_layout_inference` (test412)
- `test_feature47_openclaw_like_core_layout_inference` (test413)

These fixtures intentionally mimic structural patterns only (README markers + nested Node entrypoints) and can survive corpus folder churn.

## Regression command and result
Command:
```bash
python3 -m pytest tests --testmon -k "feature47_openclaw_like or feature36_openclaw_weighted_detection_scores or feature36_openclaw_hint_inference_runtime_package_manager_skills_state_dirs or feature36_identity_signal_detection"
```

Result:
- First run: 1 failure in entrypoint priority expectation (core layout)
- Fix applied: prioritize `src/entry.*` before `src/index.*`
- Final run: `7 passed, 391 deselected`

## Manifest validation
Command:
```bash
python3 scripts/validate_project_manifests.py
```

Result:
- `Validation passed: manifests are consistent`

## Files changed
- src/kinnoo/analyzer.py
- tests/test_analyzer.py
- FEATURES.txt
- TASKS.txt
- TESTS.txt
- notes/tasks/task280-notes.md
