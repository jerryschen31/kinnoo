# task457 Notes

## Summary
- Added `--minimal` support to `kinnoo init` CLI and propagated it into scaffold generation.
- Implemented complete-vs-minimal scaffold behavior:
  - Complete (default): adds `tools/`, `prompts/`, `evals/`, `tests/`, `data/`, and `.gitignore`.
  - Minimal: emits only core files for selected language/framework.
- Reworked OpenClaw scaffold for feature115 matrix:
  - OpenClaw minimal emits: `kinnoo.yaml`, `AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `USER.md`, `README.md`.
  - OpenClaw complete adds: `.gitignore`, `BOOTSTRAP.md`, `HEARTBEAT.md`, `MEMORY.md`, `skills/`, `memory/`.
- Added task tests:
  - `tests/test_init.py::test_init_complete_template_folders`
  - `tests/test_init.py::test_init_minimal_template`
  - `tests/test_init.py::test_init_openclaw_complete_template`

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Test run
- Command:
  - `python3 -m pytest tests/test_init.py --testmon -k "test_init_complete_template_folders or test_init_minimal_template or test_init_openclaw_complete_template"`
- Result:
  - `3 passed, 55 deselected`

## Teaching notes
- When a CLI has minimal/complete modes, define the file matrix explicitly and test both positive and negative expectations (files that must exist and files that must not exist).
- OpenClaw-specific scaffolds benefit from dedicated tests that assert absence of Python artifacts, preventing accidental cross-template leakage.
