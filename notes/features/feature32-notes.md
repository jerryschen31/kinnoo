## SWE Handoff

### Scope
Implement feature32 from [FEATURES.txt](FEATURES.txt) using tasks task178-task183 from [TASKS.txt](TASKS.txt). This is the daemon lifecycle/control-plane layer for Phase 4 and must preserve existing one-shot and mcp-server behavior.

### Feature Intent
Add generic daemon runtime support with operator lifecycle controls (`run` start semantics, `stop`, `attach`, `logs`) and supervisor/health diagnostics for Python and Node.js agents.

### Task Breakdown (Execution Order)
1. task178: Schema + validator support for `runtime.type: daemon`.
2. task179: Daemon start path in `kinnoo run` + persisted PID/state metadata.
3. task180: `kinnoo stop <agent>` graceful shutdown + deterministic fallback behavior.
4. task181: `kinnoo attach <agent>` interactive attach controls for supported daemon sessions.
5. task182: `kinnoo logs <agent>` tail/follow command with source/timestamp context.
6. task183: Supervisor/health integration and regression gate for daemon lifecycle states.

### AC Coverage Map
- AC1 -> task178 -> test276
- AC2 -> task179 -> test277
- AC3 -> task180 -> test278
- AC4 -> task181 -> test279
- AC5 -> task182 -> test280
- AC6 -> task183 -> test281

### Key Implementation Constraints
- This feature is daemon lifecycle support, not full OpenClaw gateway orchestration.
- Reuse existing [src/kinnoo/supervisor.py](src/kinnoo/supervisor.py) and [src/kinnoo/health_check.py](src/kinnoo/health_check.py) architecture where possible.
- Preserve backward compatibility for existing runtime modes (`one-shot`, `mcp-server`) and existing CLI flows.
- Keep operator diagnostics deterministic and actionable; never leak secret values.
- Daemon state file layout and log metadata format should be stable and testable.

### JS/TS Test Guidance
- No feature32 behavior requires mandatory JavaScript-native test execution at this stage; pytest integration tests can validate daemon lifecycle contracts for both Python and Node.js fixtures.
- If a JS-native control-surface behavior becomes unavoidable during implementation, use Vitest and record automation_path as a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/schema.py
- src/kinnoo/validator.py
- src/kinnoo/cli.py
- src/kinnoo/run_command.py
- src/kinnoo/supervisor.py
- src/kinnoo/health_check.py
- tests/test_validator.py
- tests/test_cli.py
- tests/test_run_preflight.py
- tests/test_regression_v1.py

### Verification Gate
- Run targeted tests for test276-test281.
- Run daemon-focused regression slices for python + node compatibility paths.
- Run full regression before handoff completion:
  - python3 -m pytest
- Validate manifests after task/test updates:
  - python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task178-task183 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
