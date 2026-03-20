# Task217 - feature39 cross-runtime permission enforcement for Python and Node

## Summary
- Updated [src/kinnoo/sandbox.py](src/kinnoo/sandbox.py):
	- made sandbox evaluation runtime-aware by adding `runtime_language` to policy evaluation,
	- added deterministic fallback classification for unsupported runtime languages,
	- retained shared permission model for parity across Python and Node runtime paths.
- Updated [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
	- passed runtime language into sandbox evaluation adapter,
	- preserved deterministic diagnostics (`classification`, message, remediation) for denied paths.
- Updated [tests/test_regression_v1.py](tests/test_regression_v1.py):
	- added mapped test315 `test_feature39_python_node_permission_parity`,
	- validates both Python and Node deny shell actions with identical policy-violation classification,
	- validates both Python and Node allow network actions under the same policy,
	- validates denied paths do not launch entrypoint processes while allowed paths do.
- Updated [TASKS.txt](TASKS.txt):
	- `task217` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature39_python_node_permission_parity` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered after integration.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Cross-runtime parity is easier to verify when both runtimes are routed through one shared policy evaluator and only runtime adapters vary.
- Deterministic fallback classifications (for unsupported runtime modes/languages) are essential for predictable automation and reliable operator guidance.
- A good parity regression asserts both behavior symmetry (allow/deny outcomes) and side-effect symmetry (denied paths never launch execution).
