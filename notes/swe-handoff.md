## SWE Handoff - Feature25 Service Health Checks (Runtime Preflight)

### Context
- Feature: feature25 "Service Health Checks - Runtime Preflight"
- Goal: execute manifest-declared service health checks during `kinnoo run` and integrate results into `--preflight` output.
- Scope: runtime health-check execution and run/preflight behavior only. Service declaration schema is already delivered in feature24.

### Tasks To Implement (Ordered)
1. `task150` - health-check module and checker primitives (HTTP/TCP/process)
2. `task151` - integrate service checks into run + preflight output
3. `task152` - interactive vs non-interactive failure policy
4. `task153` - AC coverage + no-services regression gate

### Dependency Chain
- `task150` -> `task151` -> `task152` -> `task153`

### Design Constraints
- Reuse feature24 service declarations; do not redesign schema in feature25.
- Keep dependency footprint minimal: use stdlib (`urllib.request`, `socket`, subprocess/pgrep).
- Timeouts must be configurable while preserving defaults:
	- HTTP: 5s default
	- TCP: 3s default
- Failed check output must include service name, service type, and actionable guidance.
- `--preflight` must report service checks without executing the agent entrypoint.
- Preserve backward compatibility: manifests without `services` must behave exactly as before.

### Files Expected To Change
- `src/kinnoo/health_check.py` (new)
- `src/kinnoo/run_command.py`
- `src/kinnoo/cli.py`
- `tests/test_health_check.py` (new)
- `tests/test_run_preflight.py`
- `tests/test_cli.py`
- `tests/test_regression_v1.py`

### AC-to-Test Mapping
- AC1 -> `test231`
- AC2 -> `test228`
- AC3 -> `test229`
- AC4 -> `test230`
- AC5 -> `test233`, `test234`
- AC6 -> `test232`
- AC7 -> `test235`
- AC8 -> `test234`

### Suggested Implementation Notes
- Introduce a small checker interface in `health_check.py` returning a normalized result object.
- Keep service-check result rendering deterministic to make tests stable.
- For process checks, prefer `pgrep -f <name>` behavior compatible with current test environment.
- Interactive behavior should be explicit and testable:
	- Warning prompt: `Service <name> is not healthy. Proceed anyway? [y/N]`
	- `y` proceeds, default/non-yes aborts.
- Non-interactive mode should fail-fast on first unhealthy service to avoid ambiguous runtime state.

### Validation Commands (SWE)
- `python3 src/validate_project_manifests.py`
- `python3 -m pytest tests/test_health_check.py -k feature25`
- `python3 -m pytest tests/test_run_preflight.py -k feature25`
- `python3 -m pytest tests/test_cli.py -k feature25`
- `python3 -m pytest tests/test_regression_v1.py -k feature25`
- `python3 -m pytest` (final regression gate)

### Done Criteria
- All feature25 ACs covered by automated tests (`test228`-`test235`).
- Preflight output includes service health checks and still skips entrypoint execution.
- Interactive/non-interactive behavior matches AC policy exactly.
- No regressions for no-services agents.
