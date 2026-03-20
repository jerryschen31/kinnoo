## SWE Handoff: feature31 - Node.js Runtime Support (Foundation)

### Scope
Implement feature31 from [FEATURES.txt](FEATURES.txt) using tasks task168-task173 from [TASKS.txt](TASKS.txt). This is the Phase 4 foundation for JS/TS runtime support and must preserve Python runtime behavior.

### Feature Intent
Add first-class Node.js runtime support across validation, run, install, and pack flows while preserving backward compatibility for Python agents.

### Task Breakdown (Execution Order)
1. task168: Schema + validator runtime.language support (`nodejs`).
2. task169: Node.js run execution path (`node <entrypoint> <input>`), stream output, preserve exit code contract.
3. task170: Node.js dependency install using package manager selection (`npm` default, `pnpm` optional).
4. task171: Pack/install archive behavior for Node.js (`node_modules` excluded, `package.json`/lockfiles preserved).
5. task172: Node preflight checks (node presence, version >=22, package manager availability).
6. task173: Python regression gate and parity validation.

### AC Coverage Map
- AC1 -> task168 -> test263, test264
- AC2 -> task169 -> test265
- AC3 -> task170 -> test266
- AC4 -> task171 -> test267
- AC5 -> task172 -> test268
- AC6 -> task173 -> test269

### Key Implementation Constraints
- Preserve existing Python run/install/pack behavior and outputs unless explicitly required.
- Node runtime entrypoint support is `.js/.mjs` first; TS transpilation is out of scope for feature31.
- Do not archive `node_modules`; rely on package metadata and lockfiles for reproducible restore.
- Keep error messages actionable and aligned with current kinnoo CLI style.
- Preflight failures must fail fast with clear remediation guidance.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/run_command.py
- src/kinnoo/install_command.py
- src/kinnoo/pack_command.py
- src/kinnoo/health_check.py
- tests/test_validator.py
- tests/test_cli.py
- tests/test_install.py
- tests/test_pack.py
- tests/test_run_preflight.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test263-test269.
- Run regression slices for existing Python runtime behavior.
- Run manifest validator:
  - python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task168-task173 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review + approval path is done.
