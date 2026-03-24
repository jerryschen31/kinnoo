# Task216 - feature39 sandbox execution mode and enforcement backend

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py):
	- added `--sandbox` flag for `kinnoo run` to enable permission policy enforcement.
- Added [src/kinnoo/sandbox.py](src/kinnoo/sandbox.py):
	- introduced baseline sandbox policy backend with deterministic decision model,
	- added capability inference for network/shell/filesystem write actions from pass-through args,
	- added explicit failure classification and remediation payloads.
- Updated [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
	- added `sandbox` execution mode parameter to `run_agent`,
	- routed sandbox checks through the new backend before entrypoint launch,
	- implemented deterministic failure diagnostics for unsupported runtime mode and policy violations,
	- preserved backward compatibility when `--sandbox` is not used.
- Updated [tests/test_cli.py](tests/test_cli.py):
	- added mapped test314 `test_feature39_run_sandbox_permission_enforcement`,
	- validates allowed sandboxed run path,
	- validates denied policy violation path with deterministic classification/remediation diagnostics,
	- validates denied run does not execute entrypoint.
- Updated [TASKS.txt](TASKS.txt):
	- `task216` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature39_run_sandbox_permission_enforcement` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered after integration.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Deterministic policy enforcement benefits from a structured decision object (`allowed`, `classification`, `remediation`) so CLI diagnostics remain stable and testable.
- For cross-platform sandbox baselines, capability-intent mediation is a practical first step before deeper OS-level syscall enforcement.
- Keep enforcement before process launch; this avoids side effects and makes denied paths provably non-executing.
