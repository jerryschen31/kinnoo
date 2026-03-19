# Task192 - feature34 OpenClaw template README setup guidance

## Summary
- Added an OpenClaw-specific scaffold README template in [src/kinnoo/templates.py](src/kinnoo/templates.py):
  - `OPENCLAW_README_TEMPLATE` includes:
    - Node prerequisite guidance (`Node.js 20+`),
    - dependency installation path (`npm install`),
    - required env var names (`OPENCLAW_API_KEY`, `KINNOO_TEST_SAFE_MODE`),
    - run commands for both `kinnoo run` and direct `node index.mjs`,
    - daemon stop command.
- Updated OpenClaw scaffold generation in [src/kinnoo/init_command.py](src/kinnoo/init_command.py):
  - OpenClaw branch now writes `README.md` from `OPENCLAW_README_TEMPLATE` so generated setup guidance is framework-specific.
- Added task-linked test290 in [tests/test_init.py](tests/test_init.py):
  - `test_feature34_openclaw_readme_setup_guidance`,
  - verifies generated OpenClaw README contains required Node setup, install path, env vars, and run instructions.
- Updated [TASKS.txt](TASKS.txt):
  - `task192` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_init.py::test_feature34_openclaw_readme_setup_guidance` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Framework-specific onboarding docs belong in framework-specific templates; this keeps generated projects actionable and avoids generic README drift.
- Good setup docs include three operator-critical elements: runtime prerequisite, dependency installation path, and required environment variable names.
- For scaffold docs tests, assert concrete command strings (not just broad keywords) so operator workflows remain stable across refactors.
