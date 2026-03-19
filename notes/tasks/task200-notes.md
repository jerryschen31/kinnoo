# Task200 - feature36 manifest inference for runtime package manager skills and state dirs

## Summary
- Added OpenClaw inference helpers in [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py):
  - `infer_openclaw_project_hints(...)` returns deterministic hints for runtime and project structure,
  - infers runtime as Node daemon for OpenClaw onboarding (`language: nodejs`, `type: daemon`, `version: >=20.0.0`),
  - infers package manager from lockfile conventions (`pnpm-lock.yaml` -> `pnpm`, otherwise `npm`),
  - infers `skills` from `skills/**/SKILL.md`,
  - infers candidate `state_dirs` from mutable roots (currently `memory`, optional `state`).
- Wired OpenClaw hints into manifest generation in [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
  - when framework resolves to `openclaw`, import manifest generation applies OpenClaw runtime/package manager hints,
  - appends inferred `skills` and `state_dirs` in schema-compatible list shape.
- Added task-linked integration test298 in [tests/test_cli_import.py](tests/test_cli_import.py):
  - `test_feature36_infers_runtime_skills_state_dirs` validates generated manifest includes inferred runtime/package manager/skills/state_dirs from OpenClaw fixture structure.
- Added analyzer-facing coverage in [tests/test_analyzer.py](tests/test_analyzer.py):
  - `test_feature36_openclaw_hint_inference_runtime_package_manager_skills_state_dirs` validates helper output shape and values.
- Updated [TASKS.txt](TASKS.txt):
  - `task200` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature36_infers_runtime_skills_state_dirs tests/test_analyzer.py::test_feature36_openclaw_hint_inference_runtime_package_manager_skills_state_dirs` -> `2 passed`

## Bug/error notes
- No implementation bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Inference pipelines are easier to evolve when you keep the core report contract stable and add task-specific helper APIs for richer downstream manifest shaping.
- Structure-derived hints (lockfiles, skill markdown paths, memory roots) are deterministic and testable, which is preferable to opaque heuristics for packaging/runtime decisions.
- Separating detection (what framework it is) from inference (how to map into manifest fields) keeps the flow modular and reduces accidental regressions in existing analyzer consumers.
